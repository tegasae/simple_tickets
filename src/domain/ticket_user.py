from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from src.domain.exceptions import (
    DomainOperationError,
    ItemValidationError,
)
from src.domain.statuses.ticket_user_status import TicketUserStatus
from src.domain.statuses.ticket_user_status_record import (
    TicketUserStatusRecord,
)
from src.domain.statuses.ticket_user_status_transitions import (
    FIRST_TICKET_USER_STATUSES,
    TERMINAL_TICKET_USER_STATUSES,
    TICKET_USER_TRANSITIONS,
)
from src.domain.ticket_components import Comment
from src.domain.value_objects import (
    CommonComment,
    Description,
    Empty,
)


@dataclass(kw_only=True)
class TicketUser:
    """
    Aggregate пользовательской заявки.

    TicketUser представляет внешний, пользовательский workflow заявки.

    TicketUser и внутренняя Ticket являются независимыми aggregates.

    Связь между ними устанавливается через:

        Ticket.user_ticket_id == TicketUser.ticket_id

    Cross-aggregate invariants и синхронизация Ticket/TicketUser не являются
    ответственностью этого aggregate.


    Public construction API
    =======================

    Новая TicketUser создаётся через:

        TicketUser.create(...)

    Persisted TicketUser восстанавливается через:

        TicketUser.rehydrate(...)

    Прямой вызов TicketUser(...) технически возможен, поскольку aggregate
    реализован как dataclass, но не является публичным способом создания
    объекта.

    __post_init__ всё равно проверяет основные aggregate invariants.


    Workflow
    ========

    TicketUser хранит полную историю пользовательского workflow:

        statuses: list[TicketUserStatusRecord]

    Текущий workflow state определяется последней status record.

    TicketUser отвечает за:

    - корректный первый status;
    - допустимость переходов;
    - хронологический порядок status records;
    - невозможность продолжения terminal workflow;
    - derived state is_closed/date_finished.

    TicketUserStatusRecord отвечает только за intrinsic payload одной
    записи status.

    В частности TicketUserStatusRecord проверяет:

    - status type;
    - actor identity;
    - обязательность comment;
    - date_created.

    Допустимые переходы определяются отдельно:

        TICKET_USER_TRANSITIONS

    Начальные состояния:

        FIRST_TICKET_USER_STATUSES

    Terminal states:

        TERMINAL_TICKET_USER_STATUSES


    Workflow API
    ============

    Основные бизнес-команды представлены явными методами:

        mark_in_work(...)
        mark_waiting_for_confirmation(...)
        confirm_by_user(...)
        confirm_by_admin(...)
        suspend(...)
        cancel_by_user(...)
        cancel_by_admin(...)

    Кроме них append_status(...) пока остаётся публичным низкоуровневым
    workflow API.

    Все workflow-методы изменяют aggregate непосредственно и возвращают
    None.

    Созданная status record после выполнения операции доступна через:

        current_status_record()

    Новые неперсистированные status records доступны через:

        new_statuses()


    Actor
    =====

    TicketUserStatusRecord.actor_employee_id всегда хранит реальный
    положительный идентификатор actor.

    Пространство идентификаторов является общим для User и Admin.

    Поэтому:

    - для действий User записывается реальный user id;
    - для действий Admin записывается реальный admin/employee id.

    Какой вид actor соответствует конкретному status, определяется
    TicketUserStatusRule.user_action.

    Сам TicketUser не проверяет существование User/Admin и не выполняет
    RBAC.


    user_id / contact_user_id
    =========================

    TicketUser всегда принадлежит конкретному User:

        user_id > 0

    Поэтому существующая TicketUser всегда должна иметь contact User:

        contact_user_id > 0

    При создании, если contact_user_id явно не задан:

        contact_user_id = user_id

    При update_details():

        contact_user_id == 0

    означает:

        contact_user_id = self.user_id

    contact_user_id может отличаться от user_id.

    При rehydrate persisted contact_user_id не нормализуется.

    Если persistence передал:

        contact_user_id <= 0

    aggregate отвергает такое состояние.


    Comments
    ========

    TicketUser содержит два вида комментариев.

    1. Ordinary comments:

        comments: list[Comment]

    2. Workflow status comments:

        TicketUserStatusRecord.comment

    Comment.employee_id использует общее пространство идентификаторов
    User/Admin и хранит реального автора.

    Все даты комментариев должны использовать UTC.


    Description
    ===========

    description представлен value object:

        Description | Empty

    Empty означает отсутствие description.


    Date/time contract
    ==================

    Все datetime внутри domain должны явно использовать UTC.

    Допускается только datetime с:

        tzinfo is UTC

    Domain отвергает:

    - naive datetime;
    - datetime в timezone, отличной от UTC.

    Domain не преобразует datetime автоматически.

    В частности UTC обязателен для:

    - TicketUser.date_created;
    - TicketUserStatusRecord.date_created;
    - Comment.date_created.

    Нормализация внешних datetime является ответственностью внешнего слоя.


    Derived state
    =============

    is_closed и date_finished полностью выводятся из workflow.

    Terminal status:

        is_closed = True
        date_finished = current status date_created

    Non-terminal status:

        is_closed = False
        date_finished = None


    TicketUser intentionally does not know
    ======================================

    Aggregate не знает:

    - RBAC;
    - permissions;
    - существование User;
    - существование Admin;
    - существование Client;
    - enabled/disabled state других aggregates;
    - внутреннюю Ticket;
    - механизм синхронизации Ticket <-> TicketUser;
    - cross-aggregate invariants.

    Эти обязанности находятся за пределами TicketUser.
    """

    ticket_user_id: int
    client_id: int
    user_id: int

    # Immutable business text of the user request.
    #
    # text_of_ticket задаётся при create()/rehydrate() и после создания
    # не изменяется.
    text_of_ticket: str

    # Editable optional description.
    description: Description | Empty = field(
        default_factory=Empty,
    )

    # Current contact User.
    #
    # Для существующей TicketUser значение всегда должно быть > 0.
    contact_user_id: int = 0

    # Complete workflow history.
    statuses: list[TicketUserStatusRecord] = field(
        default_factory=list,
    )

    # Ordinary comments.
    comments: list[Comment] = field(
        default_factory=list,
    )

    # Aggregate creation time.
    #
    # Для новой TicketUser генерируется автоматически.
    # При rehydrate восстанавливается из persistence.
    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Persistence / optimistic-locking version.
    version: int = 0

    # ------------------------------------------------------------------
    # Derived state.
    #
    # Эти значения не являются самостоятельным persisted domain state.
    # Они всегда вычисляются из workflow.
    # ------------------------------------------------------------------

    is_closed: bool = field(
        init=False,
        default=False,
    )

    date_finished: datetime | None = field(
        init=False,
        default=None,
    )

    def __post_init__(self) -> None:
        """
        Normalize immutable text and validate aggregate state.

        __post_init__ проверяет invariants, которые должны выполняться для
        любой существующей TicketUser.

        Он намеренно не исправляет persisted state.

        В частности:

        - contact_user_id не подставляется автоматически;
        - datetime не конвертируются в UTC;
        - workflow history не сортируется;
        - некорректная история не исправляется.

        Creation-specific normalization выполняется фабрикой create().
        """

        self.text_of_ticket = self.text_of_ticket.strip()

        self._validate_identity()
        self._validate_content()
        self._validate_datetimes()
        self._validate_status_history()

        self._recompute_closed_state()

    # ==================================================================
    # Factories
    # ==================================================================

    @staticmethod
    def _resolve_contact_user_id(
        *,
        user_id: int,
        contact_user_id: int,
    ) -> int:
        """
        Resolve contact User for a newly created TicketUser.

        Rules
        -----

        contact_user_id > 0:

            использовать явно переданный contact User.

        contact_user_id == 0:

            использовать user_id.

        contact_user_id < 0:

            invalid.

        Этот helper применяется только при создании новой TicketUser.

        rehydrate() намеренно его не использует.
        """

        if contact_user_id < 0:
            raise ItemValidationError(
                "Contact user id cannot be negative"
            )

        if contact_user_id > 0:
            return contact_user_id

        return user_id

    @classmethod
    def create(
        cls,
        *,
        client_id: int,
        user_id: int,
        text_of_ticket: str,
        contact_user_id: int = 0,
        description: str = "",
        comment: str = "",
    ) -> Self:
        """
        Create a new TicketUser initiated by a User.

        Identity
        --------

        Новая TicketUser всегда имеет:

            ticket_user_id == 0
            version == 0

        ticket_user_id назначается persistence layer позже.


        Workflow
        --------

        Начальный status всегда:

            CREATED

        CREATED является User action.

        Поэтому:

            actor_employee_id == user_id


        Contact User
        ------------

        Если contact_user_id не передан или равен 0:

            contact_user_id = user_id


        Creation time
        -------------

        date_created автоматически создаётся в UTC.

        Один timestamp используется для:

        - TicketUser.date_created;
        - начального CREATED status;
        - optional initial ordinary comment.


        Initial comment
        ---------------

        Если comment передан, он создаётся как ordinary Comment.

        Его автор:

            Comment.employee_id == user_id
        """

        if user_id <= 0:
            raise ItemValidationError(
                "User id must be positive"
            )

        now = datetime.now(UTC)

        resolved_contact_user_id = cls._resolve_contact_user_id(
            user_id=user_id,
            contact_user_id=contact_user_id,
        )

        ticket_user = cls(
            ticket_user_id=0,
            client_id=client_id,
            user_id=user_id,
            text_of_ticket=text_of_ticket,
            contact_user_id=resolved_contact_user_id,
            description=(
                Description(description)
                if description
                else Empty()
            ),
            date_created=now,
            version=0,
            statuses=[
                TicketUserStatusRecord(
                    status=TicketUserStatus.CREATED,
                    actor_employee_id=user_id,
                    date_created=now,
                ),
            ],
        )

        if comment.strip():
            ticket_user.add_comment(
                Comment(
                    employee_id=user_id,
                    comment=CommonComment(comment),
                    date_created=now,
                )
            )

        return ticket_user

    @classmethod
    def rehydrate(
        cls,
        *,
        ticket_user_id: int,
        client_id: int,
        user_id: int,
        text_of_ticket: str,
        statuses: list[TicketUserStatusRecord],
        date_created: datetime,
        contact_user_id: int,
        description: str = "",
        comments: list[Comment] | None = None,
        version: int = 0,
    ) -> Self:
        """
        Rehydrate a persisted TicketUser.

        Persistence contract
        --------------------

        Repository должен передать:

        - ticket_user_id > 0;
        - полную workflow history;
        - history в persisted порядке;
        - datetime уже в UTC;
        - persisted contact_user_id без нормализации.


        Workflow reconstruction
        -----------------------

        В constructor передаётся только первый persisted status:

            statuses[0]

        Остальные status records последовательно проигрываются через:

            append_status(...)

        Таким образом persisted history проходит те же проверки переходов
        и хронологии, что и runtime workflow.


        Contact User
        ------------

        contact_user_id восстанавливается точно таким, каким его вернул
        persistence layer.

        В отличие от create(), rehydrate() не заменяет:

            contact_user_id == 0

        на:

            user_id

        Некорректное persisted состояние отвергается aggregate.


        Derived state
        -------------

        is_closed и date_finished не загружаются как самостоятельные
        authoritative значения.

        Они вычисляются из workflow history.
        """

        if ticket_user_id <= 0:
            raise DomainOperationError(
                "Cannot rehydrate TicketUser with "
                "non-positive ticket_user_id"
            )

        if not statuses:
            raise DomainOperationError(
                "Cannot rehydrate TicketUser without status history"
            )

        ticket_user = cls(
            ticket_user_id=ticket_user_id,
            client_id=client_id,
            user_id=user_id,
            text_of_ticket=text_of_ticket,
            contact_user_id=contact_user_id,
            description=(
                Description(description)
                if description
                else Empty()
            ),
            statuses=statuses[:1],
            comments=(
                comments
                if comments is not None
                else []
            ),
            date_created=date_created,
            version=version,
        )

        for status in statuses[1:]:
            ticket_user.append_status(status)

        return ticket_user

    # ==================================================================
    # Current state / queries
    # ==================================================================

    def is_new(self) -> bool:
        """
        Return True if TicketUser has not been persisted yet.

        New aggregate uses:

            ticket_user_id == 0
        """

        return self.ticket_user_id == 0

    def current_status_record(self) -> TicketUserStatusRecord:
        """
        Return current workflow record.

        Текущее состояние TicketUser всегда определяется последней записью
        полной workflow history.
        """

        if not self.statuses:
            raise DomainOperationError(
                "TicketUser has no status history"
            )

        return self.statuses[-1]

    def current_status(self) -> TicketUserStatus:
        """
        Return current TicketUser workflow status.
        """

        return self.current_status_record().status

    def is_terminal(self) -> bool:
        """
        Return True if TicketUser is in a terminal workflow state.
        """

        return (
            self.current_status()
            in TERMINAL_TICKET_USER_STATUSES
        )

    # ==================================================================
    # Persistence helpers
    # ==================================================================

    def new_statuses(self) -> list[TicketUserStatusRecord]:
        """
        Return workflow records not yet persisted.
        """

        return [
            record
            for record in self.statuses
            if record.is_new()
        ]

    def new_comments(self) -> list[Comment]:
        """
        Return ordinary comments not yet persisted.
        """

        return [
            comment
            for comment in self.comments
            if comment.is_new()
        ]

    # ==================================================================
    # Editable TicketUser data
    # ==================================================================

    def update_details(
        self,
        *,
        actor_employee_id: int,
        description: str = "",
        contact_user_id: int = 0,
    ) -> None:
        """
        Update editable TicketUser details.

        actor_employee_id
        -----------------

        Команда требует идентификатор employee, выполняющего изменение.

        Значение должно быть положительным.

        TicketUser не выполняет RBAC и не проверяет существование actor.


        Terminal state
        --------------

        После достижения terminal status данные изменять нельзя.


        Description
        -----------

        Пустая строка очищает description и сохраняется как Empty.


        Contact User
        ------------

        contact_user_id > 0:

            установить указанного contact User.

        contact_user_id == 0:

            вернуть contact User к TicketUser.user_id.

        contact_user_id < 0:

            invalid.

        TicketUser всегда должна иметь положительный contact_user_id.
        """

        if actor_employee_id <= 0:
            raise DomainOperationError(
                "actor_employee_id must be positive"
            )

        self._ensure_not_terminal()

        if contact_user_id < 0:
            raise DomainOperationError(
                "contact_user_id cannot be negative"
            )

        self.description = (
            Description(description)
            if description
            else Empty()
        )

        self.contact_user_id = (
            contact_user_id
            if contact_user_id > 0
            else self.user_id
        )

    def change_contact_user(
            self,
            *,
            actor_employee_id: int,
            contact_user_id: int,
    ) -> None:
        """
        Change contact User.

        actor_employee_id must be positive.

        contact_user_id > 0:
            set the specified contact User.

        contact_user_id == 0:
            reset contact User to TicketUser.user_id.

        contact_user_id < 0:
            invalid.

        Contact User cannot be changed after TicketUser reaches a terminal
        workflow state.
        """

        if actor_employee_id <= 0:
            raise DomainOperationError(
                "actor_employee_id must be positive"
            )

        self._ensure_not_terminal()

        if contact_user_id < 0:
            raise DomainOperationError(
                "contact_user_id cannot be negative"
            )

        self.contact_user_id = (
            contact_user_id
            if contact_user_id > 0
            else self.user_id
        )

    # ==================================================================
    # Workflow commands
    # ==================================================================

    def mark_in_work(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """
        Move TicketUser to IN_WORK.

        IN_WORK is an Admin action.

        В зависимости от текущего workflow state это может означать:

            CREATED -> IN_WORK

                Заявка принята в работу.

            WAITING_FOR_CONFIRMATION -> IN_WORK

                Заявка возвращена в работу.

            SUSPENDED -> IN_WORK

                Работа возобновлена после suspension.

        Конкретная допустимость перехода проверяется append_status().
        """

        record = TicketUserStatusRecord(
            status=TicketUserStatus.IN_WORK,
            actor_employee_id=actor_employee_id,
            comment=self._make_status_comment(comment),
        )

        self.append_status(record)

    def mark_waiting_for_confirmation(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """
        Move TicketUser to WAITING_FOR_CONFIRMATION.

        WAITING_FOR_CONFIRMATION is an Admin action.

        Status означает, что работа со стороны исполнителей закончена и
        результат ожидает подтверждения.

        Допустимые source states определяются TICKET_USER_TRANSITIONS.
        """

        record = TicketUserStatusRecord(
            status=TicketUserStatus.WAITING_FOR_CONFIRMATION,
            actor_employee_id=actor_employee_id,
            comment=self._make_status_comment(comment),
        )

        self.append_status(record)

    def confirm_by_user(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """
        Confirm completion by User.

        Resulting status:

            CONFIRMED_BY_USER

        CONFIRMED_BY_USER является terminal status.

        TicketUserStatusRecord хранит реальный положительный идентификатор
        User actor.

        Проверка того, какой именно User имеет право подтвердить заявку,
        не выполняется этим методом.
        """

        record = TicketUserStatusRecord(
            status=TicketUserStatus.CONFIRMED_BY_USER,
            actor_employee_id=actor_employee_id,
            comment=self._make_status_comment(comment),
        )

        self.append_status(record)

    def confirm_by_admin(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """
        Confirm completion by Admin.

        Resulting status:

            CONFIRMED_BY_ADMIN

        CONFIRMED_BY_ADMIN является terminal status.
        """

        record = TicketUserStatusRecord(
            status=TicketUserStatus.CONFIRMED_BY_ADMIN,
            actor_employee_id=actor_employee_id,
            comment=self._make_status_comment(comment),
        )

        self.append_status(record)

    def suspend(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """
        Suspend TicketUser processing.

        Resulting status:

            SUSPENDED

        SUSPENDED не является terminal status.

        Status представляет временную приостановку пользовательской заявки,
        например из-за отключённого Client/User.

        Допустимые source states определяются TICKET_USER_TRANSITIONS.
        """

        record = TicketUserStatusRecord(
            status=TicketUserStatus.SUSPENDED,
            actor_employee_id=actor_employee_id,
            comment=self._make_status_comment(comment),
        )

        self.append_status(record)

    def cancel_by_user(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """
        Cancel TicketUser by User.

        Resulting status:

            CANCELLED_BY_USER

        CANCELLED_BY_USER является terminal status.

        TicketUserStatusRecord хранит реальный положительный идентификатор
        User actor.

        Допустимость перехода определяется TICKET_USER_TRANSITIONS.
        """

        record = TicketUserStatusRecord(
            status=TicketUserStatus.CANCELLED_BY_USER,
            actor_employee_id=actor_employee_id,
            comment=self._make_status_comment(comment),
        )

        self.append_status(record)

    def cancel_by_admin(
        self,
        *,
        actor_employee_id: int,
        comment: str,
    ) -> None:
        """
        Cancel TicketUser by Admin.

        Resulting status:

            CANCELLED_BY_ADMIN

        CANCELLED_BY_ADMIN является terminal status.

        Непустой comment обязателен.

        Требование comment определяется TicketUserStatusRule и проверяется
        TicketUserStatusRecord.

        Поэтому этот метод не дублирует проверку comment.
        """

        record = TicketUserStatusRecord(
            status=TicketUserStatus.CANCELLED_BY_ADMIN,
            actor_employee_id=actor_employee_id,
            comment=self._make_status_comment(comment),
        )

        self.append_status(record)

    # ==================================================================
    # Workflow
    # ==================================================================

    def append_status(
        self,
        record: TicketUserStatusRecord,
    ) -> None:
        """
        Append one workflow status record.

        TicketUserStatusRecord уже проверил собственный intrinsic payload:

        - status type;
        - actor identity;
        - required comment;
        - date_created.

        TicketUser проверяет aggregate-level workflow rules:

        - текущий status не terminal;
        - transition разрешён;
        - status history остаётся хронологической;
        - record.date_created использует UTC.

        Chronology
        ----------

        Новый record должен удовлетворять:

            record.date_created >= current_record.date_created

        Равные timestamps разрешены.

        Этот метод пока остаётся public API.

        Он также используется rehydrate(), поэтому persisted workflow
        history проходит те же transition checks, что и runtime workflow.
        """

        self._ensure_not_terminal()

        self._require_utc_datetime(
            record.date_created,
            field_name="status.date_created",
        )

        current_record = self.current_status_record()

        if (
            record.status
            not in TICKET_USER_TRANSITIONS[current_record.status]
        ):
            raise DomainOperationError(
                "TicketUser status transition is not allowed: "
                f"{current_record.status.value} -> "
                f"{record.status.value}"
            )

        if record.date_created < current_record.date_created:
            raise DomainOperationError(
                "TicketUser status history must be chronological"
            )

        self.statuses.append(record)

        self._recompute_closed_state()

    # ==================================================================
    # Ordinary comments
    # ==================================================================

    def add_comment(
        self,
        comment: Comment,
    ) -> None:
        """
        Add an ordinary comment.

        Ordinary comments нельзя добавлять после достижения terminal status.

        Comment.employee_id использует общее пространство идентификаторов
        User/Admin.

        comment.date_created должен явно использовать UTC.
        """

        self._ensure_not_terminal()

        if not comment.comment:
            raise DomainOperationError(
                "Comment cannot be empty"
            )

        self._require_utc_datetime(
            comment.date_created,
            field_name="comment.date_created",
        )

        self.comments.append(comment)

    # ==================================================================
    # Workflow validation
    # ==================================================================

    def _validate_status_history(self) -> None:
        """
        Validate complete TicketUser workflow history.

        Validation checks:

        - history is not empty;
        - first status belongs to FIRST_TICKET_USER_STATUSES;
        - every transition is allowed;
        - timestamps are chronological.

        Equal consecutive timestamps are allowed.

        Intrinsic payload каждой status record проверяется самим
        TicketUserStatusRecord.
        """

        if not self.statuses:
            raise DomainOperationError(
                "TicketUser must have status history"
            )

        first_record = self.statuses[0]

        if first_record.status not in FIRST_TICKET_USER_STATUSES:
            raise DomainOperationError(
                "TicketUser cannot start with status "
                f"{first_record.status.value}"
            )

        for index in range(1, len(self.statuses)):
            previous_record = self.statuses[index - 1]
            current_record = self.statuses[index]

            if (
                current_record.status
                not in TICKET_USER_TRANSITIONS[
                    previous_record.status
                ]
            ):
                raise DomainOperationError(
                    "Invalid TicketUser status history: "
                    f"{previous_record.status.value} -> "
                    f"{current_record.status.value}"
                )

            if current_record.date_created < previous_record.date_created:
                raise DomainOperationError(
                    "TicketUser status history must be chronological"
                )

    def _ensure_not_terminal(self) -> None:
        """
        Reject operation when TicketUser is already terminal.
        """

        if self.is_terminal():
            raise DomainOperationError(
                f"TicketUser {self.ticket_user_id} is in terminal "
                f"status {self.current_status().value}"
            )

    # ==================================================================
    # Aggregate validation
    # ==================================================================

    def _validate_identity(self) -> None:
        """
        Validate identifiers and persistence version.

        Метод проверяет только aggregate invariants.

        Он не проверяет существование:

        - Client;
        - User;
        - contact User;
        - actor.
        """

        if self.ticket_user_id < 0:
            raise DomainOperationError(
                "TicketUser ticket_user_id cannot be negative"
            )

        if self.client_id <= 0:
            raise DomainOperationError(
                "TicketUser client_id must be positive"
            )

        if self.user_id <= 0:
            raise DomainOperationError(
                "TicketUser user_id must be positive"
            )

        if self.contact_user_id <= 0:
            raise DomainOperationError(
                "TicketUser contact_user_id must be positive"
            )

        if self.version < 0:
            raise DomainOperationError(
                "TicketUser version cannot be negative"
            )

    def _validate_content(self) -> None:
        """
        Validate immutable TicketUser content.
        """

        if not self.text_of_ticket:
            raise DomainOperationError(
                "TicketUser text_of_ticket cannot be empty"
            )

    def _validate_datetimes(self) -> None:
        """
        Validate complete TicketUser datetime contract.

        Все datetime, уже находящиеся внутри aggregate, должны явно
        использовать UTC.

        Никакой normalization здесь не выполняется.
        """

        self._require_utc_datetime(
            self.date_created,
            field_name="date_created",
        )

        for record in self.statuses:
            self._require_utc_datetime(
                record.date_created,
                field_name="status.date_created",
            )

        for comment in self.comments:
            self._require_utc_datetime(
                comment.date_created,
                field_name="comment.date_created",
            )

    # ==================================================================
    # Derived state
    # ==================================================================

    def _recompute_closed_state(self) -> None:
        """
        Recompute closing state from current workflow status.

        Terminal state:

            is_closed = True
            date_finished = current status date_created

        Non-terminal state:

            is_closed = False
            date_finished = None
        """

        self.is_closed = self.is_terminal()

        if self.is_closed:
            self.date_finished = (
                self.current_status_record().date_created
            )
        else:
            self.date_finished = None

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _make_status_comment(
        comment: str,
    ) -> CommonComment | Empty:
        """
        Convert workflow comment text to status-record representation.

        Empty или whitespace-only string означает отсутствие status comment.

        Обязательность comment для конкретного status определяется
        TicketUserStatusRule и проверяется TicketUserStatusRecord.
        """

        if not comment.strip():
            return Empty()

        return CommonComment(comment)

    @staticmethod
    def _require_utc_datetime(
        value: datetime,
        *,
        field_name: str,
    ) -> None:
        """
        Validate the domain datetime contract.

        Value must:

        - be a datetime instance;
        - explicitly use datetime.UTC.

        Domain rejects:

        - naive datetime;
        - timezone-aware datetime с timezone, отличной от UTC.

        Domain не выполняет автоматическое timezone conversion.
        """

        if not isinstance(value, datetime):
            raise ItemValidationError(
                f"{field_name} must be datetime"
            )

        if value.tzinfo is not UTC:
            raise ItemValidationError(
                f"{field_name} must use UTC timezone"
            )