# src/domain/ticket_status.py

from enum import StrEnum


class TicketStatus(StrEnum):
    """
    Workflow-статусы заявки.

    Важно:
    - статус не просто поле;
    - каждая новая запись статуса — это бизнес-событие;
    - старые записи статусов не редактируются.

    До начала работы есть три разных состояния:

    SCHEDULED:
        есть плановое время, но нет исполнителя.

    ASSIGNED:
        есть исполнитель, но нет планового времени.

    READY_TO_WORK:
        есть и плановое время, и исполнитель.
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

    # Есть плановое время выполнения, но исполнитель ещё не назначен.
    SCHEDULED = "scheduled"

    # Есть назначенный исполнитель, но плановое время не задано.
    ASSIGNED = "assigned"

    # Есть и плановое время, и назначенный исполнитель.
    # Заявка готова к началу работы.
    READY_TO_WORK = "ready_to_work"

    # Исполнитель работает над заявкой прямо сейчас.
    # actual_started_at для этого статуса ставится автоматически.
    AT_WORK = "at_work"

    # Работа началась, но временно приостановлена.
    # Ответственный исполнитель сохраняется.
    PAUSED = "paused"

    # Работа внесена задним числом.
    # Используется, если исполнитель не мог вовремя перевести заявку в AT_WORK.
    # actual_started_at и actual_finished_at обязательны.
    OFFLINE_WORK = "offline_work"

    # Исполнитель завершил свой этап работы,
    # но результат ещё должен быть подтверждён клиентом или другим сотрудником.
    READY_FOR_REVIEW = "ready_for_review"

    # Заявка выполнена и подтверждена. Конечный статус.
    EXECUTED = "executed"

    # Заявка снята после того, как уже была принята. Конечный статус.
    CANCELLED = "cancelled"


# Статусы, после которых заявка больше не должна изменяться.
TERMINAL_TICKET_STATUSES = frozenset({
    TicketStatus.REJECTED,
    TicketStatus.EXECUTED,
    TicketStatus.CANCELLED,
})


# Статусы, в которых обязательно должен быть ответственный исполнитель.
#
# SCHEDULED сюда не входит:
# SCHEDULED означает "запланировано, но исполнитель ещё не назначен".
#
# READY_TO_WORK входит:
# READY_TO_WORK означает "есть и время, и исполнитель".
EXECUTOR_REQUIRED_STATUSES = frozenset({
    TicketStatus.ASSIGNED,
    TicketStatus.READY_TO_WORK,
    TicketStatus.AT_WORK,
    TicketStatus.PAUSED,
    TicketStatus.OFFLINE_WORK,
    TicketStatus.READY_FOR_REVIEW,
})


# Статусы, для которых обязательна плановая дата.
#
# ASSIGNED сюда не входит:
# ASSIGNED означает "исполнитель назначен, но планового времени нет".
#
# READY_TO_WORK входит:
# READY_TO_WORK означает "есть и время, и исполнитель".
PLANNED_START_REQUIRED_STATUSES = frozenset({
    TicketStatus.SCHEDULED,
    TicketStatus.READY_TO_WORK,
})


# Статусы, означающие, что работа уже фактически началась
# или исполнитель уже заявил результат.
#
# READY_TO_WORK сюда не входит:
# заявка готова к работе, но работа ещё не началась.
WORK_STARTED_STATUSES = frozenset({
    TicketStatus.AT_WORK,
    TicketStatus.PAUSED,
    TicketStatus.OFFLINE_WORK,
    TicketStatus.READY_FOR_REVIEW,
})


# Статусы, в которых department заявки нельзя менять всегда.
#
# SCHEDULED сюда не входит:
# заявка может быть запланирована без исполнителя,
# и позже может выясниться, что нужен другой department.
#
# ASSIGNED входит:
# исполнитель уже назначен, значит department нельзя менять простым изменением поля.
#
# READY_TO_WORK входит:
# есть и исполнитель, и плановое время.
TICKET_DEPARTMENT_CHANGE_FORBIDDEN_STATUSES = frozenset({
    TicketStatus.ASSIGNED,
    TicketStatus.READY_TO_WORK,
    TicketStatus.AT_WORK,
    TicketStatus.PAUSED,
    TicketStatus.OFFLINE_WORK,
    TicketStatus.READY_FOR_REVIEW,
    TicketStatus.EXECUTED,
    TicketStatus.CANCELLED,
    TicketStatus.REJECTED,
})


# Граф допустимых переходов между статусами.
#
# Здесь указана только теоретическая допустимость перехода.
# Роли actor-а здесь не проверяются.
#
# Например:
# - AT_WORK -> ASSIGNED бизнесом возможен как аварийный переход;
# - но обычный исполнитель не должен иметь права его делать.
ALLOWED_TICKET_STATUS_TRANSITIONS = {
    TicketStatus.CREATED: frozenset({
        TicketStatus.ACCEPTED,
        TicketStatus.REJECTED,
    }),

    TicketStatus.ACCEPTED: frozenset({
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.DEFERRED: frozenset({
        TicketStatus.ACCEPTED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.SCHEDULED: frozenset({
        # Перепланирование.
        TicketStatus.SCHEDULED,

        # Назначили исполнителя при сохранённой плановой дате.
        TicketStatus.READY_TO_WORK,

        # Сняли плановую дату и назначили исполнителя.
        TicketStatus.ASSIGNED,

        # Сняли плановую дату, заявка снова просто принята.
        TicketStatus.ACCEPTED,

        TicketStatus.DEFERRED,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.ASSIGNED: frozenset({
        # Переназначение исполнителя.
        TicketStatus.ASSIGNED,

        # Добавили плановую дату при сохранённом исполнителе.
        TicketStatus.READY_TO_WORK,

        # Сняли исполнителя и назначили плановую дату.
        TicketStatus.SCHEDULED,

        # Сняли исполнителя, заявка снова просто принята.
        TicketStatus.ACCEPTED,

        # Исполнитель начал работу без планирования.
        TicketStatus.AT_WORK,

        # Исполнитель внёс работу задним числом.
        TicketStatus.OFFLINE_WORK,

        TicketStatus.DEFERRED,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.READY_TO_WORK: frozenset({
        # Изменили исполнителя и/или плановую дату.
        TicketStatus.READY_TO_WORK,

        # Сняли исполнителя, плановая дата осталась.
        TicketStatus.SCHEDULED,

        # Сняли плановую дату, исполнитель остался.
        TicketStatus.ASSIGNED,

        # Сняли и исполнителя, и плановую дату.
        TicketStatus.ACCEPTED,

        # Работа началась.
        TicketStatus.AT_WORK,

        # Работа внесена задним числом.
        TicketStatus.OFFLINE_WORK,

        TicketStatus.DEFERRED,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.AT_WORK: frozenset({
        # Обычные действия исполнителя.
        TicketStatus.PAUSED,
        TicketStatus.READY_FOR_REVIEW,

        # Управленческие / аварийные переходы.
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.PAUSED: frozenset({
        # Исполнитель вернулся к работе.
        TicketStatus.AT_WORK,

        # Управленческие переходы.
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.OFFLINE_WORK: frozenset({
        TicketStatus.READY_FOR_REVIEW,
    }),

    TicketStatus.READY_FOR_REVIEW: frozenset({
        # Результат подтверждён.
        TicketStatus.EXECUTED,

        # Результат не подтверждён, нужна доработка.
        TicketStatus.AT_WORK,

        # Нужно переназначение / новое планирование / ожидание.
        TicketStatus.ASSIGNED,
        TicketStatus.SCHEDULED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.DEFERRED,

        TicketStatus.CANCELLED,
    }),

    TicketStatus.REJECTED: frozenset(),
    TicketStatus.EXECUTED: frozenset(),
    TicketStatus.CANCELLED: frozenset(),
}