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
from src.domain.statuses.ticket_user_status_transistions import TERMINAL_TICKET_USER_STATUSES, TICKET_USER_TRANSITIONS, \
    FIRST_TICKET_USER_STATUSES
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

    Эта связь координируется application layer и не поддерживается
    самим TicketUser.


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

    - корректность первого status;
    - допустимость переходов;
    - хронологический порядок status records;
    - terminal state;
    - derived state is_closed/date_finished.

    TicketUserStatusRecord отвечает только за собственный payload.

    Допустимые переходы определяются отдельно:

        TICKET_USER_TRANSITIONS

    Начальные состояния определяются:

        FIRST_TICKET_USER_STATUSES

    Terminal states определяются:

        TERMINAL_TICKET_USER_STATUSES


    Actor
    =====

    TicketUserStatusRecord.actor_employee_id всегда хранит реальный
    положительный идентификатор actor.

    Пространство идентификаторов является общим для User и Admin.

    Поэтому:

    - для действий User записывается реальный user_id;
    - для действий Admin записывается реальный admin/employee id.

    Какой тип actor ожидается для конкретного status, определяется
    TicketUserStatusRule.user_action.

    TicketUser самостоятельно не проверяет существование соответствующего
    User/Admin. Это ответственность application layer.


    user_id / contact_user_id
    =========================

    TicketUser всегда принадлежит конкретному User:

        user_id > 0

    Поэтому TicketUser всегда должна иметь contact User:

        contact_user_id > 0

    При создании, если contact_user_id явно не задан:

        contact_user_id = user_id

    При update_details():

        contact_user_id == 0

    означает возврат contact User к:

        self.user_id

    contact_user_id может отличаться от user_id.

    При rehydrate persisted contact_user_id не нормализуется.
    Если persistence передал 0 или отрицательное значение, aggregate
    отвергает такое состояние.


    Comments
    ========

    TicketUser содержит два разных вида комментариев.

    1. Ordinary comments:

        comments: list[Comment]

    2. Status-specific comments:

        TicketUserStatusRecord.comment

    Comment.employee_id использует общее пространство идентификаторов
    User/Admin и всегда хранит реального автора.

    Все даты комментариев должны использовать UTC.


    Description
    ===========

    description представлен value object:

        Description | Empty

    Empty означает отсутствие description.


    Date/time contract
    ==================

    Все datetime внутри domain должны явно использовать UTC.

    Domain отвергает:

    - naive datetime;
    - datetime с timezone, отличной от UTC.

    Domain не преобразует datetime автоматически.

    В частности, внутри TicketUser должны быть UTC:

    - TicketUser.date_created;
    - TicketUserStatusRecord.date_created;
    - Comment.date_created.

    Преобразование внешних datetime в UTC является ответственностью
    внешнего слоя до передачи значения в domain.


    Derived state
    =============

    is_closed и date_finished полностью выводятся из текущего workflow.

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
    - механизм синхронизации Ticket <-> TicketUser.

    Эти проверки и координация выполняются на других уровнях.
    """

    ticket_id: int
    client_id: int
    user_id: int

    # Immutable business text of the request.
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

    # Complete TicketUser workflow history.
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
    # Эти значения не загружаются как самостоятельное domain state.
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

        __post_init__ intentionally does not repair persisted data.

        In particular:

        - contact_user_id is not substituted here;
        - datetime values are not converted to UTC;
        - workflow history is not reordered.

        Creation-specific normalization belongs to create().
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

        Explicit positive contact_user_id:

            use contact_user_id

        contact_user_id == 0:

            use user_id

        Negative contact_user_id:

            invalid

        This helper is used only while creating a new aggregate.

        rehydrate() intentionally does not use it.
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

        A newly created aggregate always has:

            ticket_id == 0
            version == 0

        ticket_id is assigned by persistence later.


        Workflow
        --------

        Initial status is always:

            TicketUserStatus.CREATED

        CREATED is a User action.

        Therefore:

            actor_employee_id == user_id


        Contact User
        ------------

        If contact_user_id is omitted or equals 0:

            contact_user_id = user_id


        Creation time
        -------------

        date_created is generated automatically in UTC.

        The same timestamp is used for:

        - TicketUser.date_created;
        - initial CREATED status;
        - optional initial ordinary comment.


        Initial comment
        ---------------

        If comment is supplied, it is stored as an ordinary Comment.

        Its author is the creating User:

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
            ticket_id=0,
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

        if comment:
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
        ticket_id: int,
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

        Repository must provide:

        - persisted ticket_id > 0;
        - complete status history;
        - status history in persistence order;
        - persisted contact_user_id;
        - datetime values already using UTC.

        Domain does not repair persistence data.


        Workflow reconstruction
        -----------------------

        Only the first persisted status is initially passed to TicketUser.

        Remaining records are replayed through _append_status():

            statuses[0]
                -> constructor / __post_init__

            statuses[1:]
                -> _append_status(...)

        Therefore persisted history is checked by the same transition and
        chronology rules used for runtime workflow changes.


        Contact User
        ------------

        contact_user_id is restored exactly as persisted.

        Unlike create(), rehydrate() does not replace zero with user_id.

        Invalid persisted contact state is rejected by the aggregate.


        Derived state
        -------------

        is_closed and date_finished are recomputed from workflow history.
        They are not restored as independent authoritative values.
        """

        if ticket_id <= 0:
            raise DomainOperationError(
                "Cannot rehydrate TicketUser with "
                "non-positive ticket_id"
            )

        if not statuses:
            raise DomainOperationError(
                "Cannot rehydrate TicketUser without status history"
            )

        ticket_user = cls(
            ticket_id=ticket_id,
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
            ticket_user._append_status(status)

        return ticket_user

    # ==================================================================
    # Current state / queries
    # ==================================================================

    def is_new(self) -> bool:
        """
        Return True if TicketUser has not been persisted yet.

        New aggregate uses:

            ticket_id == 0
        """

        return self.ticket_id == 0

    def current_status_record(self) -> TicketUserStatusRecord:
        """
        Return the current TicketUser status record.

        Current state is always defined by the last record in complete
        workflow history.
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

    def new_statuses(self) -> list[TicketUserStatusRecord]:
        """
        Return status records not yet persisted.
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

        The command requires the identity of the employee performing
        the operation.

        The identifier must be positive.

        This method does not itself perform RBAC or check whether the actor
        is User or Admin.


        Terminal state
        --------------

        Details cannot be changed after TicketUser reaches a terminal
        workflow state.


        Description
        -----------

        Empty string clears description and stores Empty.


        Contact User
        ------------

        contact_user_id > 0:

            set that User as contact.

        contact_user_id == 0:

            reset contact User to TicketUser.user_id.

        contact_user_id < 0:

            invalid.

        Because TicketUser always belongs to a User, it can never exist
        without a positive contact_user_id.
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

    # ==================================================================
    # Workflow commands
    # ==================================================================

    def mark_in_work(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketUserStatusRecord:
        """
        Move TicketUser to IN_WORK.

        IN_WORK is an Admin action according to TicketUserStatusRule.

        Concrete actor authorization is handled outside the aggregate.
        """

        return self._append_status(
            TicketUserStatusRecord(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.IN_WORK,
                comment=self._make_status_comment(comment),
            )
        )

    def mark_waiting_for_confirmation(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketUserStatusRecord:
        """
        Move TicketUser to WAITING_FOR_CONFIRMATION.

        This state means that service-side work is finished and the result
        is waiting for confirmation.
        """

        return self._append_status(
            TicketUserStatusRecord(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.WAITING_FOR_CONFIRMATION,
                comment=self._make_status_comment(comment),
            )
        )

    def confirm_by_user(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketUserStatusRecord:
        """
        Confirm execution by User.

        Resulting status:

            CONFIRMED_BY_USER

        This is a terminal User action.
        """

        return self._append_status(
            TicketUserStatusRecord(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.CONFIRMED_BY_USER,
                comment=self._make_status_comment(comment),
            )
        )

    def confirm_by_admin(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketUserStatusRecord:
        """
        Confirm execution by Admin.

        Resulting status:

            CONFIRMED_BY_ADMIN

        This is a terminal Admin action.
        """

        return self._append_status(
            TicketUserStatusRecord(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.CONFIRMED_BY_ADMIN,
                comment=self._make_status_comment(comment),
            )
        )

    def suspend(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketUserStatusRecord:
        """
        Move TicketUser to SUSPENDED.

        SUSPENDED represents temporary suspension of the user-facing
        request, for example when the related Client/User is disabled.

        SUSPENDED is not terminal.
        """

        return self._append_status(
            TicketUserStatusRecord(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.SUSPENDED,
                comment=self._make_status_comment(comment),
            )
        )

    def cancel_by_user(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketUserStatusRecord:
        """
        Cancel TicketUser by User.

        Resulting status:

            CANCELLED_BY_USER

        This is a terminal User action.
        """

        return self._append_status(
            TicketUserStatusRecord(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.CANCELLED_BY_USER,
                comment=self._make_status_comment(comment),
            )
        )

    def cancel_by_admin(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketUserStatusRecord:
        """
        Cancel TicketUser by Admin.

        Resulting status:

            CANCELLED_BY_ADMIN

        This status requires a comment according to
        TicketUserStatusRule.

        TicketUserStatusRecord performs that payload validation.
        """

        return self._append_status(
            TicketUserStatusRecord(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.CANCELLED_BY_ADMIN,
                comment=self._make_status_comment(comment),
            )
        )

    # ==================================================================
    # Ordinary comments
    # ==================================================================

    def add_comment(
        self,
        comment: Comment,
    ) -> None:
        """
        Add an ordinary comment.

        Comments cannot be added to a terminal TicketUser.

        Comment date_created must explicitly use UTC.
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
    # Workflow internals
    # ==================================================================

    def _append_status(
        self,
        record: TicketUserStatusRecord,
    ) -> TicketUserStatusRecord:
        """
        Append one workflow status record.

        Responsibilities
        ----------------

        TicketUser validates:

        - TicketUser is not already terminal;
        - status transition is allowed;
        - status history remains chronological;
        - record timestamp uses UTC.

        TicketUserStatusRecord is responsible for validating its own
        payload, including:

        - actor;
        - required comment;
        - status type.


        Chronology
        ----------

        New record must satisfy:

            record.date_created >= current_record.date_created

        Equal timestamps are allowed.
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

        return record

    def _validate_status_history(self) -> None:
        """
        Validate complete TicketUser workflow history.

        Validation checks:

        - history is not empty;
        - first status is allowed as an initial status;
        - all transitions are allowed;
        - timestamps are chronological.

        Equal consecutive timestamps are allowed.

        Individual status payload is validated by TicketUserStatusRecord.
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
        Reject a command when TicketUser is already terminal.
        """

        if self.is_terminal():
            raise DomainOperationError(
                f"TicketUser {self.ticket_id} is in terminal "
                f"status {self.current_status().value}"
            )

    # ==================================================================
    # Validation
    # ==================================================================

    def _validate_identity(self) -> None:
        """
        Validate aggregate identifiers and persistence version.

        This method checks only identifier invariants.

        It does not check whether referenced entities actually exist.
        """

        if self.ticket_id < 0:
            raise DomainOperationError(
                "TicketUser ticket_id cannot be negative"
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
        Validate aggregate datetime contract.

        All datetime values currently stored inside TicketUser must
        explicitly use UTC.

        No normalization or conversion is performed.
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
        Convert command comment text to status-record representation.

        Empty string means that the status has no comment.

        Whether a comment is mandatory for a concrete status is validated
        by TicketUserStatusRecord through TicketUserStatusRule.
        """

        if not comment:
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
        - datetime in any timezone other than UTC.

        Domain never converts timezone automatically.
        """

        if not isinstance(value, datetime):
            raise ItemValidationError(
                f"{field_name} must be datetime"
            )

        if value.tzinfo is not UTC:
            raise ItemValidationError(
                f"{field_name} must use UTC timezone"
            )