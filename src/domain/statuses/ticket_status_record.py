from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import (
    TICKET_STATUS_RULES,
    TicketStatus,
    TicketStatusRule,
)
from src.domain.value_objects import CommonComment, Empty


@dataclass(slots=True, kw_only=True)
class TicketStatusRecord:
    """
    Historical record of a Ticket workflow status.

    TicketStatusRecord represents one concrete entry in Ticket workflow
    history.

    The record validates only its own intrinsic payload.

    It does not know:

    - previous Ticket status;
    - next Ticket status;
    - current Ticket executor;
    - complete Ticket workflow history.

    Context-dependent workflow validation belongs to Ticket.

    In particular, rules such as:

        "only the currently assigned executor may pause work"

    cannot be validated here because TicketStatusRecord does not know
    who the current executor is.


    Status
    ======

    status is the resulting Ticket workflow status.

    The value must be TicketStatus.


    Actor
    =====

    actor_employee_id identifies the actor representation stored in the
    internal Ticket history.

    For Admin actions:

        rule.user_action == False

    actor_employee_id must be positive.

    For User actions:

        rule.user_action == True

    the current Ticket model deliberately stores:

        actor_employee_id == 0

    The actual User identity belongs to the related Ticket/TicketUser data
    rather than this field.

    Therefore:

        Admin action -> actor_employee_id > 0
        User action  -> actor_employee_id == 0

    Negative values are never allowed.


    Persistent identity
    ===================

    status_id == 0:
        new record, not persisted yet.

    status_id > 0:
        persisted record.

    status_id < 0:
        invalid.


    Executor
    ========

    executor_id is used only by statuses whose TicketStatusRule declares:

        requires_executor == True

    Currently ASSIGNED requires executor_id > 0.

    Other statuses must have:

        executor_id == 0


    Comment
    =======

    Empty represents absence of a status comment.

    If:

        rule.requires_comment == True

    the status record must contain CommonComment.


    Work data
    =========

    Work-related payload is allowed only when:

        rule.allows_work_data == True

    Currently AT_WORK is the status that allows actual work data.

    Work data consists of:

        actual_started_at
        actual_finished_at
        duration
        work_is_remote


    Work time representation
    ========================

    Work time may be represented in three ways.

    1. Exact retrospective interval:

        actual_started_at != None
        actual_finished_at != None
        duration == timedelta(0)

    2. Explicit retrospective duration:

        actual_started_at == None
        actual_finished_at == None
        duration > timedelta(0)

    3. No explicit retrospective work time:

        actual_started_at == None
        actual_finished_at == None
        duration == timedelta(0)

    In the third case Ticket may derive work time from workflow timestamps.

    duration == timedelta(0) therefore means:

        explicit duration is not specified

    It is not an error.

    Negative duration is invalid.

    Exact retrospective interval and positive explicit duration are mutually
    exclusive.


    Work mode
    =========

    work_is_remote describes how this concrete work episode was actually
    performed:

        True  -> remote
        False -> on site
        None  -> not specified

    AT_WORK currently requires work mode.

    This is different from Ticket.remote_work_recommended, which is only a
    recommendation/property of the Ticket.


    Date/time contract
    ==================

    All datetime values in the domain must explicitly use UTC.

    The following fields therefore require datetime.UTC when present:

        date_created
        actual_started_at
        actual_finished_at

    Naive datetime values are rejected.

    Datetime values using another timezone are also rejected.

    The domain never converts values to UTC automatically.
    """

    status: TicketStatus
    actor_employee_id: int

    status_id: int = 0

    executor_id: int = 0

    comment: CommonComment | Empty = field(
        default_factory=Empty,
    )

    actual_started_at: datetime | None = None
    actual_finished_at: datetime | None = None

    # Zero means that explicit duration is not specified.
    duration: timedelta = field(
        default_factory=timedelta,
    )

    work_is_remote: bool | None = None

    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    def __post_init__(self) -> None:
        """
        Validate complete intrinsic payload of the record.

        Workflow-context validation intentionally does not belong here.
        """

        self._validate_identity()
        self._validate_actor()
        self._validate_comment()
        self._validate_executor()
        self._validate_work_payload()

    @property
    def rule(self) -> TicketStatusRule:
        """
        Return intrinsic rule for this status.
        """

        return TICKET_STATUS_RULES[self.status]

    def is_new(self) -> bool:
        """
        Return True when this status record has not been persisted.
        """

        return self.status_id == 0

    # ==================================================================
    # Identity
    # ==================================================================

    def _validate_identity(self) -> None:
        """
        Validate status record identity and creation timestamp.
        """

        if self.status_id < 0:
            raise ItemValidationError(
                "Status record ID cannot be negative"
            )

        if not isinstance(self.status, TicketStatus):
            raise ItemValidationError(
                "Invalid Ticket status"
            )

        self._validate_utc_datetime(
            self.date_created,
            field_name="Status record date_created",
        )

    # ==================================================================
    # Actor
    # ==================================================================

    def _validate_actor(self) -> None:
        """
        Validate actor according to TicketStatusRule.

        User actions
        ------------

        The internal Ticket history does not store User ID in
        actor_employee_id.

        Therefore:

            actor_employee_id == 0

        is required.

        Admin actions
        -------------

        Admin actions always store the real employee identifier:

            actor_employee_id > 0
        """

        if self.rule.user_action:
            if self.actor_employee_id != 0:
                raise ItemValidationError(
                    "User action must have actor_employee_id equal to 0"
                )
            return

        if self.actor_employee_id <= 0:
            raise ItemValidationError(
                "Admin action requires positive actor_employee_id"
            )

    # ==================================================================
    # Comment
    # ==================================================================

    def _validate_comment(self) -> None:
        """
        Validate status comment requirement.
        """

        if (
            self.rule.requires_comment
            and isinstance(self.comment, Empty)
        ):
            raise ItemValidationError(
                f"{self.status} requires a comment"
            )

    # ==================================================================
    # Executor
    # ==================================================================

    def _validate_executor(self) -> None:
        """
        Validate executor payload.

        A status requiring executor must contain executor_id > 0.

        Every other status must contain executor_id == 0.
        """

        if self.rule.requires_executor:
            if self.executor_id <= 0:
                raise ItemValidationError(
                    f"{self.status} requires a positive executor ID"
                )
            return

        if self.executor_id != 0:
            raise ItemValidationError(
                f"{self.status} does not allow executor ID"
            )

    # ==================================================================
    # Work payload
    # ==================================================================

    def _validate_work_payload(self) -> None:
        """
        Validate complete work-related payload.

        Work data is allowed only for statuses whose intrinsic rule has:

            allows_work_data == True

        Zero duration does not count as explicit work data.
        """

        if not isinstance(self.duration, timedelta):
            raise ItemValidationError(
                "duration must be timedelta"
            )

        if self.work_is_remote is not None:
            if not isinstance(self.work_is_remote, bool):
                raise ItemValidationError(
                    "work_is_remote must be bool or None"
                )

        has_started_at = self.actual_started_at is not None
        has_finished_at = self.actual_finished_at is not None

        # timedelta(0) means explicit duration is absent.
        has_duration = self.duration != timedelta(0)

        #has_work_mode = self.work_is_remote is not None

        if not self.rule.allows_work_data:
            if (
                has_started_at
                or has_finished_at
                or has_duration
         #       or has_work_mode
            ):
                raise ItemValidationError(
                    f"{self.status} does not allow work data"
                )

            return

        self._validate_work_mode()
        self._validate_work_time()

    def _validate_work_mode(self) -> None:
        """
        Validate actual work mode.

        When the status requires work mode, work_is_remote must be
        explicitly True or False.
        """

        if (
            self.rule.requires_work_mode
            and self.work_is_remote is None
        ):
            raise ItemValidationError(
                f"{self.status} requires work mode"
            )

    def _validate_work_time(self) -> None:
        """
        Validate work-time representation.

        Exact retrospective interval
        ----------------------------

        actual_started_at and actual_finished_at must either both be present
        or both be absent.

        When present:

        - both must use UTC;
        - finished time must be later than started time;
        - explicit positive duration must not also be supplied.

        Explicit duration
        -----------------

        duration == timedelta(0):
            explicit duration is absent.

        duration > timedelta(0):
            explicit work duration.

        duration < timedelta(0):
            invalid.
        """

        has_started_at = self.actual_started_at is not None
        has_finished_at = self.actual_finished_at is not None

        if self.duration < timedelta(0):
            raise ItemValidationError(
                "Work duration cannot be negative"
            )

        has_duration = self.duration > timedelta(0)

        if has_started_at != has_finished_at:
            raise ItemValidationError(
                "actual_started_at and actual_finished_at "
                "must be specified together"
            )

        if has_started_at and has_duration:
            raise ItemValidationError(
                "Work interval and duration cannot be specified together"
            )

        if has_started_at:
            assert self.actual_started_at is not None
            assert self.actual_finished_at is not None

            self._validate_utc_datetime(
                self.actual_started_at,
                field_name="actual_started_at",
            )

            self._validate_utc_datetime(
                self.actual_finished_at,
                field_name="actual_finished_at",
            )

            if self.actual_finished_at <= self.actual_started_at:
                raise ItemValidationError(
                    "actual_finished_at must be later than "
                    "actual_started_at"
                )

    # ==================================================================
    # Datetime
    # ==================================================================

    @staticmethod
    def _validate_utc_datetime(
        value: datetime,
        *,
        field_name: str,
    ) -> None:
        """
        Require an explicitly UTC datetime.

        No automatic timezone normalization is performed.
        """

        if not isinstance(value, datetime):
            raise ItemValidationError(
                f"{field_name} must be datetime"
            )

        if value.tzinfo is not UTC:
            raise ItemValidationError(
                f"{field_name} must use UTC timezone"
            )