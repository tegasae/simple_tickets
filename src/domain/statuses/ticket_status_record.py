# src/domain/statuses/ticket_status_record.py

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from src.domain.exceptions import (
    DomainOperationError,
    ItemValidationError,
)
from src.domain.statuses.ticket_status import (
    TicketState,
    TicketStatus,
    get_ticket_state,
)


@dataclass(kw_only=True)
class TicketStatusRecord:
    """
    Факт изменения workflow-состояния Ticket.

    TicketStatusRecord знает:
    - конкретный TicketStatus;
    - свойства этого состояния через TicketState;
    - допустимость перехода к следующей record;
    - требования к payload конкретного состояния;
    - context-dependent требования переходов.

    Ticket и domain services не должны знать детали
    конкретных TicketStatus без необходимости.
    """

    status_id: int = 0

    actor_employee_id: int = 0
    status: TicketStatus

    state: TicketState = field(
        init=False,
        repr=False,
        compare=False,
    )

    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    executor_id: int = 0

    planned_start_at: datetime | None = None
    planned_finish_at: datetime | None = None

    actual_started_at: datetime | None = None
    actual_finished_at: datetime | None = None

    comment: str = ""

    def __post_init__(self) -> None:
        self.status = TicketStatus(self.status)
        self.state = get_ticket_state(self.status)

        self.comment = self._normalize_comment(
            self.comment
        )

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

    # ----------------------------
    # Factories
    # ----------------------------

    @classmethod
    def create_new(
        cls,
        *,
        actor_employee_id: int,
        date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.CREATED,
            date_created=date_created or datetime.now(UTC),
        )

    @classmethod
    def create_from_ticket_user(
        cls,
        *,
        date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=0,
            status=TicketStatus.CREATED_FROM_TICKET_USER,
            date_created=date_created or datetime.now(UTC),
        )

    @classmethod
    def create_accepted(
        cls,
        *,
        actor_employee_id: int,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.ACCEPTED,
            comment=comment,
            date_created=date_created or datetime.now(UTC),
        )

    @classmethod
    def create_rejected(
        cls,
        *,
        actor_employee_id: int,
        comment: str,
        date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.REJECTED,
            comment=comment,
            date_created=date_created or datetime.now(UTC),
        )

    @classmethod
    def create_deferred(
        cls,
        *,
        actor_employee_id: int,
        comment: str,
        date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.DEFERRED,
            comment=comment,
            date_created=date_created or datetime.now(UTC),
        )

    @classmethod
    def create_scheduled(
        cls,
        *,
        actor_employee_id: int,
        planned_start_at: datetime,
        planned_finish_at: datetime | None = None,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.SCHEDULED,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
            date_created=date_created or datetime.now(UTC),
        )

    @classmethod
    def create_assigned(
        cls,
        *,
        actor_employee_id: int,
        executor_id: int,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.ASSIGNED,
            executor_id=executor_id,
            comment=comment,
            date_created=date_created or datetime.now(UTC),
        )

    @classmethod
    def create_ready_to_work(
        cls,
        *,
        actor_employee_id: int,
        executor_id: int,
        planned_start_at: datetime,
        planned_finish_at: datetime | None = None,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.READY_TO_WORK,
            executor_id=executor_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
            date_created=date_created or datetime.now(UTC),
        )

    @classmethod
    def create_cancelled(
        cls,
        *,
        actor_employee_id: int,
        comment: str,
        date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.CANCELLED,
            comment=comment,
            date_created=date_created or datetime.now(UTC),
        )

    @classmethod
    def create_cancelled_by_user(
        cls,
        *,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=0,
            status=TicketStatus.CANCELLED_BY_USER,
            comment=comment,
            date_created=date_created or datetime.now(UTC),
        )

    # ----------------------------
    # Execution factories
    # ----------------------------

    @classmethod
    def create_at_work(
            cls,
            *,
            actor_employee_id: int,
            executor_id: int,
            comment: str = "",
            date_created: datetime | None = None,
    ) -> Self:
        now = date_created or datetime.now(UTC)

        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.AT_WORK,
            executor_id=executor_id,
            date_created=now,
            actual_started_at=now,
            comment=comment,
        )

    @classmethod
    def create_paused(
            cls,
            *,
            actor_employee_id: int,
            executor_id: int,
            comment: str = "",
            date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.PAUSED,
            executor_id=executor_id,
            date_created=date_created or datetime.now(UTC),
            comment=comment,
        )

    @classmethod
    def create_ready_for_review_from_work(
            cls,
            *,
            actor_employee_id: int,
            executor_id: int,
            comment: str = "",
            date_created: datetime | None = None,
    ) -> Self:
        """
        Завершение обычной работы.

        actual_started_at здесь отсутствует:
        начало находится в предыдущей AT_WORK record.
        """
        now = date_created or datetime.now(UTC)

        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=executor_id,
            date_created=now,
            actual_finished_at=now,
            comment=comment,
        )

    @classmethod
    def create_ready_for_review_retrospective(
            cls,
            *,
            actor_employee_id: int,
            executor_id: int,
            actual_started_at: datetime,
            actual_finished_at: datetime,
            comment: str = "",
            date_created: datetime | None = None,
    ) -> Self:
        """
        Ретроспективная регистрация завершённой работы.

        Начало и окончание работы находятся
        в одной READY_FOR_REVIEW record.
        """
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=executor_id,
            date_created=date_created or datetime.now(UTC),
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            comment=comment,
        )

    @classmethod
    def create_executed(
            cls,
            *,
            actor_employee_id: int,
            comment: str = "",
            date_created: datetime | None = None,
    ) -> Self:
        return cls(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.EXECUTED,
            date_created=date_created or datetime.now(UTC),
            comment=comment,
        )
    # ----------------------------
    # Queries
    # ----------------------------

    def is_new(self) -> bool:
        return self.status_id == 0

    def is_terminal(self) -> bool:
        return self.state.terminal

    def is_first_status(self) -> bool:
        return self.state.first_status

    def has_executor(self) -> bool:
        return self.executor_id > 0

    def has_comment(self) -> bool:
        return bool(self.comment)

    def has_planned_start(self) -> bool:
        return self.planned_start_at is not None

    def has_planned_finish(self) -> bool:
        return self.planned_finish_at is not None

    def has_actual_started(self) -> bool:
        return self.actual_started_at is not None

    def has_actual_finished(self) -> bool:
        return self.actual_finished_at is not None

    def can_change_department(self) -> bool:
        return not self.state.locks_department_change

    def can_update_text(self) -> bool:
        return self.state.allows_ticket_text_update

    def can_move_to_next_record(
        self,
        record: Self,
    ) -> bool:
        return self.state.allows_transition_to(
            record.status
        )

    def created_from_ticket_user_to_accepted(
        self,
        record: Self,
    ) -> bool:
        return (
            self.status == TicketStatus.CREATED_FROM_TICKET_USER
            and record.status == TicketStatus.ACCEPTED
        )

    def should_reject_when_client_disabled(self) -> bool:
        """
        При отключении Client заявка в начальном состоянии
        должна быть отклонена.
        """
        return self.status in {
            TicketStatus.CREATED,
            TicketStatus.CREATED_FROM_TICKET_USER,
        }

    def should_defer_when_client_disabled(self) -> bool:
        """
        При отключении Client принятая, запланированная
        или назначенная заявка переводится в DEFERRED.
        """
        return self.status in {
            TicketStatus.ACCEPTED,
            TicketStatus.SCHEDULED,
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
        }

    # ----------------------------
    # Execution queries
    # ----------------------------

    def can_take_to_work(self) -> bool:
        return self.status in {
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
        }

    def can_pause_work(self) -> bool:
        return self.status == TicketStatus.AT_WORK

    def can_resume_work(self) -> bool:
        return self.status == TicketStatus.PAUSED

    def can_submit_for_review(self) -> bool:
        return self.status == TicketStatus.AT_WORK

    def can_record_completed_work_for_review(self) -> bool:
        return self.status in {
            TicketStatus.SCHEDULED,
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
        }






    def can_review_result(self) -> bool:
        return self.status == TicketStatus.READY_FOR_REVIEW
    # ----------------------------
    # Transition validation
    # ----------------------------

    def validate_review_transition(
        self,
        record: Self,
    ) -> None:
        if record.status != TicketStatus.READY_FOR_REVIEW:
            return

        if self.status == TicketStatus.AT_WORK:
            if record.actual_started_at is not None:
                raise DomainOperationError(
                    "AT_WORK -> READY_FOR_REVIEW "
                    "must not provide actual_started_at"
                )
            return

        if self.status in {
            TicketStatus.SCHEDULED,
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
        }:
            if record.actual_started_at is None:
                raise DomainOperationError(
                    "Retrospective work registration "
                    "requires actual_started_at"
                )
            return

        raise DomainOperationError(
            "READY_FOR_REVIEW can be reached only from "
            "AT_WORK, SCHEDULED, ASSIGNED, or READY_TO_WORK"
        )

    # ----------------------------
    # Validation
    # ----------------------------

    def _validate_identity(self) -> None:
        if self.status_id < 0:
            raise ItemValidationError(
                "Status record ID cannot be negative"
            )

        if self.actor_employee_id < 0:
            raise ItemValidationError(
                "Actor employee ID cannot be negative"
            )

        if self.executor_id < 0:
            raise ItemValidationError(
                "Executor ID cannot be negative"
            )

    def _validate_status_payload(self) -> None:
        self._validate_actor_payload()
        self._validate_executor_payload()
        self._validate_comment_payload()
        self._validate_planned_payload()
        self._validate_actual_payload()

    def _validate_actor_payload(self) -> None:
        user_driven_statuses = {
            TicketStatus.CREATED_FROM_TICKET_USER,
            TicketStatus.CANCELLED_BY_USER,
        }

        if self.status in user_driven_statuses:
            if self.actor_employee_id != 0:
                raise ItemValidationError(
                    f"Status {self.status.value} "
                    "must have actor_employee_id = 0"
                )
            return

        if self.actor_employee_id == 0:
            raise ItemValidationError(
                f"Status {self.status.value} "
                "requires actor_employee_id"
            )

    def _validate_executor_payload(self) -> None:
        if self.state.requires_executor:
            if self.executor_id == 0:
                raise ItemValidationError(
                    f"Status {self.status.value} "
                    "requires executor"
                )
            return

        if self.executor_id != 0:
            raise ItemValidationError(
                f"Status {self.status.value} "
                "cannot have executor"
            )

    def _validate_comment_payload(self) -> None:
        if (
            self.state.requires_comment
            and not self.comment
        ):
            raise ItemValidationError(
                f"Status {self.status.value} "
                "requires comment"
            )

    def _validate_planned_payload(self) -> None:
        if self.state.requires_planned_start:
            if self.planned_start_at is None:
                raise ItemValidationError(
                    f"Status {self.status.value} "
                    "requires planned_start_at"
                )
            return

        if (
            self.planned_start_at is not None
            or self.planned_finish_at is not None
        ):
            raise ItemValidationError(
                f"Status {self.status.value} "
                "cannot have planned time"
            )

    def _validate_actual_payload(self) -> None:
        if (
            self.state.requires_actual_start
            and self.actual_started_at is None
        ):
            raise ItemValidationError(
                f"Status {self.status.value} "
                "requires actual_started_at"
            )

        if (
            not self.state.allows_actual_start
            and self.actual_started_at is not None
        ):
            raise ItemValidationError(
                f"Status {self.status.value} "
                "cannot have actual_started_at"
            )

        if (
            self.state.requires_actual_finish
            and self.actual_finished_at is None
        ):
            raise ItemValidationError(
                f"Status {self.status.value} "
                "requires actual_finished_at"
            )

        if (
            not self.state.allows_actual_finish
            and self.actual_finished_at is not None
        ):
            raise ItemValidationError(
                f"Status {self.status.value} "
                "cannot have actual_finished_at"
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
        now = datetime.now(UTC)

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

    # ----------------------------
    # Normalization
    # ----------------------------

    @staticmethod
    def _normalize_comment(
        comment: str,
    ) -> str:
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
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)