from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Self

from src.domain.exceptions import (
    DomainOperationError,
    ItemValidationError,
)
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.statuses.ticket_status_transitions import (
    FIRST_TICKET_STATUSES,
    TERMINAL_TICKET_STATUSES,
    TICKET_TRANSITIONS,
)
from src.domain.ticket_components import Comment
from src.domain.value_objects import CommonComment


class TicketUrgency(StrEnum):
    """
    Urgency of an internal Ticket.

    NORMAL:
        Normal request.

    URGENT:
        Request requiring increased priority.

    MAINTENANCE:
        Maintenance-related request.
    """

    NORMAL = "normal"
    URGENT = "urgent"
    MAINTENANCE = "maintenance"


@dataclass(kw_only=True)
class Ticket:
    """
    Aggregate внутренней заявки.

    Public construction API
    =======================

    Новая Ticket должна создаваться через одну из фабрик:

        Ticket.create(...)
        Ticket.create_from_ticket_user(...)

    Persisted Ticket восстанавливается только через:

        Ticket.rehydrate(...)

    Технически Python позволяет вызвать Ticket(...) напрямую, поскольку
    aggregate реализован как dataclass. Однако прямой constructor не является
    публичным способом создания Ticket.

    При этом __post_init__ всё равно защищает основные aggregate invariants,
    поэтому прямым вызовом конструктора нельзя получить заведомо некорректное
    базовое состояние.


    Workflow
    ========

    Ticket хранит полную историю workflow в statuses.

    Текущий workflow state определяется исключительно последней
    TicketStatusRecord.

    Ticket проверяет aggregate-level правила workflow:

    - корректный первый status;
    - допустимость перехода между status;
    - хронологический порядок status records.

    Правила payload конкретной TicketStatusRecord находятся внутри
    TicketStatusRecord и не дублируются в Ticket.


    Ticket / TicketUser
    ===================

    Ticket и TicketUser являются независимыми aggregates.

    Связь с исходной TicketUser хранится через:

        user_ticket_id

    Ticket, созданная непосредственно Admin:

        first status == CREATED
        user_ticket_id == 0

    Ticket, созданная из TicketUser:

        first status == CREATED_FROM_TICKET_USER
        user_ticket_id > 0
        user_id > 0


    user_id / contact_user_id
    =========================

    Допустимые состояния:

        user_id == 0
        contact_user_id == 0

            Ticket не связана с User и не имеет contact User.

        user_id == 0
        contact_user_id > 0

            Ticket не имеет связанного User, но имеет contact User.

        user_id > 0
        contact_user_id > 0

            Ticket связана с User и имеет contact User.

    Если при создании:

        user_id > 0
        contact_user_id == 0

    contact_user_id автоматически становится равным user_id.

    contact_user_id не обязан совпадать с user_id.

    Если user_id > 0, удалить contact User нельзя.

    Если user_id == 0, contact_user_id может быть очищен установкой в 0.


    Actors and comments
    ===================

    TicketStatusRecord.actor_employee_id:

    - для действий Admin содержит employee id;
    - для workflow-действий User в текущей модели содержит 0.

    В частности:

        CREATED_FROM_TICKET_USER
            actor_employee_id == 0

    Comment.employee_id использует общее пространство идентификаторов
    Admin и User.

    Поэтому комментарий, созданный User, хранит настоящий user_id.


    Date/time contract
    ==================

    Все datetime внутри domain должны использовать UTC.

    Допускается только:

        datetime(..., tzinfo=UTC)

    Не допускаются:

    - naive datetime;
    - datetime с timezone, отличной от UTC.

    Domain не выполняет автоматическое преобразование timezone.
    Преобразование внешних значений в UTC должно выполняться до передачи
    значения в domain.


    planned_at
    ==========

    planned_at является текущей запланированной датой/временем выполнения
    Ticket и не является workflow status.

    При создании Ticket или вызове schedule():

    - planned_at может быть None;
    - planned_at должен быть UTC;
    - календарная UTC-дата planned_at не может быть раньше сегодняшнего дня.

    При этом время внутри сегодняшнего дня может уже пройти.

    Например, если сейчас:

        2026-09-26 17:00 UTC

    допустимо:

        2026-09-26 10:00 UTC

    но недопустимо:

        2026-09-25 23:59 UTC

    При rehydrate persisted planned_at может находиться в прошлом.
    Это является допустимым persisted state и само по себе не образует
    отдельного бизнес-состояния.


    Derived state
    =============

    is_closed и date_finished не являются самостоятельным domain state.

    Они полностью вычисляются из текущего workflow status:

        terminal status:
            is_closed = True
            date_finished = current status date_created

        non-terminal status:
            is_closed = False
            date_finished = None


    Ticket intentionally does not know
    ==================================

    Aggregate не знает:

    - RBAC;
    - permissions;
    - роли actor;
    - существование Admin;
    - существование User;
    - существование Client;
    - существование Department;
    - enabled/disabled state других aggregates;
    - cross-aggregate business rules.

    Эти проверки выполняются application/domain services соответствующего
    уровня.
    """

    ticket_id: int
    client_id: int

    # Immutable business text of the request.
    #
    # text_of_ticket задаётся при создании / rehydrate и после создания
    # не изменяется.
    text_of_ticket: str

    # User related to the Ticket.
    #
    # 0 means that there is no related User.
    user_id: int = 0

    # Current contact User.
    #
    # 0 means that no contact User is assigned.
    contact_user_id: int = 0

    # Complete workflow history.
    statuses: list[TicketStatusRecord] = field(
        default_factory=list,
    )

    # Ordinary comments attached to the Ticket.
    comments: list[Comment] = field(
        default_factory=list,
    )

    # Aggregate creation time.
    #
    # For a newly created Ticket this value is generated automatically.
    # For rehydrate it is restored from persistence.
    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Current independent planning value.
    #
    # This field is intentionally independent from workflow statuses.
    planned_at: datetime | None = None

    department_id: int = 0

    remote_work_recommended: bool = False

    # Optimistic locking / persistence version.
    version: int = 0

    urgency: TicketUrgency = TicketUrgency.NORMAL

    # Source TicketUser id.
    #
    # 0 for an ordinary internally-created Ticket.
    # > 0 for a Ticket created from TicketUser.
    user_ticket_id: int = 0

    # Editable detailed description.
    description: str = ""

    # ------------------------------------------------------------------
    # Derived state.
    #
    # These values cannot be passed to the constructor.
    # They are always reconstructed from workflow history.
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
        Normalize and validate aggregate state.

        __post_init__ validates only invariants that must always hold for
        an existing Ticket.

        Scenario-specific construction remains the responsibility of
        create(), create_from_ticket_user() and rehydrate().
        """

        self.text_of_ticket = self.text_of_ticket.strip()
        self.description = self.description.strip()

        if not self.statuses:
            raise DomainOperationError(
                "Ticket must have status history"
            )

        if self.statuses[0].status not in FIRST_TICKET_STATUSES:
            raise DomainOperationError(
                "The first Ticket status is incorrect"
            )

        self._validate_identity()
        self._validate_content()
        self._validate_datetimes()
        self._validate_creation_origin()

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
        Resolve contact_user_id for a newly created Ticket.

        Rules:

        1. Explicit contact_user_id > 0 always wins.

        2. If contact_user_id == 0 and user_id > 0,
           user_id becomes the contact User.

        3. If both values are 0, Ticket has no contact User.

        Negative contact_user_id is invalid.
        """

        if contact_user_id < 0:
            raise ItemValidationError(
                "Contact user id cannot be negative"
            )

        if contact_user_id > 0:
            return contact_user_id

        return user_id

    @classmethod
    def _create_new(
        cls,
        *,
        client_id: int,
        text_of_ticket: str,
        initial_status: TicketStatus,
        actor_employee_id: int,
        comment_employee_id: int,
        user_id: int = 0,
        contact_user_id: int = 0,
        user_ticket_id: int = 0,
        department_id: int = 0,
        description: str = "",
        remote_work_recommended: bool = False,
        urgency: TicketUrgency = TicketUrgency.NORMAL,
        planned_at: datetime | None = None,
        comment: str = "",
    ) -> Self:
        """
        Common implementation used by public creation factories.

        This method does not define a business creation scenario itself.

        The public factory supplies:

        - initial workflow status;
        - actor_employee_id of the first status;
        - author id of the optional initial comment;
        - source TicketUser information when applicable.

        actor_employee_id and comment_employee_id are intentionally
        independent values.

        For Ticket created by Admin:

            actor_employee_id == admin_id
            comment_employee_id == admin_id

        For Ticket created from TicketUser:

            actor_employee_id == 0
            comment_employee_id == user_id

        date_created is always generated automatically here.
        """

        now = datetime.now(UTC)

        if planned_at is not None:
            cls._validate_new_planned_at(
                planned_at,
                reference_time=now,
            )

        resolved_contact_user_id = cls._resolve_contact_user_id(
            user_id=user_id,
            contact_user_id=contact_user_id,
        )

        ticket = cls(
            ticket_id=0,
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=resolved_contact_user_id,
            user_ticket_id=user_ticket_id,
            department_id=department_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            date_created=now,
            version=0,
            statuses=[
                TicketStatusRecord(
                    status=initial_status,
                    actor_employee_id=actor_employee_id,
                    date_created=now,
                ),
            ],
        )

        if comment.strip():
            ticket.add_comment(
                Comment(
                    employee_id=comment_employee_id,
                    comment=CommonComment(comment),
                    date_created=now,
                )
            )

        return ticket

    @classmethod
    def create(
        cls,
        *,
        client_id: int,
        admin_id: int,
        text_of_ticket: str,
        user_id: int = 0,
        contact_user_id: int = 0,
        department_id: int = 0,
        description: str = "",
        remote_work_recommended: bool = False,
        urgency: TicketUrgency = TicketUrgency.NORMAL,
        planned_at: datetime | None = None,
        comment: str = "",
    ) -> Self:
        """
        Create a new internal Ticket directly by an Admin.

        Workflow
        --------

        First status:

            TicketStatus.CREATED

        The Admin who creates the Ticket is stored as:

            TicketStatusRecord.actor_employee_id == admin_id

        If an initial comment is provided:

            Comment.employee_id == admin_id

        TicketUser relation
        -------------------

        This factory does not create Ticket from TicketUser.

        Therefore:

            user_ticket_id == 0

        user_id may still be specified because an internally-created Ticket
        may be associated with a User.

        Contact User
        ------------

        If user_id > 0 and contact_user_id is not specified:

            contact_user_id = user_id

        text_of_ticket
        --------------

        text_of_ticket is required and immutable after Ticket creation.
        """

        if admin_id <= 0:
            raise ItemValidationError(
                "Admin id must be positive"
            )

        return cls._create_new(
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            initial_status=TicketStatus.CREATED,
            actor_employee_id=admin_id,
            comment_employee_id=admin_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            user_ticket_id=0,
            department_id=department_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            comment=comment,
        )

    @classmethod
    def create_from_ticket_user(
        cls,
        *,
        client_id: int,
        user_id: int,
        user_ticket_id: int,
        text_of_ticket: str,
        contact_user_id: int = 0,
        description: str = "",
        department_id: int = 0,
        remote_work_recommended: bool = False,
        urgency: TicketUrgency = TicketUrgency.NORMAL,
        planned_at: datetime | None = None,
        comment: str = "",
    ) -> Self:
        """
        Create an internal Ticket from an existing TicketUser.

        Ticket and TicketUser remain independent aggregates.
        Their linking is coordinated by the application layer.

        Workflow
        --------

        First status:

            TicketStatus.CREATED_FROM_TICKET_USER

        User workflow actor
        -------------------

        In the current model TicketStatusRecord.actor_employee_id represents
        an employee actor.

        A User is not stored in this field.

        Therefore for CREATED_FROM_TICKET_USER:

            actor_employee_id == 0

        The User identity is retained by Ticket.user_id.

        Initial comment
        ---------------

        Comment.employee_id uses one common identifier space for Admin
        and User.

        Therefore, if the User supplied an initial comment:

            Comment.employee_id == user_id

        Source TicketUser
        -----------------

        user_ticket_id must be positive.

        Contact User
        ------------

        If contact_user_id is not specified:

            contact_user_id = user_id
        """

        if user_id <= 0:
            raise ItemValidationError(
                "User id must be positive"
            )

        if user_ticket_id <= 0:
            raise ItemValidationError(
                "User ticket id must be positive"
            )

        return cls._create_new(
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            initial_status=TicketStatus.CREATED_FROM_TICKET_USER,
            actor_employee_id=0,
            comment_employee_id=user_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            user_ticket_id=user_ticket_id,
            department_id=department_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            comment=comment,
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        ticket_id: int,
        client_id: int,
        text_of_ticket: str,
        statuses: list[TicketStatusRecord],
        date_created: datetime,
        user_id: int = 0,
        contact_user_id: int = 0,
        comments: list[Comment] | None = None,
        department_id: int = 0,
        user_ticket_id: int = 0,
        description: str = "",
        remote_work_recommended: bool = False,
        urgency: TicketUrgency = TicketUrgency.NORMAL,
        planned_at: datetime | None = None,
        version: int = 0,
    ) -> Self:
        """
        Rehydrate a persisted Ticket.

        Repository contract
        -------------------

        Repository must provide:

        - ticket_id > 0;
        - complete workflow history;
        - workflow history in persistence order;
        - UTC datetime values;
        - persisted aggregate data without normalization.

        Workflow reconstruction
        -----------------------

        Only the first persisted status is passed to the constructor.

        Remaining records are replayed through append_status():

            statuses[0]
                -> constructor / __post_init__

            statuses[1:]
                -> append_status(...)

        Therefore persisted workflow history cannot bypass transition and
        chronology checks.

        Contact User
        ------------

        Unlike creation factories, rehydrate does not resolve or substitute
        contact_user_id.

        Persisted state is restored exactly as stored and then validated.

        planned_at
        ----------

        Persisted planned_at may be earlier than today's date.

        Rehydrate validates only that it uses UTC.

        Derived state
        -------------

        is_closed and date_finished are not loaded from persistence as
        independent domain state.

        They are reconstructed from workflow history.
        """

        if ticket_id <= 0:
            raise DomainOperationError(
                "Cannot rehydrate Ticket with non-positive ticket_id"
            )

        if not statuses:
            raise DomainOperationError(
                "Cannot rehydrate Ticket without status history"
            )

        ticket = cls(
            ticket_id=ticket_id,
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=contact_user_id,
            statuses=statuses[:1],
            comments=comments if comments is not None else [],
            date_created=date_created,
            department_id=department_id,
            user_ticket_id=user_ticket_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            version=version,
        )

        for status in statuses[1:]:
            ticket.append_status(status)

        return ticket

    # ==================================================================
    # Current state
    # ==================================================================

    def current_status_record(self) -> TicketStatusRecord:
        """
        Return the current workflow record.

        Ticket current state is always defined by the last record in the
        complete workflow history.
        """

        if not self.statuses:
            raise DomainOperationError(
                "Ticket has no status history"
            )

        return self.statuses[-1]

    def current_status(self) -> TicketStatus:
        """
        Return the current Ticket workflow status.
        """

        return self.current_status_record().status

    def is_terminal(self) -> bool:
        """
        Return True when Ticket is currently in a terminal workflow state.
        """

        return self.current_status() in TERMINAL_TICKET_STATUSES

    # ==================================================================
    # Executor
    # ==================================================================

    def current_executor_id(self) -> int:
        """
        Return the currently active executor.

        Executor-active statuses are defined by:

            current_status_record().rule.has_executors

        If the current status does not have an active executor:

            return 0

        When the current status does have an executor, the assignment is
        resolved from the nearest preceding ASSIGNED record.

        Workflow design guarantees that assignment-clearing states such as:

            ACCEPTED
            DEFERRED
            SUSPENDED

        cannot lead directly back into an executor-active state without a
        new ASSIGNED record.

        Therefore the nearest preceding ASSIGNED is the active assignment.
        """

        if not self.current_status_record().rule.has_executors:
            return 0

        for record in reversed(self.statuses):
            if record.status == TicketStatus.ASSIGNED:
                return record.executor_id

        raise DomainOperationError(
            "Ticket is in executor-active status "
            "but has no preceding ASSIGNED record"
        )

    def last_executor_id(self) -> int:
        """
        Return the most recently assigned executor.

        Unlike current_executor_id(), this method does not care whether the
        assignment is still active.

        It is intended for historical/analytical use.

        Returns:

            executor_id of the latest ASSIGNED record

        or:

            0

        when Ticket has never had an executor.
        """

        for record in reversed(self.statuses):
            if record.status == TicketStatus.ASSIGNED:
                return record.executor_id

        return 0

    # ==================================================================
    # Persistence helpers
    # ==================================================================

    def is_new(self) -> bool:
        """
        Return True when Ticket has not yet been persisted.

        New aggregate uses:

            ticket_id == 0
        """

        return self.ticket_id == 0

    def new_statuses(self) -> list[TicketStatusRecord]:
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
        Return comments not yet persisted.
        """

        return [
            comment
            for comment in self.comments
            if comment.is_new()
        ]

    # ==================================================================
    # Workflow
    # ==================================================================

    def append_status(
        self,
        record: TicketStatusRecord,
    ) -> None:
        """
        Append a new workflow status record.

        Responsibilities
        ----------------

        Ticket validates:

        1. workflow transition;
        2. chronological order;
        3. UTC datetime contract.

        TicketStatusRecord validates its own status-specific payload.

        Transition
        ----------

        Allowed next statuses are defined by:

            TICKET_TRANSITIONS[current_status]

        Chronology
        ----------

        New status cannot have date_created earlier than the current record.

        Equal timestamps are allowed.

        This is important because multiple workflow operations may be stored
        with the same timestamp resolution.
        """

        self._require_utc_datetime(
            record.date_created,
            field_name="status.date_created",
        )

        current_record = self.current_status_record()

        if record.status not in TICKET_TRANSITIONS[current_record.status]:
            raise DomainOperationError(
                "Ticket status transition is not allowed: "
                f"{current_record.status.value} -> "
                f"{record.status.value}",
            )

        if record.date_created < current_record.date_created:
            raise DomainOperationError(
                "Ticket status history must be chronological"
            )

        self.statuses.append(record)

        self._recompute_closed_state()

    # ==================================================================
    # Comments
    # ==================================================================

    def add_comment(
        self,
        comment: Comment,
    ) -> None:
        """
        Add an ordinary comment to Ticket.

        Comments cannot be added after Ticket reaches a terminal state.

        Comment.employee_id uses the common Admin/User identifier space.

        The comment datetime must use UTC.
        """

        if self.is_terminal():
            raise DomainOperationError(
                f"Cannot add comment to terminal Ticket "
                f"{self.ticket_id}",
            )

        if not comment.comment:
            raise DomainOperationError(
                "Comment cannot be empty",
            )

        self._require_utc_datetime(
            comment.date_created,
            field_name="comment.date_created",
        )

        self.comments.append(comment)

    # ==================================================================
    # Editable Ticket data
    # ==================================================================

    def change_department(
        self,
        *,
        department_id: int,
    ) -> None:
        """
        Change Ticket department.

        department_id == 0 means that department is not assigned.

        Negative department id is invalid.

        Whether Ticket data can currently be modified is determined by the
        current workflow rule:

            current_status_record().rule.can_change_data
        """

        if department_id < 0:
            raise DomainOperationError(
                "Ticket department_id cannot be negative",
            )

        if not self.current_status_record().rule.can_change_data:
            raise DomainOperationError(
                "Cannot change Ticket department in current status "
                f"{self.current_status()}",
            )

        self.department_id = department_id

    def change_contact_user(
        self,
        *,
        contact_user_id: int,
    ) -> None:
        """
        Change or clear contact User.

        Rules
        -----

        contact_user_id < 0:
            invalid.

        contact_user_id == 0:
            clear contact User.

            This is allowed only when Ticket.user_id == 0.

        contact_user_id > 0:
            set or replace contact User.

        If Ticket.user_id > 0, contact User is mandatory and therefore
        cannot be cleared.

        contact_user_id does not have to equal user_id.
        """

        if not self.current_status_record().rule.can_change_data:
            raise DomainOperationError(
                "Cannot change Ticket contact User in current status "
                f"{self.current_status()}",
            )

        if contact_user_id < 0:
            raise DomainOperationError(
                "Ticket contact_user_id cannot be negative",
            )

        if self.user_id > 0 and contact_user_id == 0:
            raise DomainOperationError(
                "Ticket with user_id must have contact_user_id",
            )

        self.contact_user_id = contact_user_id

    def update_description(
        self,
        *,
        description: str,
    ) -> None:
        """
        Update editable Ticket description.

        Leading and trailing whitespace is removed.

        Empty description is allowed.
        """

        if not self.current_status_record().rule.can_change_data:
            raise DomainOperationError(
                "Cannot change Ticket description in current status "
                f"{self.current_status()}",
            )

        self.description = description.strip()

    def set_remote_work_recommended(
        self,
        *,
        recommend: bool,
    ) -> None:
        """
        Set recommendation for remote execution.

        This value is Ticket data and is not a workflow state.
        """

        if not self.current_status_record().rule.can_change_data:
            raise DomainOperationError(
                "Cannot change remote work recommendation "
                f"in current status {self.current_status()}",
            )

        self.remote_work_recommended = recommend

    def change_urgency(
        self,
        *,
        urgency: TicketUrgency,
    ) -> None:
        """
        Change Ticket urgency.

        Runtime validation is intentional.

        Python type annotations do not guarantee that caller actually passed
        a TicketUrgency instance.
        """

        if not self.current_status_record().rule.can_change_data:
            raise DomainOperationError(
                "Cannot change Ticket urgency in current status "
                f"{self.current_status()}",
            )

        if not isinstance(urgency, TicketUrgency):
            raise DomainOperationError(
                "Invalid Ticket urgency"
            )

        self.urgency = urgency

    # ==================================================================
    # Planning
    # ==================================================================

    def schedule(
        self,
        *,
        planned_at: datetime,
    ) -> None:
        """
        Set current planned execution date/time.

        planned_at is independent from workflow state.

        Rules
        -----

        planned_at must:

        - use UTC;
        - belong to today's or a future UTC calendar date.

        The clock time may already have passed if the date is today.

        Example:

            current time:
                2026-09-26 17:00 UTC

            valid:
                2026-09-26 10:00 UTC

            invalid:
                2026-09-25 23:59 UTC

        This validation applies only when planning is being changed.

        Rehydrate intentionally does not apply the "not before today"
        requirement because persisted planning may already refer to a past
        date.
        """

        if not self.current_status_record().rule.can_change_data:
            raise DomainOperationError(
                "Cannot set planned_at in current Ticket status"
            )

        now = datetime.now(UTC)

        self._validate_new_planned_at(
            planned_at,
            reference_time=now,
        )

        self.planned_at = planned_at

    def clear_schedule(self) -> None:
        """
        Remove current planning value.

        This does not change workflow status.
        """

        if not self.current_status_record().rule.can_change_data:
            raise DomainOperationError(
                "Cannot clear planned_at in current Ticket status"
            )

        self.planned_at = None

    # ==================================================================
    # Analytics
    # ==================================================================

    def working_time(self) -> int:
        """
        Return total actual work time in seconds.

        Only AT_WORK records contribute to work time.

        An AT_WORK record can describe work duration in three ways.

        Case 1: explicit non-zero duration
        ----------------------------------

        If:

            record.duration != 0

        duration is used directly.

        Case 2: retrospective interval
        ------------------------------

        If duration is zero and both:

            actual_started_at
            actual_finished_at

        are present, their exact difference is used.

        Case 3: workflow interval
        -------------------------

        If duration is zero and no complete retrospective interval exists,
        work is measured from:

            AT_WORK.date_created

        until:

            next status.date_created

        or, if AT_WORK is the current status:

            datetime.now(UTC)

        A zero duration intentionally means that time must be derived from
        datetime values. It is not treated as an absent value.
        """

        total_seconds = 0
        now = datetime.now(UTC)

        for index, record in enumerate(self.statuses):
            if record.status != TicketStatus.AT_WORK:
                continue

            # A non-zero explicit duration has the highest priority.
            if record.duration:
                total_seconds += int(
                    record.duration.total_seconds()
                )
                continue

            # Retrospective exact work interval.
            if (
                record.actual_started_at is not None
                and record.actual_finished_at is not None
            ):
                total_seconds += int(
                    (
                        record.actual_finished_at
                        - record.actual_started_at
                    ).total_seconds()
                )
                continue

            # Normal workflow timing.
            if index + 1 < len(self.statuses):
                finish_at = self.statuses[index + 1].date_created
            else:
                finish_at = now

            total_seconds += int(
                (
                    finish_at
                    - record.date_created
                ).total_seconds()
            )

        return total_seconds

    # ==================================================================
    # Validation
    # ==================================================================

    def _validate_identity(self) -> None:
        """
        Validate identifiers and identity-related aggregate invariants.

        This method validates stable Ticket invariants.

        It does not verify existence of referenced entities. For example,
        Ticket does not query whether client_id, user_id or department_id
        actually exists.
        """

        if self.ticket_id < 0:
            raise DomainOperationError(
                "Ticket ticket_id cannot be negative",
            )

        if self.client_id <= 0:
            raise DomainOperationError(
                "Ticket client_id must be positive",
            )

        if self.user_id < 0:
            raise DomainOperationError(
                "Ticket user_id cannot be negative",
            )

        if self.contact_user_id < 0:
            raise DomainOperationError(
                "Ticket contact_user_id cannot be negative",
            )

        # A Ticket associated with a User must always have a contact User.
        #
        # The contact User does not have to be the same User.
        if self.user_id > 0 and self.contact_user_id == 0:
            raise DomainOperationError(
                "Ticket with user_id must have contact_user_id",
            )

        if self.department_id < 0:
            raise DomainOperationError(
                "Ticket department_id cannot be negative",
            )

        if self.version < 0:
            raise DomainOperationError(
                "Ticket version cannot be negative",
            )

        if not isinstance(self.urgency, TicketUrgency):
            raise DomainOperationError(
                "Invalid Ticket urgency"
            )

        if self.user_ticket_id < 0:
            raise DomainOperationError(
                "Ticket user_ticket_id cannot be negative",
            )

    def _validate_content(self) -> None:
        """
        Validate immutable Ticket content.
        """

        if not self.text_of_ticket:
            raise DomainOperationError(
                "Ticket text_of_ticket cannot be empty",
            )

    def _validate_datetimes(self) -> None:
        """
        Validate Ticket datetime contract.

        All datetime values directly owned by Ticket must use UTC.

        Persisted planned_at may be in the past; this method intentionally
        validates only timezone, not its calendar date.

        Status and comment timestamps currently present in the aggregate are
        also checked because they form part of Ticket history.
        """

        self._require_utc_datetime(
            self.date_created,
            field_name="date_created",
        )

        if self.planned_at is not None:
            self._require_utc_datetime(
                self.planned_at,
                field_name="planned_at",
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

    def _validate_creation_origin(self) -> None:
        """
        Validate relation between the first workflow status and Ticket origin.

        This validation is important primarily for rehydrate().

        It prevents corrupted persisted state from being accepted merely
        because individual field values are valid.

        CREATED
        -------

        A Ticket created directly by Admin does not originate from
        TicketUser:

            user_ticket_id == 0

        CREATED_FROM_TICKET_USER
        ------------------------

        Such Ticket must have:

            user_ticket_id > 0
            user_id > 0

        Other details of the first TicketStatusRecord remain the
        responsibility of TicketStatusRecord itself.
        """

        first_status = self.statuses[0].status

        if first_status == TicketStatus.CREATED:
            if self.user_ticket_id != 0:
                raise DomainOperationError(
                    "Ticket with CREATED status "
                    "cannot have user_ticket_id"
                )

            return

        if first_status == TicketStatus.CREATED_FROM_TICKET_USER:
            if self.user_ticket_id <= 0:
                raise DomainOperationError(
                    "Ticket created from TicketUser "
                    "must have user_ticket_id"
                )

            if self.user_id <= 0:
                raise DomainOperationError(
                    "Ticket created from TicketUser "
                    "must have user_id"
                )

    @staticmethod
    def _require_utc_datetime(
        value: datetime,
        *,
        field_name: str,
    ) -> None:
        """
        Require an explicitly UTC datetime.

        The domain intentionally does not normalize timezones.

        Valid:

            datetime(..., tzinfo=UTC)

        Invalid:

            datetime(...)

        Invalid:

            datetime(..., tzinfo=<non-UTC timezone>)

        External layers are responsible for converting values to UTC before
        passing them into domain objects.
        """

        if value.tzinfo is not UTC:
            raise DomainOperationError(
                f"Ticket {field_name} must use UTC timezone"
            )

    @classmethod
    def _validate_new_planned_at(
        cls,
        planned_at: datetime,
        *,
        reference_time: datetime,
    ) -> None:
        """
        Validate planned_at when a new planning value is being assigned.

        Both planned_at and reference_time must use UTC.

        The comparison intentionally uses calendar dates rather than full
        datetime values.

        Therefore an earlier time today is valid, while any time yesterday
        is invalid.
        """

        cls._require_utc_datetime(
            planned_at,
            field_name="planned_at",
        )

        cls._require_utc_datetime(
            reference_time,
            field_name="planning reference_time",
        )

        if planned_at.date() < reference_time.date():
            raise DomainOperationError(
                "planned_at cannot be earlier than today"
            )

    # ==================================================================
    # Derived state
    # ==================================================================

    def _recompute_closed_state(self) -> None:
        """
        Recompute derived closing state from current workflow status.

        is_closed and date_finished are never authoritative independent
        values.

        For a terminal Ticket:

            is_closed = True
            date_finished = current_status_record().date_created

        Otherwise:

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
