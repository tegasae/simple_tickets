from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import (
    TICKET_STATUS_RULES,
    TicketStatus,
)
from src.domain.value_objects import CommonComment, Empty


@dataclass(frozen=True, slots=True, kw_only=True)
class TicketStatusRecord:
    """
    Historical record of a Ticket workflow status.

    The record represents one concrete status change in Ticket history.

    Responsibilities
    ----------------

    TicketStatusRecord validates only its own intrinsic payload:

    - persistent identity;
    - status type;
    - actor identity;
    - required comment;
    - executor payload;
    - work payload;
    - datetime contract.

    It does not validate transitions between Ticket statuses.

    Allowed transitions are defined separately by:

        TICKET_TRANSITIONS


    status
    ------

    Ticket workflow status represented by this record.

    The value must be an instance of TicketStatus.


    actor_employee_id
    -----------------

    Identifier of the actor who performed the workflow action.

    The actor realm is determined by TicketStatusRule:

        user_action == False
            action is performed by Admin

        user_action == True
            action is performed by User

    In the current Ticket model some User actions may use:

        actor_employee_id == 0

    Therefore actor validation must follow the semantics of the concrete
    status rather than assuming that every actor identifier is positive.


    status_id
    ---------

    Persistent identifier of the status record.

        status_id == 0
            record has not been persisted yet

        status_id > 0
            persisted record

        status_id < 0
            invalid


    executor_id
    -----------

    Executor assigned to the Ticket.

    Required only when the corresponding TicketStatusRule declares:

        requires_executor == True

    For statuses that do not allow executor assignment:

        executor_id must be 0.


    comment
    -------

    Optional status comment.

    The absence of a comment is represented by Empty.

    Some statuses require a comment according to:

        TicketStatusRule.requires_comment


    Work payload
    ------------

    Work payload is allowed only for statuses whose rule declares:

        allows_work_data == True

    The payload may contain:

        actual_started_at
        actual_finished_at
        duration
        work_is_remote

    The current workflow model uses these values for AT_WORK.


    actual_started_at / actual_finished_at
    --------------------------------------

    These fields represent an exact retrospective work interval.

    They must:

    - either both be specified or both be absent;
    - use UTC;
    - satisfy actual_finished_at > actual_started_at.

    Exact timestamps are an alternative to explicit duration.


    duration
    --------

    Explicit actual work duration.

    Used when exact start/finish timestamps are not known.

    duration must be positive.

    duration cannot be specified together with an exact retrospective
    interval.


    work_is_remote
    --------------

    Describes how this concrete work episode was actually performed:

        True
            remotely

        False
            on site

        None
            not specified

    Whether this value is required is determined by:

        TicketStatusRule.requires_work_mode

    This field is different from Ticket.remote_work_recommended.

    Ticket.remote_work_recommended describes a recommendation/property
    of the Ticket.

    work_is_remote describes how one concrete work episode was actually
    performed.


    Date/time contract
    ------------------

    All datetime values inside domain use UTC.

    Therefore:

        date_created
        actual_started_at
        actual_finished_at

    must explicitly use datetime.UTC when present.

    The domain rejects:

    - naive datetime;
    - datetime values using another timezone.

    The domain does not automatically normalize other timezones to UTC.

    Conversion must happen before values enter the domain.
    """

    status: TicketStatus
    actor_employee_id: int

    # Persistent identifier of this status record.
    #
    # 0 means that the record has not been persisted yet.
    status_id: int = 0

    # Executor assigned by this status.
    #
    # Only statuses whose rule requires executor may have executor_id > 0.
    executor_id: int = 0

    # Optional status comment.
    #
    # Empty represents the absence of a comment.
    comment: CommonComment | Empty = field(
        default_factory=Empty,
    )

    # Exact retrospective work interval.
    #
    # These values are used only when work data is allowed by the
    # corresponding status rule.
    actual_started_at: datetime | None = None
    actual_finished_at: datetime | None = None

    # Explicit work duration.
    #
    # This is an alternative to actual_started_at + actual_finished_at.
    duration: timedelta | None = None

    # Actual work mode for this concrete work episode.
    work_is_remote: bool | None = None

    # Time when this status record was created.
    #
    # Newly created records use UTC automatically.
    # Rehydrated records must already contain UTC datetime.
    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        """
        Validate complete intrinsic state of the status record.

        Validation is intentionally divided into small methods:

        - _validate_identity()
        - _validate_actor()
        - _validate_comment()
        - _validate_executor()
        - _validate_work_payload()

        Transition validation does not belong here.
        """

        self._validate_identity()
        self._validate_actor()
        self._validate_comment()
        self._validate_executor()
        self._validate_work_payload()

    @property
    def rule(self):
        """
        Return intrinsic rules for the current Ticket status.

        These rules describe properties of the status itself.

        They do not define allowed workflow transitions.
        """

        return TICKET_STATUS_RULES[self.status]

    def is_new(self) -> bool:
        """
        Return True when this status record has not been persisted yet.

        New records use:

            status_id == 0
        """

        return not bool(self.status_id)

    # ==================================================================
    # Identity
    # ==================================================================

    def _validate_identity(self) -> None:
        """
        Validate persistent identity, status type and creation time.

        status_id
        ---------

        Negative values are not allowed.

        status
        ------

        Must be an instance of TicketStatus.

        date_created
        ------------

        Must explicitly use UTC.
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
        Validate actor identity.

        For Admin actions actor_employee_id must be positive.

        For User actions the current Ticket model may use
        actor_employee_id == 0.

        Negative actor identifiers are never allowed.
        """

        if self.rule.user_action:
            if self.actor_employee_id < 0:
                raise ItemValidationError(
                    "Actor employee ID cannot be negative"
                )
            return

        if self.actor_employee_id <= 0:
            raise ItemValidationError(
                "Actor employee ID must be positive"
            )

    # ==================================================================
    # Comment
    # ==================================================================

    def _validate_comment(self) -> None:
        """
        Validate comment requirements.

        Most statuses allow an empty comment.

        If:

            rule.requires_comment == True

        the record must contain CommonComment rather than Empty.
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

        If the status requires executor:

            executor_id must be positive.

        Otherwise:

            executor_id must be exactly 0.
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
        Validate all work-related payload.

        Work payload is allowed only when:

            rule.allows_work_data == True

        If work data is not allowed, none of these fields may be set:

            actual_started_at
            actual_finished_at
            duration
            work_is_remote

        If work data is allowed, validation is delegated to:

            _validate_work_mode()
            _validate_work_time()
        """

        has_started_at = self.actual_started_at is not None
        has_finished_at = self.actual_finished_at is not None
        has_duration = self.duration is not None
        has_work_mode = self.work_is_remote is not None

        if not self.rule.allows_work_data:
            if (
                has_started_at
                or has_finished_at
                or has_duration
                or has_work_mode
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

        If the status requires work mode:

            work_is_remote must be either True or False.

        None means that work mode was not specified.
        """

        if self.rule.requires_work_mode:
            if self.work_is_remote is None:
                raise ItemValidationError(
                    f"{self.status} requires work mode"
                )

    def _validate_work_time(self) -> None:
        """
        Validate actual work time payload.

        Work time can be represented in one of two explicit forms:

        1. exact retrospective interval:

               actual_started_at
               actual_finished_at

        2. explicit duration:

               duration

        These forms are mutually exclusive.

        If neither form is supplied, work time may later be derived by
        Ticket from workflow timestamps.

        Exact interval
        --------------

        actual_started_at and actual_finished_at must:

        - be specified together;
        - explicitly use UTC;
        - satisfy:

              actual_finished_at > actual_started_at

        Duration
        --------

        duration must be strictly positive.
        """

        has_started_at = self.actual_started_at is not None
        has_finished_at = self.actual_finished_at is not None
        has_duration = self.duration is not None

        # Exact retrospective interval must be complete.
        if has_started_at != has_finished_at:
            raise ItemValidationError(
                "actual_started_at and actual_finished_at "
                "must be specified together"
            )

        # Exact interval and duration represent alternative forms
        # of the same work-time information.
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

        if has_duration:
            assert self.duration is not None

            if self.duration <= timedelta(0):
                raise ItemValidationError(
                    "Work duration must be positive"
                )

    # ==================================================================
    # Datetime helpers
    # ==================================================================

    @staticmethod
    def _validate_utc_datetime(
        value: datetime,
        *,
        field_name: str,
    ) -> None:
        """
        Validate the domain datetime contract.

        The value must:

        - be a datetime instance;
        - explicitly use datetime.UTC.

        The domain rejects both:

        - naive datetime values;
        - timezone-aware values from any timezone other than UTC.

        No timezone conversion is performed here.
        """

        if not isinstance(value, datetime):
            raise ItemValidationError(
                f"{field_name} must be datetime"
            )

        if value.tzinfo is not UTC:
            raise ItemValidationError(
                f"{field_name} must use UTC timezone"
            )

