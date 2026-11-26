
"""
Intrinsic rules of Ticket statuses.

These rules describe requirements for TicketStatusRecord.
They do not define workflow transitions or aggregate-level rules.
"""

from dataclasses import dataclass
from typing import Final

from src.domain.statuses.ticket_status import TicketStatus


@dataclass(frozen=True, slots=True)
class TicketStatusRule:
    """
    Intrinsic rules of a Ticket status.

    Attributes
    ----------
    requires_comment:
        Whether a valid non-empty comment is required.

    requires_executor:
        Whether executor_id must be positive.

    tracks_work_time:
        Whether this status represents a period of actual work.

        If True, the record contributes to Ticket working time.

        Work time is determined by exactly one of:

        - an explicit positive duration;
        - an explicit start/finish interval;
        - the workflow interval when no explicit time is provided.

        If False, explicit work-time data is forbidden
        and the record does not contribute to working time.

    requires_work_mode:
        True:
            work_is_remote must be True or False.

        False:
            work_is_remote must be None.

    user_action:
        True:
            The action is performed by a User.
            actor_employee_id must be 0.

        False:
            The action is performed by an Admin.
            actor_employee_id must be positive.
    """

    requires_comment: bool = False
    requires_executor: bool = False
    tracks_work_time: bool = False
    requires_work_mode: bool = False
    user_action: bool = False


TICKET_STATUS_RULES: Final[
    dict[TicketStatus, TicketStatusRule]
] = {
    TicketStatus.CREATED: TicketStatusRule(),

    TicketStatus.CREATED_FROM_TICKET_USER: TicketStatusRule(
        user_action=True,
    ),

    TicketStatus.CREATED_FROM_REQUEST_USER: TicketStatusRule(),

    TicketStatus.REJECTED: TicketStatusRule(
        requires_comment=True,
    ),

    TicketStatus.ACCEPTED: TicketStatusRule(),

    TicketStatus.DEFERRED: TicketStatusRule(
        requires_comment=True,
    ),

    TicketStatus.SUSPENDED: TicketStatusRule(),

    TicketStatus.ASSIGNED: TicketStatusRule(
        requires_executor=True,
    ),

    TicketStatus.AT_WORK: TicketStatusRule(
        tracks_work_time=True,
        requires_work_mode=True,
    ),

    TicketStatus.PAUSED: TicketStatusRule(),

    TicketStatus.READY_FOR_REVIEW: TicketStatusRule(),

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
