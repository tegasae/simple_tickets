# src/domain/policy/ticket_workflow_actor_policy.py

from enum import StrEnum

from src.domain.exceptions import DomainOperationError
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

    Эта policy не проверяет:
    - есть ли у actor-а RBAC permission;
    - является ли actor текущим executor;
    - belongs ли executor к department;
    - enabled ли Admin;
    - enabled ли Department.

    Она проверяет только тип workflow-действия.
    """

    _EXECUTOR_ALLOWED_TRANSITIONS = frozenset({
        # Исполнитель начал работу, потом временно приостановил.
        (TicketStatus.AT_WORK, TicketStatus.PAUSED),

        # Исполнитель считает, что его этап работы завершён.
        (TicketStatus.AT_WORK, TicketStatus.READY_FOR_REVIEW),

        # Исполнитель возвращается к работе после паузы.
        (TicketStatus.PAUSED, TicketStatus.AT_WORK),

        # Исполнитель внёс offline work и отправляет результат на проверку.
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
        (TicketStatus.ACCEPTED, TicketStatus.AT_WORK),
        (TicketStatus.ACCEPTED, TicketStatus.OFFLINE_WORK),
        (TicketStatus.ACCEPTED, TicketStatus.CANCELLED),

        # Управление отложенной заявкой.
        (TicketStatus.DEFERRED, TicketStatus.SCHEDULED),
        (TicketStatus.DEFERRED, TicketStatus.ASSIGNED),
        (TicketStatus.DEFERRED, TicketStatus.CANCELLED),

        # Планирование / перепланирование.
        (TicketStatus.SCHEDULED, TicketStatus.SCHEDULED),
        (TicketStatus.SCHEDULED, TicketStatus.ASSIGNED),
        (TicketStatus.SCHEDULED, TicketStatus.AT_WORK),
        (TicketStatus.SCHEDULED, TicketStatus.OFFLINE_WORK),
        (TicketStatus.SCHEDULED, TicketStatus.CANCELLED),

        # Назначение / переназначение.
        (TicketStatus.ASSIGNED, TicketStatus.ASSIGNED),
        (TicketStatus.ASSIGNED, TicketStatus.SCHEDULED),
        (TicketStatus.ASSIGNED, TicketStatus.AT_WORK),
        (TicketStatus.ASSIGNED, TicketStatus.OFFLINE_WORK),
        (TicketStatus.ASSIGNED, TicketStatus.CANCELLED),

        # Аварийные / управленческие переходы из работы.
        (TicketStatus.AT_WORK, TicketStatus.PAUSED),
        (TicketStatus.AT_WORK, TicketStatus.DEFERRED),
        (TicketStatus.AT_WORK, TicketStatus.ASSIGNED),
        (TicketStatus.AT_WORK, TicketStatus.SCHEDULED),
        (TicketStatus.AT_WORK, TicketStatus.CANCELLED),

        # Управление paused-заявкой.
        (TicketStatus.PAUSED, TicketStatus.AT_WORK),
        (TicketStatus.PAUSED, TicketStatus.DEFERRED),
        (TicketStatus.PAUSED, TicketStatus.ASSIGNED),
        (TicketStatus.PAUSED, TicketStatus.SCHEDULED),
        (TicketStatus.PAUSED, TicketStatus.CANCELLED),

        # Управление результатом проверки.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.AT_WORK),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.ASSIGNED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.SCHEDULED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.DEFERRED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.CANCELLED),

        # Manager тоже может подтвердить выполнение,
        # если это разрешено конкретным use case / permission.
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.EXECUTED),
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

        allowed_transitions = TicketWorkflowActorPolicy._TRANSITIONS_BY_ACTOR_KIND[
            actor_kind
        ]

        transition = (current_status, new_status)

        if transition not in allowed_transitions:
            raise DomainOperationError(
                f"{actor_kind} cannot change ticket status "
                f"from {current_status} to {new_status}"
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