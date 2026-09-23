from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import StrEnum
from typing import Self, Final

from src.domain.exceptions import ItemValidationError
from src.domain.ticket_components import Comment
from src.domain.value_objects import Empty


class TicketUserStatus(StrEnum):
    CREATED = "created"
    CONFIRMED_BY_ADMIN = "confirmed_by_admin"
    IN_WORK = "in_work"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"

    DEFERRED = "deferred"

    EXECUTION_CONFIRMED_BY_USER = "execution_confirmed_by_user"
    EXECUTION_CONFIRMED_BY_ADMIN = "execution_confirmed_by_admin"

    CANCELLED_BY_USER = "cancelled_by_user"
    CANCELLED_BY_ADMIN = "cancelled_by_admin"

    @classmethod
    def can_transition(
        cls,
        from_status: Self,
        to_status: Self,
    ) -> bool:
        return (
            cls(to_status)
            in TICKET_USER_TRANSITIONS[cls(from_status)]
        )

    @classmethod
    def is_terminal(
        cls,
        status: Self,
    ) -> bool:
        return cls(status) in TERMINAL_TICKET_USER_STATUSES

    @classmethod
    def is_first_status(
        cls,
        status: Self,
    ) -> bool:
        return cls(status) in FIRST_TICKET_USER_STATUSES


FIRST_TICKET_USER_STATUSES: Final[
    frozenset[TicketUserStatus]
] = frozenset({
    TicketUserStatus.CREATED,
})
TERMINAL_TICKET_USER_STATUSES: Final[
    frozenset[TicketUserStatus]
] = frozenset({
    TicketUserStatus.EXECUTION_CONFIRMED_BY_USER,
    TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN,
    TicketUserStatus.CANCELLED_BY_USER,
    TicketUserStatus.CANCELLED_BY_ADMIN,
})
TICKET_USER_TRANSITIONS: Final[
    dict[TicketUserStatus, frozenset[TicketUserStatus]]
] = {
    TicketUserStatus.CREATED: frozenset({
        TicketUserStatus.CONFIRMED_BY_ADMIN,
        TicketUserStatus.CANCELLED_BY_USER,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.CONFIRMED_BY_ADMIN: frozenset({
        TicketUserStatus.IN_WORK,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.IN_WORK: frozenset({
        TicketUserStatus.CONFIRMED_BY_ADMIN,
        TicketUserStatus.WAITING_FOR_CONFIRMATION,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.WAITING_FOR_CONFIRMATION: frozenset({
        TicketUserStatus.CONFIRMED_BY_ADMIN,
        TicketUserStatus.IN_WORK,
        TicketUserStatus.EXECUTION_CONFIRMED_BY_USER,
        TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.EXECUTION_CONFIRMED_BY_USER: frozenset(),
    TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN: frozenset(),
    TicketUserStatus.CANCELLED_BY_USER: frozenset(),
    TicketUserStatus.CANCELLED_BY_ADMIN: frozenset(),
}


def _validate_ticket_user_transitions() -> None:
    missing_statuses: list[TicketUserStatus] = [
        status
        for status in TicketUserStatus
        if status not in TICKET_USER_TRANSITIONS
    ]

    if missing_statuses:
        missing_values = [
            status.value
            for status in missing_statuses
        ]
        missing_values.sort()

        raise RuntimeError(
            "Missing TicketUser transition definitions: "
            + ", ".join(str(missing_values))
        )

    for status in TERMINAL_TICKET_USER_STATUSES:
        if TICKET_USER_TRANSITIONS[status]:
            raise RuntimeError(
                f"Terminal TicketUser status "
                f"{status.value} cannot have transitions"
            )


@dataclass(kw_only=True)
class StatusRecordTicketUser:
    """
    Факт изменения workflow-состояния TicketUser.

    actor_employee_id:
        - для пользовательского действия: User.employee_id;
        - для административного действия: Admin.employee_id.

    В TicketUser actor_employee_id всегда > 0.
    """

    status_id: int = 0

    actor_employee_id: int
    status: TicketUserStatus

    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    #comment: str = ""
    status_comment:Comment|Empty=field(default_factory=Empty)

    def __post_init__(self) -> None:
        self.status = TicketUserStatus(self.status)



        self.date_created = self._normalize_datetime(
            value=self.date_created,
            field_name="date_created",
        )


        self._validate_identity()
        self._validate_record_time()

    # ----------------------------
    # Queries
    # ----------------------------

    def is_new(self) -> bool:
        return self.status_id == 0

    def is_terminal(self) -> bool:
        return TicketUserStatus.is_terminal(
            self.status
        )

    def is_first_status(self) -> bool:
        return TicketUserStatus.is_first_status(
            self.status
        )

    def can_move_to_next_record(
        self,
        record: Self,
    ) -> bool:
        return TicketUserStatus.can_transition(
            self.status,
            record.status,
        )

    # ----------------------------
    # Validation
    # ----------------------------

    def _validate_identity(self) -> None:
        if self.status_id < 0:
            raise ItemValidationError(
                "TicketUser status record ID cannot be negative"
            )

        if self.actor_employee_id <= 0:
            raise ItemValidationError(
                "TicketUser status actor employee ID "
                "must be positive"
            )

    def _validate_record_time(self) -> None:
        if self.date_created > datetime.now(UTC):
            raise ItemValidationError(
                "TicketUser status record date_created "
                "cannot be in the future"
            )

    # ----------------------------
    # Normalization
    # ----------------------------


    @staticmethod
    def _normalize_datetime(
        *,
        value: datetime,
        field_name: str,
    ) -> datetime:
        if not isinstance(value, datetime):
            raise ItemValidationError(
                f"{field_name} must be datetime"
            )

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)
