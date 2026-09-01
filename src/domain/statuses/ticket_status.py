# src/domain/statuses/ticket_status.py

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class TicketStatus(StrEnum):
    CREATED = "created"
    CREATED_FROM_TICKET_USER = "created_from_ticket_user"

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
    CANCELLED_BY_USER = "cancelled_by_user"


@dataclass(frozen=True, slots=True)
class TicketState:
    """
    Неизменяемое описание одного workflow-состояния Ticket.

    status:
        Стабильный код состояния для хранения, DTO и API.

    first_status:
        Состояние может быть первым в истории Ticket.

    terminal:
        После такого состояния Ticket больше не изменяется.

    requires_executor:
        В status-record должен быть executor_id > 0.

    requires_planned_start:
        В status-record должен быть planned_start_at.

    allows_actual_start:
        В status-record разрешён actual_started_at.

    requires_actual_start:
        В status-record обязателен actual_started_at.

    allows_actual_finish:
        В status-record разрешён actual_finished_at.

    requires_actual_finish:
        В status-record обязателен actual_finished_at.

    work_started:
        Работа над заявкой уже началась либо её результат
        уже передан на review.

    locks_department_change:
        Department заявки нельзя менять обычной операцией.

    allows_ticket_text_update:
        Текст заявки можно менять обычной операцией.

    requires_comment:
        В status-record обязателен непустой comment.

    allowed_next:
        Допустимые следующие состояния workflow.

        Это не RBAC и не описание того, кто имеет право
        выполнить переход.
    """

    status: TicketStatus

    first_status: bool = False
    terminal: bool = False

    requires_executor: bool = False
    requires_planned_start: bool = False
    requires_comment: bool = False

    allows_actual_start: bool = False
    requires_actual_start: bool = False

    allows_actual_finish: bool = False
    requires_actual_finish: bool = False

    work_started: bool = False

    locks_department_change: bool = False
    allows_ticket_text_update: bool = False

    allowed_next: frozenset[TicketStatus] = frozenset()

    def allows_transition_to(
        self,
        new_status: TicketStatus,
    ) -> bool:
        return TicketStatus(new_status) in self.allowed_next


_TICKET_STATES: Final[dict[TicketStatus, TicketState]] = {
    TicketStatus.CREATED: TicketState(
        status=TicketStatus.CREATED,
        first_status=True,
        allows_ticket_text_update=True,
        allowed_next=frozenset({
            TicketStatus.ACCEPTED,
            TicketStatus.REJECTED,
        }),
    ),

    TicketStatus.CREATED_FROM_TICKET_USER: TicketState(
        status=TicketStatus.CREATED_FROM_TICKET_USER,
        first_status=True,
        allowed_next=frozenset({
            TicketStatus.ACCEPTED,
            TicketStatus.REJECTED,
            TicketStatus.CANCELLED_BY_USER,
        }),
    ),

    TicketStatus.REJECTED: TicketState(
        status=TicketStatus.REJECTED,
        terminal=True,
        requires_comment=True,
    ),

    TicketStatus.ACCEPTED: TicketState(
        status=TicketStatus.ACCEPTED,
        allows_ticket_text_update=True,
        allowed_next=frozenset({
            TicketStatus.DEFERRED,
            TicketStatus.SCHEDULED,
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
            TicketStatus.CANCELLED,
        }),
    ),

    TicketStatus.DEFERRED: TicketState(
        status=TicketStatus.DEFERRED,
        requires_comment=True,
        allowed_next=frozenset({
            TicketStatus.ACCEPTED,
            TicketStatus.SCHEDULED,
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
            TicketStatus.CANCELLED,
        }),
    ),

    TicketStatus.SCHEDULED: TicketState(
        status=TicketStatus.SCHEDULED,
        requires_planned_start=True,
        allowed_next=frozenset({
            TicketStatus.SCHEDULED,
            TicketStatus.READY_TO_WORK,
            TicketStatus.ASSIGNED,
            TicketStatus.ACCEPTED,
            TicketStatus.DEFERRED,
            TicketStatus.CANCELLED,
            TicketStatus.READY_FOR_REVIEW,
        }),
    ),

    TicketStatus.ASSIGNED: TicketState(
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
            TicketStatus.READY_FOR_REVIEW,
        }),
    ),

    TicketStatus.READY_TO_WORK: TicketState(
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
            TicketStatus.READY_FOR_REVIEW,
        }),
    ),

    TicketStatus.AT_WORK: TicketState(
        status=TicketStatus.AT_WORK,
        requires_executor=True,

        allows_actual_start=True,
        requires_actual_start=True,

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
    ),

    TicketStatus.PAUSED: TicketState(
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
    ),

    TicketStatus.READY_FOR_REVIEW: TicketState(
        status=TicketStatus.READY_FOR_REVIEW,
        requires_executor=True,

        allows_actual_start=True,

        allows_actual_finish=True,
        requires_actual_finish=True,

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
    ),

    TicketStatus.EXECUTED: TicketState(
        status=TicketStatus.EXECUTED,
        terminal=True,
    ),

    TicketStatus.CANCELLED: TicketState(
        status=TicketStatus.CANCELLED,
        terminal=True,
        requires_comment=True,
    ),

    TicketStatus.CANCELLED_BY_USER: TicketState(
        status=TicketStatus.CANCELLED_BY_USER,
        terminal=True,
    ),
}


def _validate_ticket_states() -> None:
    missing_statuses = set(TicketStatus) - set(_TICKET_STATES)

    if missing_statuses:
        missing = ", ".join(
            sorted(str(status) for status in missing_statuses)
        )
        raise RuntimeError(
            f"Missing TicketState definitions: {missing}"
        )

    for status, state in _TICKET_STATES.items():
        if status != state.status:
            raise RuntimeError(
                "TicketState key does not match state.status: "
                f"{status.value} != {state.status.value}"
            )

        if (
            state.requires_actual_start
            and not state.allows_actual_start
        ):
            raise RuntimeError(
                f"TicketState {status.value}: "
                "requires_actual_start requires allows_actual_start"
            )

        if (
            state.requires_actual_finish
            and not state.allows_actual_finish
        ):
            raise RuntimeError(
                f"TicketState {status.value}: "
                "requires_actual_finish requires allows_actual_finish"
            )


_validate_ticket_states()


def get_ticket_state(
    status: TicketStatus,
) -> TicketState:
    return _TICKET_STATES[TicketStatus(status)]


def is_ticket_status_transition_allowed(
    *,
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> bool:
    return get_ticket_state(
        current_status
    ).allows_transition_to(
        new_status
    )


def is_terminal_ticket_status(
    status: TicketStatus,
) -> bool:
    return get_ticket_state(status).terminal


def is_department_change_locked(
    status: TicketStatus,
) -> bool:
    state = get_ticket_state(status)

    return (
        state.terminal
        or state.locks_department_change
    )


def is_text_change_allowed(
    status: TicketStatus,
) -> bool:
    return get_ticket_state(
        status
    ).allows_ticket_text_update