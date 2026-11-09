from dataclasses import dataclass
from typing import Final

from src.domain.statuses.ticket_status import TicketStatus

"""Правила описания статуса"""

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

    requires_user_id Должен быть установлен пользователь от которог заявка



    """
    requires_comment: bool = False  # internal state
    requires_executor: bool = False  # internal state
    allows_work_data: bool = False  # internal state
    requires_work_mode: bool = False   # internal state елси установлен, то работа делаласб удаленно, если нет, то на месте. Если None то все равно
    user_action: bool = False # internal статус устанваливается пользователем или админом
    can_change_data: bool = False
    has_executor:bool=False
    requires_user_id:bool=False
    requires_ticket_user_id:bool=False


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
