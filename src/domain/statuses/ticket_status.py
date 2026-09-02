# src/domain/statuses/ticket_status.py

from __future__ import annotations

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

    @property
    def state(self) -> TicketState:
        return _TICKET_STATES[self]


@dataclass(frozen=True, slots=True)
class TicketState:
    """
    Неизменяемое описание одного workflow-состояния Ticket.

    TicketState содержит только свойства состояния:
    - требования к payload status-record;
    - свойства текущего состояния Ticket;
    - допустимые workflow-переходы;
    - допустимость execution/review операций.

    Здесь нет:
    - RBAC;
    - permissions;
    - actor role checks;
    - cross-aggregate rules;
    - реакций на внешние события вроде Client disabled.

    status:
        Стабильный код состояния.

    first_status:
        Состояние может быть первым в status history.

    terminal:
        Состояние завершает Ticket.
        Из terminal-состояния переходов быть не должно.

    requires_executor:
        TicketStatusRecord должен содержать executor_id > 0.

    requires_planned_start:
        TicketStatusRecord должен содержать planned_start_at.

        planned_finish_at при этом остаётся необязательным.

    requires_comment:
        TicketStatusRecord должен содержать непустой comment.

    allows_actual_start:
        В TicketStatusRecord разрешён actual_started_at.

    requires_actual_start:
        actual_started_at не только разрешён,
        но и обязателен.

    allows_actual_finish:
        В TicketStatusRecord разрешён actual_finished_at.

    requires_actual_finish:
        actual_finished_at не только разрешён,
        но и обязателен.

    work_started:
        Работа по Ticket уже была начата.

        Это семантическое свойство состояния,
        а не проверка наличия actual timestamps.

    locks_department_change:
        Department Ticket нельзя менять
        обычной domain-операцией.

    allows_ticket_text_update:
        Текст Ticket разрешено изменять
        в текущем состоянии.

    can_take_to_work:
        ExecutionService может начать новый рабочий интервал.

    can_pause_work:
        ExecutionService может приостановить работу.

    can_resume_work:
        ExecutionService может возобновить работу.

    can_submit_for_review:
        Текущий рабочий интервал можно завершить
        и отправить результат на review.

    can_record_completed_work:
        Можно ретроспективно зарегистрировать
        уже завершённую работу напрямую в review.

    can_review_result:
        Ticket находится в состоянии ожидания
        проверки результата.

    allowed_next:
        Допустимые следующие TicketStatus.

        Это только общий workflow-граф.
        Более узкие правила конкретного use case
        могут дополнительно проверяться domain service.
    """

    status: TicketStatus

    first_status: bool = False
    terminal: bool = False
    work_in_progress: bool = False
    # Status-record payload.
    requires_executor: bool = False
    requires_planned_start: bool = False
    requires_comment: bool = False

    allows_actual_start: bool = False
    requires_actual_start: bool = False

    allows_actual_finish: bool = False
    requires_actual_finish: bool = False

    # Ticket state semantics.
    work_started: bool = False
    locks_department_change: bool = False
    allows_ticket_text_update: bool = False

    # Execution / review capabilities.
    can_take_to_work: bool = False
    can_pause_work: bool = False
    can_resume_work: bool = False
    can_submit_for_review: bool = False
    can_record_completed_work: bool = False
    can_review_result: bool = False

    # Workflow graph.
    allowed_next: frozenset[TicketStatus] = frozenset()

    def allows_transition_to(
        self,
        new_status: TicketStatus,
    ) -> bool:
        return TicketStatus(new_status) in self.allowed_next


_TICKET_STATES: Final[dict[TicketStatus, TicketState]] = {

    # ---------------------------------------------------------
    # Initial states
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Initial decision
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Management
    # ---------------------------------------------------------

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

        can_record_completed_work=True,

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

        can_take_to_work=True,
        can_record_completed_work=True,

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

        can_take_to_work=True,
        can_record_completed_work=True,

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

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    TicketStatus.AT_WORK: TicketState(
        status=TicketStatus.AT_WORK,
        requires_executor=True,

        allows_actual_start=True,
        requires_actual_start=True,

        work_started=True,
        locks_department_change=True,

        can_pause_work=True,
        can_submit_for_review=True,
        work_in_progress=True,

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

        can_resume_work=True,

        allowed_next=frozenset({
            TicketStatus.AT_WORK,
            TicketStatus.DEFERRED,
            TicketStatus.SCHEDULED,
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
            TicketStatus.CANCELLED,
        }),
    ),

    # ---------------------------------------------------------
    # Review
    # ---------------------------------------------------------

    TicketStatus.READY_FOR_REVIEW: TicketState(
        status=TicketStatus.READY_FOR_REVIEW,
        requires_executor=True,


        allows_actual_start=True,

        allows_actual_finish=True,
        requires_actual_finish=True,

        work_started=True,
        locks_department_change=True,

        can_review_result=True,

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

    # ---------------------------------------------------------
    # Terminal states
    # ---------------------------------------------------------

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
    """
    Проверяет внутреннюю согласованность описания workflow.
    """

    # Каждый TicketStatus должен иметь TicketState.
    missing_statuses: list[TicketStatus] = [
        status
        for status in TicketStatus
        if status not in _TICKET_STATES
    ]

    if missing_statuses:
        missing_values: list[str] = [
            str(status.value)
            for status in missing_statuses
        ]
        missing_values.sort()

        raise RuntimeError(
            "Missing TicketState definitions: "
            + ", ".join(missing_values)
        )

    for status, state in _TICKET_STATES.items():

        # Ключ mapping должен соответствовать state.status.
        if status != state.status:
            raise RuntimeError(
                "TicketState key does not match state.status: "
                f"{status.value} != {state.status.value}"
            )

        # Нельзя требовать actual_start, если он запрещён.
        if (
            state.requires_actual_start
            and not state.allows_actual_start
        ):
            raise RuntimeError(
                f"TicketState {status.value}: "
                "requires_actual_start=True requires "
                "allows_actual_start=True"
            )

        # Нельзя требовать actual_finish, если он запрещён.
        if (
            state.requires_actual_finish
            and not state.allows_actual_finish
        ):
            raise RuntimeError(
                f"TicketState {status.value}: "
                "requires_actual_finish=True requires "
                "allows_actual_finish=True"
            )

        # Terminal state не должен иметь исходящих переходов.
        if state.terminal and state.allowed_next:
            raise RuntimeError(
                f"Terminal TicketState {status.value} "
                "cannot have allowed_next statuses"
            )

        # take_to_work всегда означает переход в AT_WORK.
        if (
            state.can_take_to_work
            and TicketStatus.AT_WORK not in state.allowed_next
        ):
            raise RuntimeError(
                f"TicketState {status.value}: "
                "can_take_to_work requires transition "
                "to AT_WORK"
            )

        # pause_work всегда означает переход в PAUSED.
        if (
            state.can_pause_work
            and TicketStatus.PAUSED not in state.allowed_next
        ):
            raise RuntimeError(
                f"TicketState {status.value}: "
                "can_pause_work requires transition "
                "to PAUSED"
            )

        # resume_work всегда означает переход в AT_WORK.
        if (
            state.can_resume_work
            and TicketStatus.AT_WORK not in state.allowed_next
        ):
            raise RuntimeError(
                f"TicketState {status.value}: "
                "can_resume_work requires transition "
                "to AT_WORK"
            )

        # Обычное завершение работы ведёт на review.
        if (
            state.can_submit_for_review
            and TicketStatus.READY_FOR_REVIEW
            not in state.allowed_next
        ):
            raise RuntimeError(
                f"TicketState {status.value}: "
                "can_submit_for_review requires transition "
                "to READY_FOR_REVIEW"
            )

        # Ретроспективная фиксация работы тоже ведёт на review.
        if (
            state.can_record_completed_work
            and TicketStatus.READY_FOR_REVIEW
            not in state.allowed_next
        ):
            raise RuntimeError(
                f"TicketState {status.value}: "
                "can_record_completed_work requires transition "
                "to READY_FOR_REVIEW"
            )

        if state.terminal and (
                state.can_take_to_work
                or state.can_pause_work
                or state.can_resume_work
                or state.can_submit_for_review
                or state.can_record_completed_work
                or state.can_review_result
        ):
            raise RuntimeError(
                f"Terminal TicketState {status.value} "
                "cannot have workflow capabilities"
            )
_validate_ticket_states()





