# src/domain/statuses/ticket_status.py


from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class TicketStatus(StrEnum):
    CREATED = "created"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    SCHEDULED = "scheduled"
    ASSIGNED = "assigned"
    READY_TO_WORK = "ready_to_work"
    AT_WORK = "at_work"
    PAUSED = "paused"
    READY_FOR_REVIEW = "ready_for_review"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class TicketState:
    """
    Неизменяемое описание одного workflow-состояния.

    status:
        Стабильный код для хранения, DTO и API.

    terminal:
        После такого состояния Ticket больше не изменяется.

    requires_executor:
        В status-record должен быть executor_id > 0.

    requires_planned_start:
        В status-record должен быть planned_start_at.

    work_started:
        Работа над заявкой уже началась или результат уже передан
        на подтверждение.

    locks_department_change:
        Department заявки нельзя менять обычной операцией.

    allowed_next:
        Следующие статусы, допустимые по общему workflow-графу.
        Это не RBAC и не описание того, кто вызывает use case.
    """

    status: TicketStatus

    terminal: bool = False
    requires_executor: bool = False
    requires_planned_start: bool = False
    work_started: bool = False
    locks_department_change: bool = False
    allows_ticket_text_update: bool = False
    allowed_next: frozenset[TicketStatus] = frozenset()

    def allows_transition_to(
        self,
        new_status: TicketStatus,
    ) -> bool:
        return TicketStatus(new_status) in self.allowed_next


CREATED_STATE: Final = TicketState(
    status=TicketStatus.CREATED,
    allows_ticket_text_update = True,
    allowed_next=frozenset({
        TicketStatus.ACCEPTED,
        TicketStatus.REJECTED,

    }),
)

REJECTED_STATE: Final = TicketState(
    status=TicketStatus.REJECTED,
    terminal=True,
)

ACCEPTED_STATE: Final = TicketState(

    status=TicketStatus.ACCEPTED,
    allows_ticket_text_update = True,
    allowed_next=frozenset({
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.CANCELLED,
    }),
)

DEFERRED_STATE: Final = TicketState(
    status=TicketStatus.DEFERRED,
    allowed_next=frozenset({
        TicketStatus.ACCEPTED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.CANCELLED,
    }),
)

SCHEDULED_STATE: Final = TicketState(
    status=TicketStatus.SCHEDULED,
    requires_planned_start=True,
    allowed_next=frozenset({
        TicketStatus.SCHEDULED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.ASSIGNED,
        TicketStatus.ACCEPTED,
        TicketStatus.DEFERRED,
        TicketStatus.CANCELLED,
        TicketStatus.READY_FOR_REVIEW,  #
    }),
)

ASSIGNED_STATE: Final = TicketState(
    status=TicketStatus.ASSIGNED,
    requires_executor=True,
    locks_department_change=True,
    allowed_next=frozenset({
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.SCHEDULED,
        TicketStatus.ACCEPTED,
        TicketStatus.AT_WORK,
        TicketStatus.DEFERRED,
        TicketStatus.CANCELLED,
        TicketStatus.READY_FOR_REVIEW,  #
    }),
)

READY_TO_WORK_STATE: Final = TicketState(
    status=TicketStatus.READY_TO_WORK,
    requires_executor=True,
    requires_planned_start=True,
    locks_department_change=True,
    allowed_next=frozenset({
        TicketStatus.READY_TO_WORK,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.ACCEPTED,
        TicketStatus.AT_WORK,
        TicketStatus.DEFERRED,
        TicketStatus.CANCELLED,
        TicketStatus.READY_FOR_REVIEW,  #
    }),
)

AT_WORK_STATE: Final = TicketState(
    status=TicketStatus.AT_WORK,
    requires_executor=True,
    work_started=True,
    locks_department_change=True,
    allowed_next=frozenset({
        TicketStatus.PAUSED,
        TicketStatus.READY_FOR_REVIEW,
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.CANCELLED,
    }),
)

PAUSED_STATE: Final = TicketState(
    status=TicketStatus.PAUSED,
    requires_executor=True,
    work_started=True,
    locks_department_change=True,
    allowed_next=frozenset({
        TicketStatus.AT_WORK,
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.CANCELLED,
    }),
)


READY_FOR_REVIEW_STATE: Final = TicketState(
    status=TicketStatus.READY_FOR_REVIEW,
    requires_executor=True,
    work_started=True,
    locks_department_change=True,

    allowed_next=frozenset({
        TicketStatus.EXECUTED,
        TicketStatus.AT_WORK,
        TicketStatus.ASSIGNED,
        TicketStatus.SCHEDULED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.DEFERRED,
        TicketStatus.CANCELLED,
    }),
)

EXECUTED_STATE: Final = TicketState(
    status=TicketStatus.EXECUTED,
    terminal=True,
)

CANCELLED_STATE: Final = TicketState(
    status=TicketStatus.CANCELLED,
    terminal=True,
)


_TICKET_STATES: Final[dict[TicketStatus, TicketState]] = {
    state.status: state
    for state in (
        CREATED_STATE,
        REJECTED_STATE,
        ACCEPTED_STATE,
        DEFERRED_STATE,
        SCHEDULED_STATE,
        ASSIGNED_STATE,
        READY_TO_WORK_STATE,
        AT_WORK_STATE,
        PAUSED_STATE,
        READY_FOR_REVIEW_STATE,
        EXECUTED_STATE,
        CANCELLED_STATE,
    )
}


def get_ticket_state(
    status: TicketStatus,
) -> TicketState:
    return _TICKET_STATES[TicketStatus(status)]


def is_ticket_status_transition_allowed(
    *,
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> bool:
    return get_ticket_state(current_status).allows_transition_to(
        new_status,
    )


def is_terminal_ticket_status(
    status: TicketStatus,
) -> bool:
    return get_ticket_state(status).terminal


def is_department_change_locked(
    status: TicketStatus,
) -> bool:
    state = get_ticket_state(status)

    return state.terminal or state.locks_department_change