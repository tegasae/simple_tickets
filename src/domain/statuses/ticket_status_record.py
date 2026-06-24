# src/domain/statuses/ticket_status_record.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import (
    TicketStatus,
    get_ticket_state,
)


@dataclass(kw_only=True)
class TicketStatusRecord:
    """
    Неизменяемый факт изменения статуса Ticket.

    Record хранит:
    - кто выполнил действие;
    - в какой статус переведена заявка;
    - текущего исполнителя после перехода;
    - плановые и фактические времена;
    - комментарий к переходу.

    Старые записи не изменяются.
    """

    status_id: int = 0

    actor_employee_id: int
    status: TicketStatus

    date_created: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    executor_id: int = 0

    planned_start_at: datetime | None = None
    planned_finish_at: datetime | None = None

    actual_started_at: datetime | None = None
    actual_finished_at: datetime | None = None

    comment: str = ""

    def __post_init__(self) -> None:
        self.status = TicketStatus(self.status)
        self.comment = self._normalize_comment(self.comment)

        self.date_created = self._normalize_datetime(
            value=self.date_created,
            field_name="date_created",
        )
        self.planned_start_at = self._normalize_optional_datetime(
            value=self.planned_start_at,
            field_name="planned_start_at",
        )
        self.planned_finish_at = self._normalize_optional_datetime(
            value=self.planned_finish_at,
            field_name="planned_finish_at",
        )
        self.actual_started_at = self._normalize_optional_datetime(
            value=self.actual_started_at,
            field_name="actual_started_at",
        )
        self.actual_finished_at = self._normalize_optional_datetime(
            value=self.actual_finished_at,
            field_name="actual_finished_at",
        )

        self._validate_identity()
        self._validate_time_ranges()
        self._validate_actual_times()
        self._validate_status_payload()

    def is_new(self) -> bool:
        return self.status_id == 0

    def has_executor(self) -> bool:
        return self.executor_id > 0

    def has_planned_start(self) -> bool:
        return self.planned_start_at is not None

    def has_planned_finish(self) -> bool:
        return self.planned_finish_at is not None

    def has_actual_started(self) -> bool:
        return self.actual_started_at is not None

    def has_actual_finished(self) -> bool:
        return self.actual_finished_at is not None

    def _validate_identity(self) -> None:
        if self.status_id < 0:
            raise ItemValidationError(
                "Status record ID cannot be negative"
            )

        if self.actor_employee_id <= 0:
            raise ItemValidationError(
                "Actor employee ID must be positive"
            )

        if self.executor_id < 0:
            raise ItemValidationError(
                "Executor ID cannot be negative"
            )

    def _validate_time_ranges(self) -> None:
        if (
            self.planned_start_at is not None
            and self.planned_finish_at is not None
            and self.planned_finish_at < self.planned_start_at
        ):
            raise ItemValidationError(
                "Planned finish cannot be before planned start"
            )

        if (
            self.actual_started_at is not None
            and self.actual_finished_at is not None
            and self.actual_finished_at < self.actual_started_at
        ):
            raise ItemValidationError(
                "Actual finish cannot be before actual start"
            )

    def _validate_actual_times(self) -> None:
        now = datetime.now(timezone.utc)

        if (
            self.actual_started_at is not None
            and self.actual_started_at > now
        ):
            raise ItemValidationError(
                "Actual start cannot be in the future"
            )

        if (
            self.actual_finished_at is not None
            and self.actual_finished_at > now
        ):
            raise ItemValidationError(
                "Actual finish cannot be in the future"
            )

    def _validate_status_payload(self) -> None:
        state = get_ticket_state(self.status)

        self._validate_executor_payload(
            requires_executor=state.requires_executor,
        )
        self._validate_planned_payload(
            requires_planned_start=state.requires_planned_start,
        )
        self._validate_actual_payload()

    def _validate_executor_payload(
        self,
        *,
        requires_executor: bool,
    ) -> None:
        if requires_executor and self.executor_id <= 0:
            raise ItemValidationError(
                f"Status {self.status.value} requires executor"
            )

        if not requires_executor and self.executor_id != 0:
            raise ItemValidationError(
                f"Status {self.status.value} cannot have executor"
            )

    def _validate_planned_payload(
        self,
        *,
        requires_planned_start: bool,
    ) -> None:
        if requires_planned_start and self.planned_start_at is None:
            raise ItemValidationError(
                f"Status {self.status.value} requires planned start"
            )

        if (
            not requires_planned_start
            and (
                self.planned_start_at is not None
                or self.planned_finish_at is not None
            )
        ):
            raise ItemValidationError(
                f"Status {self.status.value} cannot have planned time"
            )

    def _validate_actual_payload(self) -> None:
        if self.status == TicketStatus.AT_WORK:
            self._validate_at_work_payload()
            return

        if self.status == TicketStatus.OFFLINE_WORK:
            self._validate_offline_work_payload()
            return

        if self.status == TicketStatus.READY_FOR_REVIEW:
            self._validate_ready_for_review_payload()
            return

        self._ensure_no_actual_times()

    def _validate_at_work_payload(self) -> None:
        if self.actual_started_at is None:
            raise ItemValidationError(
                "AT_WORK requires actual start time"
            )

        if self.actual_finished_at is not None:
            raise ItemValidationError(
                "AT_WORK cannot have actual finish time"
            )

    def _validate_offline_work_payload(self) -> None:
        if self.actual_started_at is None:
            raise ItemValidationError(
                "OFFLINE_WORK requires actual start time"
            )

        if self.actual_finished_at is None:
            raise ItemValidationError(
                "OFFLINE_WORK requires actual finish time"
            )

    def _validate_ready_for_review_payload(self) -> None:
        if self.actual_started_at is not None:
            raise ItemValidationError(
                "READY_FOR_REVIEW cannot have actual start time"
            )

        if self.actual_finished_at is None:
            raise ItemValidationError(
                "READY_FOR_REVIEW requires actual finish time"
            )

    def _ensure_no_actual_times(self) -> None:
        if self.actual_started_at is not None:
            raise ItemValidationError(
                f"Status {self.status.value} cannot have actual start time"
            )

        if self.actual_finished_at is not None:
            raise ItemValidationError(
                f"Status {self.status.value} cannot have actual finish time"
            )

    @staticmethod
    def _normalize_comment(comment: str) -> str:
        if not isinstance(comment, str):
            raise ItemValidationError(
                "Status comment must be a string"
            )

        comment = comment.strip()

        if len(comment) > 1000:
            raise ItemValidationError(
                "Status comment cannot exceed 1000 characters"
            )

        return comment

    @staticmethod
    def _normalize_optional_datetime(
        *,
        value: datetime | None,
        field_name: str,
    ) -> datetime | None:
        if value is None:
            return None

        return TicketStatusRecord._normalize_datetime(
            value=value,
            field_name=field_name,
        )

    @staticmethod
    def _normalize_datetime(
        *,
        value: datetime,
        field_name: str,
    ) -> datetime:
        if not isinstance(value, datetime):
            raise ItemValidationError(
                f"{field_name} must be datetime"
            )

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)