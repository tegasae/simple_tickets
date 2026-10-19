from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class TicketUserStatus(StrEnum):
    CREATED = "created"

    IN_WORK = "in_work"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"

    CONFIRMED_BY_USER = "confirmed_by_user"
    CONFIRMED_BY_ADMIN = "confirmed_by_admin"

    SUSPENDED = "suspended"

    CANCELLED_BY_USER = "cancelled_by_user"
    CANCELLED_BY_ADMIN = "cancelled_by_admin"


@dataclass(frozen=True, slots=True)
class TicketUserStatusRule:
    """
    Intrinsic rules of a TicketUser status.

    These rules describe only the status itself.
    They do not define allowed transitions between statuses.

    By default, a status represents an action performed by an Admin.
    Statuses explicitly marked with ``user_action=True`` represent
    actions performed by a User.

    Attributes
    ----------
    user_action:
        ``True`` if the status is produced by a User action.

        ``False`` means that the status is produced by an Admin action.

    requires_comment:
        ``True`` if the status record must contain a non-empty comment.
    """

    user_action: bool = False
    requires_comment: bool = False


TICKET_USER_STATUS_RULES: Final[
    dict[TicketUserStatus, TicketUserStatusRule]
] = {
    TicketUserStatus.CREATED: TicketUserStatusRule(
        user_action=True,
    ),

    TicketUserStatus.IN_WORK: TicketUserStatusRule(),

    TicketUserStatus.WAITING_FOR_CONFIRMATION: TicketUserStatusRule(),

    TicketUserStatus.CONFIRMED_BY_USER: TicketUserStatusRule(
        user_action=True,
    ),

    TicketUserStatus.CONFIRMED_BY_ADMIN: TicketUserStatusRule(),

    TicketUserStatus.SUSPENDED: TicketUserStatusRule(),

    TicketUserStatus.CANCELLED_BY_USER: TicketUserStatusRule(
        user_action=True,
    ),

    TicketUserStatus.CANCELLED_BY_ADMIN: TicketUserStatusRule(
        requires_comment=True,
    ),
}


def _validate_ticket_user_status_rules() -> None:
    """
    Validate that every TicketUserStatus has a corresponding rule.
    """

    missing: list[TicketUserStatus] = [
        status
        for status in TicketUserStatus
        if status not in TICKET_USER_STATUS_RULES
    ]

    if missing:
        raise RuntimeError(
            "TicketUser statuses without rules: "
            + ", ".join(map(str, missing))
        )


_validate_ticket_user_status_rules()