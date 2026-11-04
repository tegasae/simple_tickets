from typing import Final

from src.domain.statuses.rules.rules import TicketStateRule, TicketStatusRule, TicketOriginRule

from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_transitions import FIRST_TICKET_STATUSES

TICKET_STATUS_RULES: Final[dict[TicketStatus, TicketStatusRule]] = {
    TicketStatus.CREATED: TicketStatusRule(can_change_data=True),

    TicketStatus.CREATED_FROM_TICKET_USER: TicketStatusRule(
        user_action=True,
        can_change_data=True,
        requires_user_id=True,
        requires_ticket_user_id=True
    ),

    TicketStatus.CREATED_FROM_REQUEST_USER: TicketStatusRule(
        can_change_data=True,
        requires_user_id=True
    ),

    TicketStatus.REJECTED: TicketStatusRule(
        requires_comment=True,
    ),

    TicketStatus.ACCEPTED: TicketStatusRule(can_change_data=True),

    TicketStatus.DEFERRED: TicketStatusRule(
        requires_comment=True,
        can_change_data=True
    ),

    TicketStatus.SUSPENDED: TicketStatusRule(),

    TicketStatus.ASSIGNED: TicketStatusRule(
        requires_executor=True,
        has_executor=True
    ),

    TicketStatus.AT_WORK: TicketStatusRule(
        allows_work_data=True,
        requires_work_mode=True,
        has_executor=True

    ),

    TicketStatus.PAUSED: TicketStatusRule(has_executor=True),

    TicketStatus.READY_FOR_REVIEW: TicketStatusRule(has_executor=True),

    TicketStatus.CONFIRMED_BY_USER: TicketStatusRule(
        user_action=True,
    ),

    TicketStatus.EXECUTED: TicketStatusRule(),

    TicketStatus.CANCELLED: TicketStatusRule(
        requires_comment=True,
    ),

    TicketStatus.CANCELLED_BY_USER: TicketStatusRule(
        user_action=True,
    ),
}


def _validate_ticket_status_rules() -> None:
    missing: list[TicketStatus] = [
        status
        for status in TicketStatus
        if status not in TICKET_STATUS_RULES
    ]

    if missing:
        raise RuntimeError(
            "Ticket statuses without rules: "
            + ", ".join(map(str, missing))
        )
_validate_ticket_status_rules()

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


_validate_ticket_state_rules()