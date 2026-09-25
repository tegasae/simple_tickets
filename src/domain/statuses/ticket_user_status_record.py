from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.exceptions import ItemValidationError

from src.domain.statuses.ticket_user_status import (
    TICKET_USER_STATUS_RULES,
    TicketUserStatus, TicketUserStatusRule,
)
from src.domain.value_objects import CommonComment, Empty


@dataclass(frozen=True, slots=True, kw_only=True)
class TicketUserStatusRecord:
    """
    Historical record of a TicketUser status.

    The record represents one concrete status change in TicketUser
    history and validates only its own payload.

    Allowed transitions between TicketUser statuses are defined
    separately by TICKET_USER_TRANSITIONS.

    Attributes
    ----------
    status:
        TicketUser status represented by this record.

    actor_employee_id:
        Identifier of the employee who performed the action.

        The actor may be either a User or an Admin depending on the
        intrinsic rules of the status.

        The identifier must always be positive.

        Whether the concrete Admin identifier is exposed to the User
        is a presentation/API concern. The domain history always keeps
        the real actor identifier.

    status_id:
        Persistent identifier of the status record.

        Zero means that the record has not been persisted yet.
        Negative values are not allowed.

    comment:
        Optional comment associated with the status.

        Some statuses require a non-empty comment according to
        TICKET_USER_STATUS_RULES.

    date_created:
        Time when this status record was created.

        The value must be timezone-aware.
    """

    status: TicketUserStatus
    actor_employee_id: int

    status_id: int = 0

    comment: CommonComment | Empty = field(
        default_factory=Empty,
    )

    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    def __post_init__(self) -> None:
        self._validate_identity()
        self._validate_actor()
        self._validate_comment()

    @property
    def rule(self) -> TicketUserStatusRule:
        """
        Return intrinsic rules for the current TicketUser status.
        """
        return TICKET_USER_STATUS_RULES[self.status]

    def _validate_identity(self) -> None:
        if self.status_id < 0:
            raise ItemValidationError(
                "Status record ID cannot be negative"
            )

        if not isinstance(self.status, TicketUserStatus):
            raise ItemValidationError(
                "Invalid TicketUser status"
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
        if (
            self.rule.requires_comment
            and isinstance(self.comment, Empty)
        ):
            raise ItemValidationError(
                f"{self.status} requires a comment"
            )