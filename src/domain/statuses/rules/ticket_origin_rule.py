from dataclasses import dataclass
from typing import Final

from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.rules.ticket_status_transition import FIRST_TICKET_STATUSES

"""правила проихождения заявки"""

@dataclass(frozen=True, slots=True)
class TicketOriginRule:
    """
    Requirements determined by the initial Ticket status.

    These requirements remain valid throughout
    the entire Ticket lifecycle.
    """

    requires_user_id: bool = False
    requires_ticket_user_id: bool = False


TICKET_ORIGIN_RULES: Final[
    dict[TicketStatus, TicketOriginRule]
] = {
    TicketStatus.CREATED: TicketOriginRule(),

    TicketStatus.CREATED_FROM_REQUEST_USER: TicketOriginRule(
        requires_user_id=True,
    ),

    TicketStatus.CREATED_FROM_TICKET_USER: TicketOriginRule(
        requires_user_id=True,
        requires_ticket_user_id=True,
    ),
}


def _validate_ticket_origin_rules() -> None:
    missing: list[TicketStatus] = [
        status
        for status in FIRST_TICKET_STATUSES
        if status not in TICKET_ORIGIN_RULES
    ]

    if missing:
        raise RuntimeError(
            "Initial Ticket statuses without origin rules: "
            + ", ".join(map(str, missing))
        )

_validate_ticket_origin_rules()