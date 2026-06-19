# src/domain/ticket_status_record.py



from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus


@dataclass(kw_only=True)
class TicketStatusRecord:
    """
    Одна запись истории workflow заявки.

    Это не просто "значение статуса".
    Это бизнес-событие, добавленное в историю заявки.

    Старые записи статусов не редактируются.
    Новое workflow-действие добавляет новую запись.

    Важно:
    - executor_id = 0 означает "исполнитель не назначен";
    - planned_start_at/planned_finish_at могут быть None;
    - actual_started_at/actual_finished_at могут быть None;
    - необходимость comment для отдельных операций проверяется factory-методами.
    """

    # 0 означает: запись ещё не сохранена в БД.
    status_id: int = 0

    # Кто выполнил workflow-действие.
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
    planned_start_at: datetime | None = None

    # Плановое время окончания.
    planned_finish_at: datetime | None = None

    # Фактическое начало работы.
    actual_started_at: datetime | None = None

    # Фактическое окончание работы.
    actual_finished_at: datetime | None = None

    # Комментарий к workflow-событию.
    #
    # Это не обычный комментарий к заявке.
    # Обычные комментарии лежат отдельно в Ticket.comments.
    comment: str = ""

    def __post_init__(self) -> None:
        self._normalize_status()
        self._normalize_comment()

        self._validate_ids()
        self._validate_planned_time()
        self._validate_actual_time()
        self._validate_comment()
        self._validate_status_payload()

    # ----------------------------
    # Queries
    # ----------------------------

    def is_new(self) -> bool:
        return self.status_id == 0

    def has_executor(self) -> bool:
        return self.executor_id > 0

    def has_planned_start(self) -> bool:
        return self.planned_start_at is not None

    def has_planned_finish(self) -> bool:
        return self.planned_finish_at is not None

    def has_actual_start(self) -> bool:
        return self.actual_started_at is not None

    def has_actual_finish(self) -> bool:
        return self.actual_finished_at is not None

    # ----------------------------
    # Normalize
    # ----------------------------

    def _normalize_status(self) -> None:
        try:
            self.status = TicketStatus(self.status)
        except ValueError as e:
            raise ItemValidationError(f"Invalid ticket status: {self.status}") from e

    def _normalize_comment(self) -> None:
        self.comment = self.comment.strip()

    # ----------------------------
    # Basic validation
    # ----------------------------

    def _validate_ids(self) -> None:
        if self.status_id < 0:
            raise ItemValidationError("Status ID cannot be negative")

        if self.actor_employee_id <= 0:
            raise ItemValidationError("Actor employee ID must be positive")

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
        now = datetime.now(timezone.utc)

        if self.actual_started_at is not None:
            self._ensure_not_future(
                value=self.actual_started_at,
                now=now,
                message="Actual start time cannot be in the future",
            )

        if self.actual_finished_at is not None:
            self._ensure_not_future(
                value=self.actual_finished_at,
                now=now,
                message="Actual finish time cannot be in the future",
            )

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

    # ----------------------------
    # Status payload validation
    # ----------------------------

    def _validate_status_payload(self) -> None:
        """
        Проверяет, что поля записи соответствуют смыслу статуса.

        Это локальная валидность самой status-record.

        Здесь НЕ проверяем:
        - можно ли перейти из старого статуса в новый;
        - кто имеет право выполнить переход;
        - существует ли executor;
        - belongs ли executor к department заявки.
        """

        if self.status == TicketStatus.SCHEDULED:
            self._validate_scheduled_payload()
            return

        if self.status == TicketStatus.ASSIGNED:
            self._validate_assigned_payload()
            return

        if self.status == TicketStatus.READY_TO_WORK:
            self._validate_ready_to_work_payload()
            return

        if self.status == TicketStatus.AT_WORK:
            self._validate_at_work_payload()
            return

        if self.status == TicketStatus.PAUSED:
            self._validate_paused_payload()
            return

        if self.status == TicketStatus.OFFLINE_WORK:
            self._validate_offline_work_payload()
            return

        if self.status == TicketStatus.READY_FOR_REVIEW:
            self._validate_ready_for_review_payload()
            return

        self._validate_non_workflow_payload()

    def _validate_scheduled_payload(self) -> None:
        if not self.has_planned_start():
            raise ItemValidationError("Planned start time is required for SCHEDULED")

        if self.has_executor():
            raise ItemValidationError("SCHEDULED cannot have executor")

        self._ensure_no_actual_time("SCHEDULED cannot have actual work time")

    def _validate_assigned_payload(self) -> None:
        if not self.has_executor():
            raise ItemValidationError("Executor is required for ASSIGNED")

        if self.has_planned_start() or self.has_planned_finish():
            raise ItemValidationError("ASSIGNED cannot have planned time")

        self._ensure_no_actual_time("ASSIGNED cannot have actual work time")

    def _validate_ready_to_work_payload(self) -> None:
        if not self.has_executor():
            raise ItemValidationError("Executor is required for READY_TO_WORK")

        if not self.has_planned_start():
            raise ItemValidationError(
                "Planned start time is required for READY_TO_WORK"
            )

        self._ensure_no_actual_time("READY_TO_WORK cannot have actual work time")

    def _validate_at_work_payload(self) -> None:
        if not self.has_executor():
            raise ItemValidationError("Executor is required for AT_WORK")

        if not self.has_actual_start():
            raise ItemValidationError("Actual start time is required for AT_WORK")

        if self.has_actual_finish():
            raise ItemValidationError("AT_WORK cannot have actual finish time")

        self._ensure_no_planned_time("AT_WORK cannot have planned time")

    def _validate_paused_payload(self) -> None:
        if not self.has_executor():
            raise ItemValidationError("Executor is required for PAUSED")

        self._ensure_no_planned_time("PAUSED cannot have planned time")
        self._ensure_no_actual_time("PAUSED cannot have actual work time")

    def _validate_offline_work_payload(self) -> None:
        if not self.has_executor():
            raise ItemValidationError("Executor is required for OFFLINE_WORK")

        if not self.has_actual_start():
            raise ItemValidationError(
                "Actual start time is required for OFFLINE_WORK"
            )

        if not self.has_actual_finish():
            raise ItemValidationError(
                "Actual finish time is required for OFFLINE_WORK"
            )

        self._ensure_no_planned_time("OFFLINE_WORK cannot have planned time")


    def _validate_ready_for_review_payload(self) -> None:
        if not self.has_executor():
            raise ItemValidationError("Executor is required for READY_FOR_REVIEW")

        if not self.has_actual_finish():
            raise ItemValidationError(
                "Actual finish time is required for READY_FOR_REVIEW"
            )

        self._ensure_no_planned_time("READY_FOR_REVIEW cannot have planned time")

    def _validate_non_workflow_payload(self) -> None:
        """
        CREATED / ACCEPTED / REJECTED / DEFERRED / EXECUTED / CANCELLED.

        Эти статусы не должны нести executor/planned/actual данные.
        Если нужны детали причины — используем comment.
        """
        self._ensure_no_executor(f"{self.status} cannot have executor")
        self._ensure_no_planned_time(f"{self.status} cannot have planned time")
        self._ensure_no_actual_time(f"{self.status} cannot have actual work time")

    # ----------------------------
    # Small helpers
    # ----------------------------

    def _ensure_no_executor(self, message: str) -> None:
        if self.has_executor():
            raise ItemValidationError(message)

    def _ensure_no_planned_time(self, message: str) -> None:
        if self.has_planned_start() or self.has_planned_finish():
            raise ItemValidationError(message)

    def _ensure_no_actual_time(self, message: str) -> None:
        if self.has_actual_start() or self.has_actual_finish():
            raise ItemValidationError(message)

    @staticmethod
    def _ensure_not_future(
        *,
        value: datetime,
        now: datetime,
        message: str,
    ) -> None:
        """
        datetime может быть timezone-aware или naive.

        В новом коде лучше использовать timezone-aware UTC.
        Но для совместимости с уже сохранёнными naive datetime
        сравниваем naive с naive, aware с aware.
        """
        if value.tzinfo is None:
            comparable_now = datetime.now()
        else:
            comparable_now = now

        if value > comparable_now:
            raise ItemValidationError(message)