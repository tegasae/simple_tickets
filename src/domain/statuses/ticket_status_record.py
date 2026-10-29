
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime, timedelta
from typing import get_type_hints

from src.domain.datetime_check import validate_utc_datetime
from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus, TicketStatusRule, TICKET_STATUS_RULES
from src.domain.value_objects import CommonComment, Empty


@dataclass(slots=True, kw_only=True)
class TicketStatusRecord:
    """
    Historical record of a Ticket workflow status.

    Responsibilities
    ================

    TicketStatusRecord validates only its own data integrity:

    - field types according to dataclass annotations;
    - non-negative identifiers;
    - valid work-time representation;
    - UTC datetime values.

    Business rules associated with a particular TicketStatus
    belong to the Ticket aggregate.

    In particular, Ticket validates:

    - actor requirements;
    - required comments;
    - executor requirements;
    - allowed work data;
    - required work mode;
    - workflow transitions;
    - current executor restrictions.

    Identity
    ========

    status_id == 0:
        New record, not persisted yet.

    status_id > 0:
        Persisted record.

    actor_employee_id == 0:
        Allowed at record level. Ticket determines whether the
        status represents a User action.

    executor_id == 0:
        Allowed at record level. Ticket determines whether the
        status requires an executor.

    Negative identifiers are invalid.

    Work time
    =========

    Three representations are supported:

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

    Exact interval and explicit duration are mutually exclusive.

    Work mode
    =========

    work_is_remote:

        True  - remote work
        False - on-site work
        None  - not specified

    Whether work mode is required belongs to Ticket.

    Date/time
    =========

    All datetime values must explicitly use datetime.UTC.

    Naive datetime values and other timezones are rejected.
    No automatic timezone conversion is performed.
    """

    status: TicketStatus
    actor_employee_id: int =field(metadata={"min": 0})

    status_id: int = field(default=0, metadata={"min": 0})
    executor_id: int = field(default=0, metadata={"min": 0})

    comment: CommonComment | Empty = field(default_factory=Empty)

    actual_started_at: datetime | None = None
    actual_finished_at: datetime | None = None

    duration: timedelta = field(
        default_factory=timedelta,
    )

    work_is_remote: bool | None = None

    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    def __post_init__(self) -> None:
        self._validate_types()
        self._validate_ranges()
        self._validate_datetimes()
        self._validate_work_data()


    def is_new(self) -> bool:
        return self.status_id == 0


    @property
    def rule(self)->TicketStatusRule:
        return TICKET_STATUS_RULES[self.status]


    # ==============================================================
    # Types
    # ==============================================================

    def _validate_types(self) -> None:
        """
        Validate all dataclass fields against their type annotations.

        get_type_hints resolves postponed annotations and unions.

        int is checked strictly because bool is a subclass of int.
        """

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
    # Identity
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
        """
        Require UTC for all present datetime values.
        """

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
    # Work data
    # ==============================================================

    def _validate_work_data(self) -> None:
        """
        Validate work-time consistency.

        - duration cannot be negative;
        - started and finished timestamps must appear together;
        - exact interval and explicit duration are mutually exclusive;
        - finished timestamp must be later than started timestamp.

        Whether work data is allowed for a particular status
        belongs to Ticket.
        """

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
