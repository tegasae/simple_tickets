
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime, timedelta
from typing import get_type_hints

from src.domain.datetime_check import validate_utc_datetime
from src.domain.exceptions import ItemValidationError
from src.domain.statuses.rules.ticket_status_rule import TicketStatusRule, TICKET_STATUS_RULES
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.value_objects import CommonComment, Empty


@dataclass(slots=True, kw_only=True)
class TicketStatusRecord:
    """
    Historical record of a Ticket workflow status.

    Validates:
    - field types and ranges;
    - UTC datetime values;
    - consistency of work-time data;
    - intrinsic TicketStatusRule requirements.

    Ticket validates aggregate-dependent rules:
    - workflow transitions;
    - current executor;
    - creation origin and other Ticket context.
    """

    status: TicketStatus

    actor_employee_id: int = field(
        metadata={"min": 0},
    )

    status_id: int = field(
        default=0,
        metadata={"min": 0},
    )

    executor_id: int = field(
        default=0,
        metadata={"min": 0},
    )

    comment: str | CommonComment | Empty = ""

    actual_started_at: datetime | None = None
    actual_finished_at: datetime | None = None

    duration: timedelta = timedelta(0)

    work_is_remote: bool | None = None

    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    def __post_init__(self) -> None:
        self._validate_types()
        self._validate_ranges()
        self._validate_datetimes()
        self._validate_work_data()
        self._check_rules()

    def is_new(self) -> bool:
        return self.status_id == 0

    @property
    def rule(self) -> TicketStatusRule:
        return TICKET_STATUS_RULES[self.status]

    @property
    def has_retrospective_work_time(self) -> bool:
        return (
                self.actual_started_at is not None
                or self.actual_finished_at is not None
                or self.duration > timedelta(0)
        )
    # ==============================================================
    # Intrinsic status rules
    # ==============================================================

    def _check_rules(self) -> None:
        rule = self.rule

        # Actor
        if rule.user_action:
            if self.actor_employee_id != 0:
                raise ItemValidationError(
                    f"{self.status} requires a User action"
                )
        else:
            if self.actor_employee_id == 0:
                raise ItemValidationError(
                    f"{self.status} requires an Admin actor"
                )

        # Comment
        if isinstance(self.comment, str):
            try:
                self.comment = CommonComment(self.comment)
            except ValueError:
                self.comment = Empty()

        if rule.requires_comment and isinstance(self.comment, Empty):
            raise ItemValidationError(
                f"Comment is required for {self.status}"
            )

        # Executor
        if rule.requires_executor and self.executor_id == 0:
            raise ItemValidationError(
                f"Executor is required for {self.status}"
            )

        # Work data


        if not rule.allows_work_data and self.has_retrospective_work_time:
            raise ItemValidationError(
                f"Work data is not allowed for {self.status}"
            )

        # Work mode
        if rule.requires_work_mode:
            if self.work_is_remote is None:
                raise ItemValidationError(
                    f"Work mode is required for {self.status}"
                )
        elif self.work_is_remote is not None:
            raise ItemValidationError(
                f"Work mode is not allowed for {self.status}"
            )

    # ==============================================================
    # Types
    # ==============================================================

    def _validate_types(self) -> None:
        hints = get_type_hints(type(self))

        for f in fields(self):
            value = getattr(self, f.name)
            expected_type = hints[f.name]

            if expected_type is int:
                valid = type(value) is int
            else:
                valid = isinstance(value, expected_type)

            if not valid:
                raise ItemValidationError(
                    f"{f.name}: expected {expected_type}, "
                    f"got {type(value).__name__}"
                )

    # ==============================================================
    # Ranges
    # ==============================================================

    def _validate_ranges(self) -> None:
        for f in fields(self):
            value = getattr(self, f.name)

            if "min" in f.metadata and value < f.metadata["min"]:
                raise ItemValidationError(
                    f"{f.name} must be >= {f.metadata['min']}"
                )

            if "max" in f.metadata and value > f.metadata["max"]:
                raise ItemValidationError(
                    f"{f.name} must be <= {f.metadata['max']}"
                )

    # ==============================================================
    # Datetimes
    # ==============================================================

    def _validate_datetimes(self) -> None:
        validate_utc_datetime(
            self.date_created,
            field_name="date_created",
        )

        if self.actual_started_at is not None:
            validate_utc_datetime(
                self.actual_started_at,
                field_name="actual_started_at",
            )

        if self.actual_finished_at is not None:
            validate_utc_datetime(
                self.actual_finished_at,
                field_name="actual_finished_at",
            )

    # ==============================================================
    # Work data integrity
    # ==============================================================

    def _validate_work_data(self) -> None:
        if self.duration < timedelta(0):
            raise ItemValidationError(
                "Work duration cannot be negative"
            )

        started_at = self.actual_started_at
        finished_at = self.actual_finished_at

        if (started_at is None) != (finished_at is None):
            raise ItemValidationError(
                "actual_started_at and actual_finished_at "
                "must be specified together"
            )

        if started_at is not None and finished_at is not None:
            if self.duration > timedelta(0):
                raise ItemValidationError(
                    "Work interval and duration cannot "
                    "be specified together"
                )

            if finished_at <= started_at:
                raise ItemValidationError(
                    "actual_finished_at must be later than "
                    "actual_started_at"
                )
