"""
Ticket statuses and their intrinsic rules.

This module describes:

- the set of statuses available for Ticket;
- which statuses represent actions performed by a User rather than an Admin;
- which statuses require a comment;
- which statuses require an executor;
- which statuses may contain actual work-time data.

Workflow transitions are intentionally not defined here.
They belong to a separate part of the domain model.

By default, a status is considered to be produced by an Admin action.
Only statuses explicitly marked with ``user_action=True`` are produced
by a User action.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class TicketStatus(StrEnum):
    """
    Status of a Ticket.

    The status represents the business state recorded in the Ticket history.

    Notes
    -----
    CREATED
        Ticket was created directly by an Admin.

    CREATED_FROM_TICKET_USER
        Ticket was created from a TicketUser request.
        The action is attributed to the User.

    REJECTED
        Ticket was rejected by an Admin.
        A comment explaining the reason is required.

    ACCEPTED
        Ticket was accepted by an Admin.

    DEFERRED
        Ticket was deliberately deferred by an Admin.
        A comment explaining the reason is required.

    SUSPENDED
        Ticket was suspended because the related Client or User was disabled.

        This status is semantically different from DEFERRED.
        DEFERRED represents a normal business decision to postpone work,
        while SUSPENDED represents suspension caused by availability of the
        related Client/User.

    ASSIGNED
        An executor was assigned to the Ticket.
        ``executor_id`` is required for the corresponding status record.

    AT_WORK
        Work on the Ticket is being performed or actual work is being
        registered retrospectively.

        The corresponding status record may contain:

        - actual_started_at;
        - actual_finished_at;
        - duration.

        Exact validation rules for these fields belong to the status-record
        payload validation.

    PAUSED
        Work on the Ticket was paused.

    READY_FOR_REVIEW
        Work was completed by the executor and submitted for review.

    CONFIRMED_BY_USER
        User confirmed the result of the work.

        This is not a terminal status. Final completion of the Ticket is
        performed by an Admin with the required permission.

    EXECUTED
        Ticket was finally completed by an authorized Admin.

    CANCELLED
        Ticket was cancelled by an Admin.
        A comment explaining the reason is required.

    CANCELLED_BY_USER
        Ticket was cancelled by the User.
    """

    CREATED = "created"
    CREATED_FROM_TICKET_USER = "created_from_ticket_user"

    REJECTED = "rejected"
    ACCEPTED = "accepted"

    DEFERRED = "deferred"
    SUSPENDED = "suspended"

    ASSIGNED = "assigned"
    AT_WORK = "at_work"
    PAUSED = "paused"

    READY_FOR_REVIEW = "ready_for_review"

    CONFIRMED_BY_USER = "confirmed_by_user"
    EXECUTED = "executed"

    CANCELLED = "cancelled"
    CANCELLED_BY_USER = "cancelled_by_user"


@dataclass(frozen=True, slots=True)
class TicketStatusRule:
    """
    Intrinsic rules of a Ticket status.

    These rules describe the payload and origin of a status itself.
    They do not describe allowed transitions between statuses.

    Attributes
    ----------
    user_action:
        ``True`` if the status represents an action performed by a User.

        ``False`` means that the action is performed by an Admin.

        Admin is intentionally the default because most Ticket workflow
        actions are administrative actions.

    requires_comment:
        ``True`` if the status record must contain a non-empty comment.

    requires_executor:
        ``True`` if the status record must contain a valid ``executor_id``.

    allows_work_data:
        ``True`` if the status record may contain actual work information:

        - ``actual_started_at``;
        - ``actual_finished_at``;
        - ``duration``.

        This flag only declares that such data is allowed for the status.
        Validation of valid combinations of these fields belongs to the
        status-record payload validation.

     requires_work_mode True if kind of work has to set
    """

    user_action: bool = False
    requires_comment: bool = False
    requires_executor: bool = False
    allows_work_data: bool = False
    requires_work_mode:bool = False

TICKET_STATUS_RULES: Final[dict[TicketStatus, TicketStatusRule]] = {
    TicketStatus.CREATED: TicketStatusRule(),

    TicketStatus.CREATED_FROM_TICKET_USER: TicketStatusRule(
        user_action=True,
    ),

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
        allows_work_data=True,
        requires_work_mode=True
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