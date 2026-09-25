from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from src.domain.statuses.ticket_status import (
    TICKET_STATUS_RULES,
    TicketStatus,
)


from src.domain.exceptions import ItemValidationError
from src.domain.value_objects import CommonComment, Empty


@dataclass(frozen=True, slots=True, kw_only=True)
class TicketStatusRecord:
    """
    Historical record of a Ticket status.

    A record contains:

    - the resulting Ticket status;
    - the actor who performed the action;
    - optional status-specific payload;
    - the time when the record was created.

    The record validates only its own payload.

    Allowed transitions between statuses are defined separately by
    TICKET_TRANSITIONS.

    Fields
    ------
    status_id:
        Persistent identifier of the status record.

        Zero means that the record has not been persisted yet.
        Negative values are not allowed.

    status:
        Ticket status represented by this record.

    actor_employee_id:
        Identifier of the employee who performed the action.

        The actor realm is determined by TicketStatusRule:

        - user_action=False -> Admin;
        - user_action=True  -> User.

    executor_id:
        Executor assigned to the Ticket.

        Required for ASSIGNED.
        For other statuses it must be zero.

    comment:
        Optional status comment.

        Some statuses require a non-empty comment according to
        TicketStatusRule.

    actual_started_at:
        Actual start time of retrospectively registered work.

        Used only by AT_WORK.

    actual_finished_at:
        Actual finish time of retrospectively registered work.

        Used only by AT_WORK.

    duration:
        Actual work duration when exact start and finish times are
        unknown.

        Used only by AT_WORK.

        duration is an alternative to
        actual_started_at + actual_finished_at.

    work_is_remote:
        Describes how this concrete work episode was actually
        performed:

        - True  -> remotely;
        - False -> on site;
        - None  -> not specified.

        This field is required for AT_WORK and must not be set for
        other statuses.

        It is different from Ticket.is_remote. Ticket.is_remote is a
        recommendation/property of the Ticket, while work_is_remote
        records how this particular work episode was actually
        performed.

    date_created:
        Time when this status record was created.
    """

    status: TicketStatus
    actor_employee_id: int

    status_id: int = 0
    executor_id: int = 0

    comment: CommonComment | Empty = field(default_factory=Empty)

    actual_started_at: datetime | None = None
    actual_finished_at: datetime | None = None
    duration: timedelta | None = None

    work_is_remote: bool | None = None

    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        self._validate_identity()
        self._validate_actor()
        self._validate_comment()
        self._validate_executor()
        self._validate_work_payload()

    @property
    def rule(self):
        """
        Return intrinsic rules for this status.
        """
        return TICKET_STATUS_RULES[self.status]

    def _validate_identity(self) -> None:
        if self.status_id < 0:
            raise ItemValidationError(
                "Status record ID cannot be negative"
            )

        if not isinstance(self.status, TicketStatus):
            raise ItemValidationError(
                "Invalid Ticket status"
            )

        if self.date_created.tzinfo is None:
            raise ItemValidationError(
                "Status record date_created must be timezone-aware"
            )

    def _validate_actor(self) -> None:
        if self.actor_employee_id <= 0:
            raise ItemValidationError(
                "Actor employee ID must be positive"
            )

    def _validate_comment(self) -> None:
        if self.rule.requires_comment and isinstance(self.comment, Empty):
            raise ItemValidationError(
                f"{self.status} requires a comment"
            )

    def _validate_executor(self) -> None:
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

    def _validate_work_payload(self) -> None:
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
        if self.rule.requires_work_mode:
            if self.work_is_remote is None:
                raise ItemValidationError(
                    f"{self.status} requires work mode"
                )

    def _validate_work_time(self) -> None:
        has_started_at = self.actual_started_at is not None
        has_finished_at = self.actual_finished_at is not None
        has_duration = self.duration is not None

        # Exact retrospective interval must be complete.
        if has_started_at != has_finished_at:
            raise ItemValidationError(
                "actual_started_at and actual_finished_at "
                "must be specified together"
            )

        # Exact interval and explicit duration are alternative forms
        # of representing actual work.
        if has_started_at and has_duration:
            raise ItemValidationError(
                "Work interval and duration cannot be specified together"
            )

        if has_started_at:
            assert self.actual_started_at is not None
            assert self.actual_finished_at is not None

            if self.actual_started_at.tzinfo is None:
                raise ItemValidationError(
                    "actual_started_at must be timezone-aware"
                )

            if self.actual_finished_at.tzinfo is None:
                raise ItemValidationError(
                    "actual_finished_at must be timezone-aware"
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