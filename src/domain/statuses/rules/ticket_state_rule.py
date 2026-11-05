from dataclasses import dataclass
from typing import Final

from src.domain.statuses.ticket_status import TicketStatus
"""Правила состояний заявки от статуса"""

@dataclass(frozen=True, slots=True)
class TicketStateRule:
    """
    Rules determined by the current Ticket status.

    can_change_data:
        Whether Ticket attributes can be modified.

    has_executor:
        Whether the current workflow state retains
        an active executor assignment.
    """

    can_change_data: bool = False
    has_executor: bool = False


TICKET_STATE_RULES: Final[
    dict[TicketStatus, TicketStateRule]
] = {
    TicketStatus.CREATED: TicketStateRule(
        can_change_data=True,
    ),

    TicketStatus.CREATED_FROM_REQUEST_USER: TicketStateRule(
        can_change_data=True,
    ),

    TicketStatus.CREATED_FROM_TICKET_USER: TicketStateRule(
        can_change_data=True,
    ),

    TicketStatus.REJECTED: TicketStateRule(),

    TicketStatus.ACCEPTED: TicketStateRule(
        can_change_data=True,
    ),

    TicketStatus.DEFERRED: TicketStateRule(
        can_change_data=True,
    ),

    TicketStatus.SUSPENDED: TicketStateRule(),

    TicketStatus.ASSIGNED: TicketStateRule(
        has_executor=True,
    ),

    TicketStatus.AT_WORK: TicketStateRule(
        has_executor=True,
    ),

    TicketStatus.PAUSED: TicketStateRule(
        has_executor=True,
    ),

    TicketStatus.READY_FOR_REVIEW: TicketStateRule(
        has_executor=True,
    ),

    TicketStatus.CONFIRMED_BY_USER: TicketStateRule(),

    TicketStatus.EXECUTED: TicketStateRule(),

    TicketStatus.CANCELLED: TicketStateRule(),

    TicketStatus.CANCELLED_BY_USER: TicketStateRule(),
}


def _validate_ticket_state_rules() -> None:
    missing: list[TicketStatus] = [
        status
        for status in TicketStatus
        if status not in TICKET_STATE_RULES
    ]

    if missing:
        raise RuntimeError(
            "Ticket statuses without state rules: "
            + ", ".join(map(str, missing))
        )
