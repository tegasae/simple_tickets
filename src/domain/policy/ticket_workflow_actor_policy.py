# src/domain/policy/ticket_workflow_actor_policy.py

from enum import StrEnum

from src.domain.exceptions import DomainOperationError
from src.domain.policy.ticket_workflow_policy import TicketWorkflowPolicy
from src.domain.statuses.ticket_status import TicketStatus


class TicketWorkflowActorKind(StrEnum):
    """
    Тип actor-а внутри workflow.

    Это не RBAC permission.

    RBAC отвечает на вопрос:
        "Имеет ли сотрудник право вызвать use case?"

    ActorKind отвечает на вопрос:
        "Какой тип workflow-действия он сейчас выполняет?"
    """

    # Ответственный исполнитель заявки.
    EXECUTOR = "executor"

    # Сотрудник, который управляет заявкой:
    # первая линия, менеджер, сотрудник по работе с клиентами,
    # руководитель, администратор процесса.
    MANAGER = "manager"

    # Проверяющий / подтверждающий результат.
    # Это может быть клиент, сотрудник по работе с клиентами,
    # старший технический специалист и т.д.
    REVIEWER = "reviewer"


class TicketWorkflowActorPolicy:
    """
    Проверяет, может ли actor данного типа выполнить переход.

    Важно:
    actor-specific transitions НЕ расширяют общий workflow-граф.

    Переход разрешён только если:
    1. он разрешён общим TicketWorkflowPolicy;
    2. он разрешён для actor_kind.

    Эта policy не проверяет:
    - есть ли у actor-а RBAC permission;
    - является ли actor текущим executor;
    - belongs ли executor к department;
    - enabled ли Admin;
    - enabled ли Department.
    """

    _EXECUTOR_ALLOWED_TRANSITIONS = frozenset({
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

        # Offline-work уже содержит actual_started_at и actual_finished_at,
        # после этого результат можно отправить на проверку.
        (TicketStatus.OFFLINE_WORK, TicketStatus.READY_FOR_REVIEW),
    })

    _MANAGER_ALLOWED_TRANSITIONS = frozenset({
        # Первичная обработка.
        (TicketStatus.CREATED, TicketStatus.ACCEPTED),
        (TicketStatus.CREATED, TicketStatus.REJECTED),

        # Управление принятой заявкой.
        (TicketStatus.ACCEPTED, TicketStatus.DEFERRED),
        (TicketStatus.ACCEPTED, TicketStatus.SCHEDULED),
        (TicketStatus.ACCEPTED, TicketStatus.ASSIGNED),
        (TicketStatus.ACCEPTED, TicketStatus.READY_TO_WORK),
        (TicketStatus.ACCEPTED, TicketStatus.CANCELLED),

        # Управление отложенной заявкой.
        (TicketStatus.DEFERRED, TicketStatus.ACCEPTED),
        (TicketStatus.DEFERRED, TicketStatus.SCHEDULED),
        (TicketStatus.DEFERRED, TicketStatus.ASSIGNED),
        (TicketStatus.DEFERRED, TicketStatus.READY_TO_WORK),
        (TicketStatus.DEFERRED, TicketStatus.CANCELLED),

        # Планирование / перепланирование.
        (TicketStatus.SCHEDULED, TicketStatus.SCHEDULED),
        (TicketStatus.SCHEDULED, TicketStatus.READY_TO_WORK),
        (TicketStatus.SCHEDULED, TicketStatus.ASSIGNED),
        (TicketStatus.SCHEDULED, TicketStatus.ACCEPTED),
        (TicketStatus.SCHEDULED, TicketStatus.DEFERRED),
        (TicketStatus.SCHEDULED, TicketStatus.CANCELLED),

        # Назначение / переназначение.
        (TicketStatus.ASSIGNED, TicketStatus.ASSIGNED),
        (TicketStatus.ASSIGNED, TicketStatus.READY_TO_WORK),
        (TicketStatus.ASSIGNED, TicketStatus.SCHEDULED),
        (TicketStatus.ASSIGNED, TicketStatus.ACCEPTED),
        (TicketStatus.ASSIGNED, TicketStatus.AT_WORK),
        (TicketStatus.ASSIGNED, TicketStatus.OFFLINE_WORK),
        (TicketStatus.ASSIGNED, TicketStatus.DEFERRED),
        (TicketStatus.ASSIGNED, TicketStatus.CANCELLED),

        # Управление заявкой, готовой к работе.
        (TicketStatus.READY_TO_WORK, TicketStatus.READY_TO_WORK),
        (TicketStatus.READY_TO_WORK, TicketStatus.SCHEDULED),
        (TicketStatus.READY_TO_WORK, TicketStatus.ASSIGNED),
        (TicketStatus.READY_TO_WORK, TicketStatus.ACCEPTED),
        (TicketStatus.READY_TO_WORK, TicketStatus.AT_WORK),
        (TicketStatus.READY_TO_WORK, TicketStatus.OFFLINE_WORK),
        (TicketStatus.READY_TO_WORK, TicketStatus.DEFERRED),
        (TicketStatus.READY_TO_WORK, TicketStatus.CANCELLED),

        # Аварийные / управленческие переходы из работы.
        (TicketStatus.AT_WORK, TicketStatus.PAUSED),
        (TicketStatus.AT_WORK, TicketStatus.DEFERRED),
        (TicketStatus.AT_WORK, TicketStatus.SCHEDULED),
        (TicketStatus.AT_WORK, TicketStatus.ASSIGNED),
        (TicketStatus.AT_WORK, TicketStatus.READY_TO_WORK),
        (TicketStatus.AT_WORK, TicketStatus.CANCELLED),

        # Управление paused-заявкой.
        (TicketStatus.PAUSED, TicketStatus.AT_WORK),
        (TicketStatus.PAUSED, TicketStatus.DEFERRED),
        (TicketStatus.PAUSED, TicketStatus.SCHEDULED),
        (TicketStatus.PAUSED, TicketStatus.ASSIGNED),
        (TicketStatus.PAUSED, TicketStatus.READY_TO_WORK),
        (TicketStatus.PAUSED, TicketStatus.CANCELLED),

        # Offline-work внесён, результат нужно передать на проверку.
        (TicketStatus.OFFLINE_WORK, TicketStatus.READY_FOR_REVIEW),

        # Управление результатом проверки.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.EXECUTED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.AT_WORK),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.ASSIGNED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.SCHEDULED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.READY_TO_WORK),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.DEFERRED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.CANCELLED),
    })

    _REVIEWER_ALLOWED_TRANSITIONS = frozenset({
        # Проверяющий подтверждает результат.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.EXECUTED),

        # Проверяющий отклоняет результат и возвращает на доработку.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.AT_WORK),

        # Проверяющий понимает, что нужен другой исполнитель.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.ASSIGNED),

        # Проверяющий понимает, что нужно новое планирование.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.SCHEDULED),

        # Проверяющий понимает, что нужны и исполнитель, и новая дата.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.READY_TO_WORK),

        # Проверяющий понимает, что нужно ожидание клиента / данные / согласование.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.DEFERRED),
    })

    _TRANSITIONS_BY_ACTOR_KIND = {
        TicketWorkflowActorKind.EXECUTOR: _EXECUTOR_ALLOWED_TRANSITIONS,
        TicketWorkflowActorKind.MANAGER: _MANAGER_ALLOWED_TRANSITIONS,
        TicketWorkflowActorKind.REVIEWER: _REVIEWER_ALLOWED_TRANSITIONS,
    }

    @staticmethod
    def ensure_actor_can_change_status(
        *,
        actor_kind: TicketWorkflowActorKind,
        current_status: TicketStatus,
        new_status: TicketStatus,
    ) -> None:
        actor_kind = TicketWorkflowActorKind(actor_kind)
        current_status = TicketStatus(current_status)
        new_status = TicketStatus(new_status)

        # Главная защита:
        # actor-policy не может расширить общий workflow-граф.
        TicketWorkflowPolicy.ensure_can_change_status(
            current_status=current_status,
            new_status=new_status,
        )

        TicketWorkflowActorPolicy._ensure_actor_transition_allowed(
            actor_kind=actor_kind,
            current_status=current_status,
            new_status=new_status,
        )

    @staticmethod
    def can_actor_change_status(
        *,
        actor_kind: TicketWorkflowActorKind,
        current_status: TicketStatus,
        new_status: TicketStatus,
    ) -> bool:
        try:
            TicketWorkflowActorPolicy.ensure_actor_can_change_status(
                actor_kind=actor_kind,
                current_status=current_status,
                new_status=new_status,
            )
            return True
        except DomainOperationError:
            return False

    @staticmethod
    def _ensure_actor_transition_allowed(
        *,
        actor_kind: TicketWorkflowActorKind,
        current_status: TicketStatus,
        new_status: TicketStatus,
    ) -> None:
        allowed_transitions = TicketWorkflowActorPolicy._TRANSITIONS_BY_ACTOR_KIND[
            actor_kind
        ]

        transition = (current_status, new_status)

        if transition not in allowed_transitions:
            raise DomainOperationError(
                f"{actor_kind.value} cannot change ticket status "
                f"from {current_status.value} to {new_status.value}"
            )