# tests/domain/policy/test_ticket_workflow_actor_policy.py

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.policy.ticket_workflow_actor_policy import (
    TicketWorkflowActorKind,
    TicketWorkflowActorPolicy,
)
from src.domain.statuses.ticket_status import TicketStatus, ALLOWED_TICKET_STATUS_TRANSITIONS


def assert_allowed(
    actor_kind: TicketWorkflowActorKind,
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    TicketWorkflowActorPolicy.ensure_actor_can_change_status(
        actor_kind=actor_kind,
        current_status=current_status,
        new_status=new_status,
    )

    assert TicketWorkflowActorPolicy.can_actor_change_status(
        actor_kind=actor_kind,
        current_status=current_status,
        new_status=new_status,
    )


def assert_forbidden(
    actor_kind: TicketWorkflowActorKind,
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    with pytest.raises(DomainOperationError):
        TicketWorkflowActorPolicy.ensure_actor_can_change_status(
            actor_kind=actor_kind,
            current_status=current_status,
            new_status=new_status,
        )

    assert not TicketWorkflowActorPolicy.can_actor_change_status(
        actor_kind=actor_kind,
        current_status=current_status,
        new_status=new_status,
    )


def test_all_actor_transitions_are_subset_of_common_workflow_graph() -> None:
    """
    Actor-specific transitions не должны расширять общий workflow-граф.

    Если сюда случайно попадёт, например:

        CREATED -> CANCELLED

    тест должен упасть, потому что общего такого перехода нет.
    """

    for actor_kind, transitions in (
        TicketWorkflowActorPolicy._TRANSITIONS_BY_ACTOR_KIND.items()
    ):
        for current_status, new_status in transitions:
            allowed_common_statuses = ALLOWED_TICKET_STATUS_TRANSITIONS.get(
                current_status,
                frozenset(),
            )

            assert new_status in allowed_common_statuses, (
                f"{actor_kind.value} transition "
                f"{current_status.value} -> {new_status.value} "
                f"is not present in common workflow graph"
            )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        # Исполнитель начал работу без плановой даты.
        (TicketStatus.ASSIGNED, TicketStatus.AT_WORK),

        # Исполнитель начал работу по запланированной заявке.
        (TicketStatus.READY_TO_WORK, TicketStatus.AT_WORK),

        # Исполнитель внёс выполненную offline-работу задним числом.
        (TicketStatus.ASSIGNED, TicketStatus.OFFLINE_WORK),
        (TicketStatus.READY_TO_WORK, TicketStatus.OFFLINE_WORK),

        # Исполнитель временно приостановил работу.
        (TicketStatus.AT_WORK, TicketStatus.PAUSED),

        # Исполнитель вернулся к работе после паузы.
        (TicketStatus.PAUSED, TicketStatus.AT_WORK),

        # Исполнитель завершил свой этап работы.
        (TicketStatus.AT_WORK, TicketStatus.READY_FOR_REVIEW),

        # Offline-work передан на проверку.
        (TicketStatus.OFFLINE_WORK, TicketStatus.READY_FOR_REVIEW),
    ],
)
def test_executor_can_make_executor_transitions(
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    assert_allowed(
        TicketWorkflowActorKind.EXECUTOR,
        current_status,
        new_status,
    )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        # В SCHEDULED нет исполнителя, поэтому исполнитель не может начать работу.
        (TicketStatus.SCHEDULED, TicketStatus.AT_WORK),

        # Исполнитель не принимает заявку.
        (TicketStatus.CREATED, TicketStatus.ACCEPTED),

        # Исполнитель не отменяет заявку.
        (TicketStatus.AT_WORK, TicketStatus.CANCELLED),

        # Исполнитель не планирует заявку.
        (TicketStatus.ACCEPTED, TicketStatus.SCHEDULED),

        # Исполнитель не подтверждает выполнение.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.EXECUTED),
    ],
)
def test_executor_cannot_make_non_executor_transitions(
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    assert_forbidden(
        TicketWorkflowActorKind.EXECUTOR,
        current_status,
        new_status,
    )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        # Первичная обработка.
        (TicketStatus.CREATED, TicketStatus.ACCEPTED),
        (TicketStatus.CREATED, TicketStatus.REJECTED),

        # Принятая заявка.
        (TicketStatus.ACCEPTED, TicketStatus.SCHEDULED),
        (TicketStatus.ACCEPTED, TicketStatus.ASSIGNED),
        (TicketStatus.ACCEPTED, TicketStatus.READY_TO_WORK),
        (TicketStatus.ACCEPTED, TicketStatus.DEFERRED),
        (TicketStatus.ACCEPTED, TicketStatus.CANCELLED),

        # Планирование.
        (TicketStatus.SCHEDULED, TicketStatus.SCHEDULED),
        (TicketStatus.SCHEDULED, TicketStatus.READY_TO_WORK),
        (TicketStatus.SCHEDULED, TicketStatus.ASSIGNED),
        (TicketStatus.SCHEDULED, TicketStatus.ACCEPTED),

        # Назначение.
        (TicketStatus.ASSIGNED, TicketStatus.ASSIGNED),
        (TicketStatus.ASSIGNED, TicketStatus.READY_TO_WORK),
        (TicketStatus.ASSIGNED, TicketStatus.SCHEDULED),
        (TicketStatus.ASSIGNED, TicketStatus.AT_WORK),

        # Готова к работе.
        (TicketStatus.READY_TO_WORK, TicketStatus.READY_TO_WORK),
        (TicketStatus.READY_TO_WORK, TicketStatus.SCHEDULED),
        (TicketStatus.READY_TO_WORK, TicketStatus.ASSIGNED),
        (TicketStatus.READY_TO_WORK, TicketStatus.AT_WORK),

        # Управленческие переходы из работы.
        (TicketStatus.AT_WORK, TicketStatus.PAUSED),
        (TicketStatus.AT_WORK, TicketStatus.DEFERRED),
        (TicketStatus.AT_WORK, TicketStatus.ASSIGNED),
        (TicketStatus.AT_WORK, TicketStatus.SCHEDULED),
        (TicketStatus.AT_WORK, TicketStatus.READY_TO_WORK),
        (TicketStatus.AT_WORK, TicketStatus.CANCELLED),

        # Проверка результата.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.EXECUTED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.AT_WORK),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.ASSIGNED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.SCHEDULED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.READY_TO_WORK),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.DEFERRED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.CANCELLED),
    ],
)
def test_manager_can_make_manager_transitions(
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    assert_allowed(
        TicketWorkflowActorKind.MANAGER,
        current_status,
        new_status,
    )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        # CREATED можно только ACCEPTED или REJECTED.
        (TicketStatus.CREATED, TicketStatus.CANCELLED),

        # Terminal status нельзя менять.
        (TicketStatus.REJECTED, TicketStatus.ACCEPTED),
        (TicketStatus.EXECUTED, TicketStatus.AT_WORK),
        (TicketStatus.CANCELLED, TicketStatus.ACCEPTED),
    ],
)
def test_manager_cannot_break_common_workflow_graph(
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    assert_forbidden(
        TicketWorkflowActorKind.MANAGER,
        current_status,
        new_status,
    )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        # Проверяющий подтверждает результат.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.EXECUTED),

        # Проверяющий возвращает на доработку.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.AT_WORK),

        # Проверяющий возвращает в управление.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.ASSIGNED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.SCHEDULED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.READY_TO_WORK),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.DEFERRED),
    ],
)
def test_reviewer_can_make_reviewer_transitions(
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    assert_allowed(
        TicketWorkflowActorKind.REVIEWER,
        current_status,
        new_status,
    )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        # Проверяющий не принимает новую заявку.
        (TicketStatus.CREATED, TicketStatus.ACCEPTED),

        # Проверяющий не отменяет принятую заявку.
        (TicketStatus.ACCEPTED, TicketStatus.CANCELLED),

        # Проверяющий не стартует работу до стадии review.
        (TicketStatus.ASSIGNED, TicketStatus.AT_WORK),

        # Проверяющий не планирует обычную принятую заявку.
        (TicketStatus.ACCEPTED, TicketStatus.SCHEDULED),
    ],
)
def test_reviewer_cannot_make_non_reviewer_transitions(
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    assert_forbidden(
        TicketWorkflowActorKind.REVIEWER,
        current_status,
        new_status,
    )