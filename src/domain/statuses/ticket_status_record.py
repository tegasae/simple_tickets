# src/domain/ticket_status_record.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus


@dataclass(kw_only=True)
class StatusRecordTicket:
    """
    Одна запись истории workflow заявки.

    Это не просто "значение статуса".
    Это бизнес-событие, добавленное в историю заявки.

    Старые записи статусов не редактируются.
    Новое workflow-действие добавляет новую запись.
    """
    status_id: int = 0
    # Кто выполнил действие.
    actor_employee_id: int

    # Новый статус заявки.
    status: TicketStatus

    # Когда событие было добавлено в систему.
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


    # Ответственный исполнитель.
    #
    # 0 означает: исполнитель отсутствует.
    # > 0 означает: исполнитель назначен.
    executor_id: int = 0

    # Плановое время начала / выполнения.
    #
    # Для SCHEDULED planned_start_at обязателен,
    # но это проверяется factory-методом.
    planned_start_at: datetime | None = None

    # Плановое время окончания.
    planned_finish_at: datetime | None = None

    # Фактическое начало работы.
    #
    # Для AT_WORK ставится автоматически factory-методом.
    # Для OFFLINE_WORK обязательно передаётся явно.
    actual_started_at: datetime | None = None

    # Фактическое окончание работы.
    #
    # Используется для OFFLINE_WORK и READY_FOR_REVIEW.
    actual_finished_at: datetime | None = None

    # Комментарий к событию.
    comment: str = ""

    def __post_init__(self) -> None:
        self._normalize_status()
        self._normalize_comment()

        self._validate_actor()
        self._validate_executor()
        self._validate_planned_time()
        self._validate_actual_time()
        self._validate_comment()

    def has_executor(self) -> bool:
        return self.executor_id > 0

    def has_planned_start(self) -> bool:
        return self.planned_start_at is not None

    def has_actual_start(self) -> bool:
        return self.actual_started_at is not None

    def has_actual_finish(self) -> bool:
        return self.actual_finished_at is not None

    def _normalize_status(self) -> None:
        try:
            self.status = TicketStatus(self.status)
        except ValueError as e:
            raise ItemValidationError(f"Invalid ticket status: {self.status}") from e

    def _normalize_comment(self) -> None:
        self.comment = self.comment.strip()

    def _validate_actor(self) -> None:
        if self.actor_employee_id <= 0:
            raise ItemValidationError("Actor employee ID must be positive")

    def _validate_executor(self) -> None:
        if self.executor_id < 0:
            raise ItemValidationError("Executor ID cannot be negative")

    def _validate_planned_time(self) -> None:
        if (
            self.planned_start_at is not None
            and self.planned_finish_at is not None
            and self.planned_finish_at < self.planned_start_at
        ):
            raise ItemValidationError(
                "Planned finish time cannot be earlier than planned start time"
            )

    def _validate_actual_time(self) -> None:
        now = datetime.now()

        if self.actual_started_at is not None and self.actual_started_at > now:
            raise ItemValidationError("Actual start time cannot be in the future")

        if self.actual_finished_at is not None and self.actual_finished_at > now:
            raise ItemValidationError("Actual finish time cannot be in the future")

        if (
            self.actual_started_at is not None
            and self.actual_finished_at is not None
            and self.actual_finished_at < self.actual_started_at
        ):
            raise ItemValidationError(
                "Actual finish time cannot be earlier than actual start time"
            )

    def _validate_comment(self) -> None:
        if len(self.comment) > 1000:
            raise ItemValidationError("Comment is too long")