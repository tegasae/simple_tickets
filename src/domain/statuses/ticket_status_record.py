# src/domain/statuses/ticket_status_record.py


from dataclasses import dataclass, field
from datetime import datetime, timezone, UTC
from typing import Self

from src.domain.exceptions import ItemValidationError, DomainOperationError
from src.domain.statuses.ticket_status import (

    get_ticket_state, TicketStatus,
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

    actor_employee_id: int=0
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

    @classmethod
    def create_new(cls,actor_employee_id:int):
        return TicketStatusRecord(actor_employee_id=actor_employee_id,status=TicketStatus.CREATED,date_created=datetime.now(UTC))

    @classmethod
    def create_from_ticket_user(cls):
        return TicketStatusRecord(status_id=0,
            actor_employee_id=0,
            status=TicketStatus.CREATED_FROM_TICKET_USER,
            date_created=datetime.now(UTC),
            executor_id=0,
            planned_start_at=None,
            planned_finish_at=None,
            actual_started_at=None,
            actual_finished_at=None,
            comment="")

    def validate_review_transition(self,record: Self):

        """
                Проверяет два разных способа попасть в READY_FOR_REVIEW.

                Онлайн-workflow:
                    AT_WORK -> READY_FOR_REVIEW

                    actual_started_at не передаётся:
                    начало уже отражено status record AT_WORK.

                Ретроспективная регистрация:
                    SCHEDULED / ASSIGNED / READY_TO_WORK
                    -> READY_FOR_REVIEW

                    actual_started_at обязателен.
                """
        if record.status != TicketStatus.READY_FOR_REVIEW:
            return



        if self.status == TicketStatus.AT_WORK:
            if record.actual_started_at is not None:
                raise DomainOperationError(
                    "AT_WORK -> READY_FOR_REVIEW must not provide "
                    "actual_started_at",
                )
            return

        if self.status in {
            TicketStatus.SCHEDULED,
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
        }:
            if record.actual_started_at is None:
                raise DomainOperationError(
                    "Retrospective work registration requires "
                    "actual_started_at",
                )
            return
        raise DomainOperationError(
            "READY_FOR_REVIEW can be reached only from "
            "AT_WORK, SCHEDULED, ASSIGNED, or READY_TO_WORK",
        )

    def online_work(self)->bool:
        return self.status==TicketStatus.AT_WORK

    def offline_work(self)->bool:
        return self.status == TicketStatus.READY_FOR_REVIEW

    def is_new(self) -> bool:
        return self.status_id == 0

    def is_terminal(self):
        return get_ticket_state(self.status).terminal

    def can_change_department(self)->bool:
        state=get_ticket_state(self.status)
        return not state.locks_department_change

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

    def can_update_text(self)->bool:
        state = get_ticket_state(
            self.status,
        )
        return state.allows_ticket_text_update

    def can_move_to_next_record(self,record: Self)->bool:
        state = get_ticket_state(self.status)
        return state.allows_transition_to(record.status)


    def is_first_status(self)->bool:
        state=get_ticket_state(status=self.status)
        return state.first_status

    def _validate_identity(self) -> None:
        if self.status_id < 0:
            raise ItemValidationError(
                "Status record ID cannot be negative"
            )

        if self.actor_employee_id < 0:
            raise ItemValidationError(
                "Actor employee ID cannot be negative"
            )

        state=get_ticket_state(status=self.status)
        if (
                self.actor_employee_id == 0
                and
                not state.first_status
            ):
            raise ItemValidationError(
                "Actor employee ID can be 0 only for user-driven ticket statuses"
            )

        if (
                self.actor_employee_id > 0
                and state.first_status
        ):
            raise ItemValidationError(
                f"Status {self.status.value} must have actor_employee_id = 0"
            )

        if self.executor_id < 0:
            raise ItemValidationError(
                "Executor ID cannot be negative"
            )

    def created_from_ticket_user_to_accepted(self,record:Self)->bool:
        if self.status == TicketStatus.CREATED_FROM_TICKET_USER and record.status == TicketStatus.ACCEPTED:
            return True
        else:
            return False


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

        if state.requires_comment and not self.comment:
            raise ItemValidationError(
                f"Status {self.status.value} requires comment"
            )

        if state.requires_executor and self.executor_id <= 0:
            raise ItemValidationError(
                f"Status {self.status.value} requires executor"
            )

        if not state.requires_executor and self.executor_id != 0:
            raise ItemValidationError(
                f"Status {self.status.value} cannot have executor"
            )


        self._validate_planned_payload(
            requires_planned_start=state.requires_planned_start,
        )
        self._validate_actual_payload()



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



    def _validate_ready_for_review_payload(self) -> None:
        if self.executor_id <= 0:
            raise ItemValidationError(
                "READY_FOR_REVIEW requires executor_id"
            )

        if self.actual_finished_at is None:
            raise ItemValidationError(
                "READY_FOR_REVIEW requires actual_finished_at"
            )

        if (
                self.actual_started_at is not None
                and self.actual_started_at > self.actual_finished_at
        ):
            raise ItemValidationError(
                "actual_started_at cannot be after actual_finished_at"
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