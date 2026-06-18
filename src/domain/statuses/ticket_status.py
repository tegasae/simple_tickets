# src/domain/ticket_status.py

from enum import StrEnum


class TicketStatus(StrEnum):
    """
    Workflow-статусы заявки.

    Важно:
    - статус не просто поле;
    - каждая новая запись статуса — это бизнес-событие;
    - старые записи статусов не редактируются.
    """

    # Заявка создана, но ещё не подтверждена как корректная.
    CREATED = "created"

    # Заявка отклонена до принятия. Конечный статус.
    REJECTED = "rejected"

    # Заявка принята как корректная и стала рабочей заявкой.
    ACCEPTED = "accepted"

    # Заявка отложена: нужны данные, согласование, доступы,
    # решение менеджера или другое внешнее ожидание.
    DEFERRED = "deferred"

    # Заявка запланирована.
    # Обязательна плановая дата.
    # Исполнитель может быть ещё не назначен.
    SCHEDULED = "scheduled"

    # Назначен ответственный исполнитель.
    # Исполнитель обязателен.
    ASSIGNED = "assigned"

    # Исполнитель работает над заявкой прямо сейчас.
    # actual_started_at для этого статуса ставится автоматически.
    AT_WORK = "at_work"

    # Работа началась, но временно приостановлена.
    # Ответственный исполнитель сохраняется.
    PAUSED = "paused"

    # Работа внесена задним числом.
    # Используется, если исполнитель не мог вовремя перевести заявку в AT_WORK.
    OFFLINE_WORK = "offline_work"

    # Исполнитель завершил свой этап работы,
    # но результат ещё должен быть подтверждён клиентом или другим сотрудником.
    READY_FOR_REVIEW = "ready_for_review"

    # Заявка выполнена и подтверждена. Конечный статус.
    EXECUTED = "executed"

    # Заявка снята после того, как уже была принята. Конечный статус.
    CANCELLED = "cancelled"


TERMINAL_TICKET_STATUSES = frozenset({
    TicketStatus.REJECTED,
    TicketStatus.EXECUTED,
    TicketStatus.CANCELLED,
})


EXECUTOR_REQUIRED_STATUSES = frozenset({
    TicketStatus.ASSIGNED,
    TicketStatus.AT_WORK,
    TicketStatus.PAUSED,
    TicketStatus.OFFLINE_WORK,
    TicketStatus.READY_FOR_REVIEW,
})


PLANNED_START_REQUIRED_STATUSES = frozenset({
    TicketStatus.SCHEDULED,
})


WORK_STARTED_STATUSES = frozenset({
    TicketStatus.AT_WORK,
    TicketStatus.PAUSED,
    TicketStatus.OFFLINE_WORK,
    TicketStatus.READY_FOR_REVIEW,
})


TICKET_DEPARTMENT_CHANGE_FORBIDDEN_STATUSES = frozenset({
    TicketStatus.AT_WORK,
    TicketStatus.PAUSED,
    TicketStatus.OFFLINE_WORK,
    TicketStatus.READY_FOR_REVIEW,
    TicketStatus.EXECUTED,
    TicketStatus.CANCELLED,
    TicketStatus.REJECTED,
})


ALLOWED_TICKET_STATUS_TRANSITIONS = {
    TicketStatus.CREATED: frozenset({
        TicketStatus.ACCEPTED,
        TicketStatus.REJECTED,
    }),

    TicketStatus.ACCEPTED: frozenset({
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.AT_WORK,
        TicketStatus.OFFLINE_WORK,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.DEFERRED: frozenset({
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.SCHEDULED: frozenset({
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.AT_WORK,
        TicketStatus.OFFLINE_WORK,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.ASSIGNED: frozenset({
        TicketStatus.ASSIGNED,
        TicketStatus.SCHEDULED,
        TicketStatus.AT_WORK,
        TicketStatus.OFFLINE_WORK,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.AT_WORK: frozenset({
        TicketStatus.PAUSED,
        TicketStatus.READY_FOR_REVIEW,

        # Управленческие / аварийные переходы.
        # Обычный исполнитель их делать не должен.
        TicketStatus.DEFERRED,
        TicketStatus.ASSIGNED,
        TicketStatus.SCHEDULED,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.PAUSED: frozenset({
        TicketStatus.AT_WORK,

        # Управленческие переходы.
        TicketStatus.DEFERRED,
        TicketStatus.ASSIGNED,
        TicketStatus.SCHEDULED,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.OFFLINE_WORK: frozenset({
        TicketStatus.READY_FOR_REVIEW,
    }),

    TicketStatus.READY_FOR_REVIEW: frozenset({
        TicketStatus.EXECUTED,
        TicketStatus.AT_WORK,
        TicketStatus.ASSIGNED,
        TicketStatus.SCHEDULED,
        TicketStatus.DEFERRED,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.REJECTED: frozenset(),
    TicketStatus.EXECUTED: frozenset(),
    TicketStatus.CANCELLED: frozenset(),
}