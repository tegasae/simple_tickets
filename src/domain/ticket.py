# src/domain/ticket.py

from dataclasses import dataclass, field
from datetime import datetime, timezone, UTC
from typing import Self

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.statuses.ticket_status import (
    TicketStatus,
    get_ticket_state,
)
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket_components import Comment


@dataclass(kw_only=True)
class Ticket:
    """
    Ticket aggregate.

    Responsibilities:
    - хранит данные заявки;
    - хранит историю workflow-статусов;
    - хранит обычные комментарии к заявке;
    - вычисляет текущий статус;
    - вычисляет текущего исполнителя из текущей status-record;
    - защищает локальные инварианты workflow.

    Not responsible for:
    - permissions;
    - actor role checks;
    - department rules между aggregates;
    - executor.department_id == ticket.department_id;
    - enabled / disabled Admin;
    - enabled / disabled Department;
    - concrete workflow use cases.

    Workflow use cases живут в:
    - TicketExecutionService;
    - TicketManagementService;
    - TicketReviewService.
    """

    ticket_id: int
    client_id: int
    admin_id: int = 0

    text_of_ticket: str = ""
    user_id: int = 0
    contact_user_id: int = 0

    statuses: list[TicketStatusRecord] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)

    date_created: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    department_id: int = 0
    is_remote: bool = False

    is_closed: bool = False
    date_finished: datetime | None = None

    version: int = 0
    urgency_level: int = 0
    user_ticket_id: int = 0
    description: str = ""

    @classmethod
    def create(
        cls,
        *,
        ticket_id: int,
        client_id: int,
        admin_id: int,
        text_of_ticket: str = "",
        user_id: int = 0,
        contact_user_id: int = 0,
        is_remote: bool = False,
        urgency_level: int = 0,
        user_ticket_id: int = 0,
        department_id: int = 0,
        comment: str = "",
        description: str = "",
    ) -> Self:
        """
        Создаёт новую заявку.

        CREATED добавляется только здесь.
        __post_init__ не должен автоматически добавлять CREATED.
        """
        ticket = cls(
            ticket_id=ticket_id,
            client_id=client_id,
            admin_id=admin_id,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=contact_user_id,
            is_remote=is_remote,
            urgency_level=urgency_level,
            user_ticket_id=user_ticket_id,
            department_id=department_id,
            description=description,
            statuses=[
                TicketStatusRecord(
                    actor_employee_id=admin_id,
                    status=TicketStatus.CREATED,
                )
            ],
        )

        if comment.strip():
            ticket.add_comment(
                Comment(
                    employee_id=admin_id,
                    comment=comment.strip(),
                )
            )

        return ticket

    @classmethod
    def create_from_ticket_user(
            cls,
            *,
            ticket_id: int,
            client_id: int,
            user_id: int,
            contact_user_id: int,
            user_ticket_id: int,
            text_of_ticket: str,
            description: str = "",
            urgency_level: int = 0,
            department_id: int = 0,
            is_remote: bool = False,
            date_created: datetime | None = None,
    ) -> "Ticket":
        """
        Create internal Ticket automatically from TicketUser.

        This factory is used only by application service in the coordinated use case:

            User creates TicketUser
                -> application service creates linked Ticket

        Important:
            Ticket must not create TicketUser.
            TicketUser must not create Ticket.
            Both aggregates are coordinated by application service.

        Initial state:

            Ticket.CREATED
            admin_id = 0
            user_ticket_id = TicketUser.ticket_id
            initial TicketStatusRecord.actor_employee_id = 0

        Meaning of actor_employee_id = 0:

            system-generated action;
            not Admin;
            not User;
            not Executor.
        """
        if ticket_id <= 0:
            raise ItemValidationError("Ticket id must be positive.")

        if client_id <= 0:
            raise ItemValidationError("Client id must be positive.")

        if user_id <= 0:
            raise ItemValidationError("User id must be positive.")

        if user_ticket_id <= 0:
            raise ItemValidationError("User ticket id must be positive.")

        text = text_of_ticket.strip()
        if not text:
            raise ItemValidationError("Text of ticket must not be empty.")

        now = date_created or datetime.now(UTC)

        created_status = TicketStatusRecord(
            status_id=0,
            actor_employee_id=0,
            status=TicketStatus.CREATED,
            date_created=now,
            executor_id=0,
            planned_start_at=None,
            planned_finish_at=None,
            actual_started_at=None,
            actual_finished_at=None,
            comment="",
        )

        return cls(
            ticket_id=ticket_id,
            client_id=client_id,
            admin_id=0,
            user_id=user_id,
            contact_user_id=contact_user_id,
            text_of_ticket=text,
            statuses=[created_status],
            comments=[],
            date_created=now,
            department_id=department_id,
            is_remote=is_remote,
            is_closed=False,
            date_finished=None,
            version=0,
            urgency_level=urgency_level,
            user_ticket_id=user_ticket_id,
            description=description.strip(),
        )


    @classmethod
    def rehydrate(
        cls,
        *,
        ticket_id: int,
        client_id: int,
        admin_id: int,
        text_of_ticket: str = "",
        user_id: int = 0,
        contact_user_id: int = 0,
        statuses: list[TicketStatusRecord],
        comments: list[Comment] | None = None,
        date_created: datetime,
        department_id: int = 0,
        description: str = "",
        is_remote: bool = False,
        is_closed: bool = False,
        date_finished: datetime | None = None,
        version: int = 0,
        urgency_level: int = 0,
        user_ticket_id: int = 0,
    ) -> Self:
        """
        Восстанавливает Ticket из БД.

        Repository обязан передать полную историю статусов
        в стабильном порядке:
            ORDER BY date_created, status_id

        is_closed и date_finished являются derived state.
        Они будут пересчитаны в __post_init__.
        """
        if not statuses:
            raise DomainOperationError(
                "Cannot rehydrate Ticket without status history"
            )

        return cls(
            ticket_id=ticket_id,
            client_id=client_id,
            admin_id=admin_id,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=contact_user_id,
            statuses=statuses,
            comments=comments or [],
            date_created=date_created,
            department_id=department_id,
            description=description,
            is_remote=is_remote,
            is_closed=is_closed,
            date_finished=date_finished,
            version=version,
            urgency_level=urgency_level,
            user_ticket_id=user_ticket_id,
        )

    def __post_init__(self) -> None:
        self.text_of_ticket = self.text_of_ticket.strip()
        self.description = self.description.strip()

        if not self.text_of_ticket:
            raise DomainOperationError(
                "Ticket text_of_ticket cannot be empty"
            )

        if self.department_id < 0:
            raise DomainOperationError(
                "Ticket department_id cannot be negative"
            )

        self._recompute_closed_state()

    # ----------------------------
    # Queries
    # ----------------------------

    def current_status(self) -> TicketStatus:
        if not self.statuses:
            raise DomainOperationError(
                "Ticket has no status history"
            )

        return self.statuses[-1].status

    def current_status_record(self) -> TicketStatusRecord:
        if not self.statuses:
            raise DomainOperationError(
                "Ticket has no status history"
            )

        return self.statuses[-1]

    def current_executor_id(self) -> int:
        """
        Возвращает текущего ответственного исполнителя.

        0 означает: текущий исполнитель отсутствует.

        Источник истины — текущая status-record, а не последняя
        историческая запись с executor_id > 0.

        Например:
            READY_TO_WORK executor_id=10
            SCHEDULED executor_id=0

        После SCHEDULED текущего исполнителя нет.
        """
        return self.current_status_record().executor_id

    def has_executor(self) -> bool:
        return self.current_executor_id() > 0

    def is_terminal(self) -> bool:
        return get_ticket_state(
            self.current_status()
        ).terminal

    def can_change_status(
        self,
        new_status: TicketStatus,
    ) -> bool:
        """
        Проверяет допустимость перехода из текущего TicketState.

        Метод не изменяет aggregate.
        """
        current_state = get_ticket_state(
            self.current_status()
        )

        if current_state.terminal:
            return False

        return current_state.allows_transition_to(
            TicketStatus(new_status)
        )

    def new_statuses(self) -> list[TicketStatusRecord]:
        """
        Возвращает новые status-records, ещё не сохранённые в БД.
        """
        return [
            status
            for status in self.statuses
            if status.is_new()
        ]

    def new_comments(self) -> list[Comment]:
        """
        Возвращает новые обычные комментарии, ещё не сохранённые в БД.
        """
        return [
            comment
            for comment in self.comments
            if comment.comment_id == 0
        ]

    # ----------------------------
    # Commands
    # ----------------------------

    def append_status(self, record: TicketStatusRecord) -> None:
        """
        Добавляет новую workflow-запись.

        Ticket защищает инварианты:
        - terminal Ticket не изменяется;
        - переход разрешён текущим TicketState;
        - READY_FOR_REVIEW содержит корректный payload
          для конкретного исходного статуса.
        """
        self._ensure_not_terminal()

        if not self.can_change_status(record.status):
            raise DomainOperationError(
                "Ticket status transition is not allowed: "
                f"{self.current_status().value} -> "
                f"{record.status.value}"
            )

        self._validate_review_transition(record)

        self.statuses.append(record)
        self._recompute_closed_state()

    def add_comment(self, comment: Comment) -> None:
        """
        Добавляет обычный комментарий к заявке.

        Это не комментарий к workflow-событию.
        Комментарии к workflow-событиям лежат в
        TicketStatusRecord.comment.
        """
        self._ensure_not_terminal()
        comment.comment=comment.comment.strip()
        if not comment.comment:
            DomainOperationError("The comment can't be empty")
        self.comments.append(comment)

    def change_department(
        self,
        *,
        department_id: int,
    ) -> None:
        """
        Меняет department Ticket.

        Проверки существования Department, его enabled-state
        и совместимости с Admin выполняются вне aggregate.

        Ticket проверяет только локальный workflow-инвариант:
        в текущем статусе department может быть заблокирован.
        """
        self._ensure_not_terminal()
        if department_id < 0:
            raise DomainOperationError(
                "Ticket department_id cannot be negative"
            )

        current_state = get_ticket_state(
            self.current_status()
        )

        if current_state.locks_department_change:
            raise DomainOperationError(
                "Cannot change ticket department in current status"
            )

        self.department_id = department_id

    def update_ticket_text(
            self,
            *,
            text_of_ticket: str,
    ) -> None:
        state = get_ticket_state(self.current_status_record().status)
        text_of_ticket=text_of_ticket.strip()
        if not text_of_ticket:
            DomainOperationError("The text can't be empty")
        if not state.allows_ticket_text_update:
            raise DomainOperationError(
                "Ticket text cannot be changed in the current status."
            )

        self.text_of_ticket = text_of_ticket

    def update_description(
            self,
            *,
            description: str,
    ) -> None:
        description = description.strip()
        if not description:
            DomainOperationError("The description can't be empty")
        if self.is_terminal():
            raise DomainOperationError(
                "Ticket description cannot be changed after ticket completion."
            )

        self.description = description
    # ----------------------------
    # Internal workflow helpers
    # ----------------------------

    def _validate_review_transition(
        self,
        record: TicketStatusRecord,
    ) -> None:
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

        previous_status = self.current_status()

        if previous_status == TicketStatus.AT_WORK:
            if record.actual_started_at is not None:
                raise DomainOperationError(
                    "AT_WORK -> READY_FOR_REVIEW must not provide "
                    "actual_started_at"
                )
            return

        if previous_status in {
            TicketStatus.SCHEDULED,
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
        }:
            if record.actual_started_at is None:
                raise DomainOperationError(
                    "Retrospective work registration requires "
                    "actual_started_at"
                )
            return

        raise DomainOperationError(
            "READY_FOR_REVIEW can be reached only from "
            "AT_WORK, SCHEDULED, ASSIGNED, or READY_TO_WORK"
        )

    def _ensure_not_terminal(self) -> None:
        if self.is_terminal():
            raise DomainOperationError(
                f"The ticket {self.ticket_id} is in terminal status "
                f"{self.current_status().value}"
            )

    def _recompute_closed_state(self) -> None:
        """
        Пересчитывает derived state.

        is_closed и date_finished определяются текущим статусом.
        """
        if not self.statuses:
            self.is_closed = False
            self.date_finished = None
            return

        self.is_closed = self.is_terminal()

        if self.is_closed:
            self.date_finished = (
                self.current_status_record().date_created
            )
        else:
            self.date_finished = None

    # ----------------------------
    # Analytics
    # ----------------------------

    def working_time(self) -> int:
        """
        Возвращает рабочее время в секундах.

        Онлайн-работа:
            AT_WORK.date_created
            -> date_created следующей status record.

            Если AT_WORK является текущим статусом:
            AT_WORK.date_created -> now().

        Ретроспективно внесённая работа:
            READY_FOR_REVIEW.actual_started_at
            -> READY_FOR_REVIEW.actual_finished_at.

        READY_FOR_REVIEW без actual_started_at является результатом
        обычной работы через AT_WORK и отдельно не учитывается.
        """
        if not self.statuses:
            return 0

        total_seconds = 0

        for index, current_record in enumerate(self.statuses):
            next_record = (
                self.statuses[index + 1]
                if index + 1 < len(self.statuses)
                else None
            )

            if current_record.status == TicketStatus.AT_WORK:
                finish_at = (
                    next_record.date_created
                    if next_record is not None
                    else self._now_like(current_record.date_created)
                )

                total_seconds += self._seconds_between(
                    current_record.date_created,
                    finish_at,
                )

            elif (
                current_record.status
                == TicketStatus.READY_FOR_REVIEW
            ):
                total_seconds += self._retrospective_work_seconds(
                    current_record
                )

        return total_seconds

    @staticmethod
    def _retrospective_work_seconds(
        record: TicketStatusRecord,
    ) -> int:
        """
        Возвращает длительность ретроспективно внесённой работы.

        Признак ретроспективной регистрации:
            READY_FOR_REVIEW.actual_started_at is not None.
        """
        if (
            record.actual_started_at is None
            or record.actual_finished_at is None
        ):
            return 0

        return Ticket._seconds_between(
            record.actual_started_at,
            record.actual_finished_at,
        )

    def belong(self, employee_id: int) -> bool:
        """
        Проверяет, упоминается ли сотрудник в истории Ticket.

        Это не permission check.

        Использовать для проверки доступа нельзя.
        Для удаления Admin/User нужны repository-level проверки:
            has_admin_reference
            has_user_reference
        """
        if employee_id == self.admin_id:
            return True

        for comment in self.comments:
            if employee_id == comment.employee_id:
                return True

        for status in self.statuses:
            if employee_id == status.actor_employee_id:
                return True

            if employee_id == status.executor_id:
                return True

        return False

    @staticmethod
    def _seconds_between(
        start: datetime,
        finish: datetime,
    ) -> int:
        """
        Возвращает разницу между datetime в секундах.

        Новый код использует timezone-aware UTC datetime.
        Helper терпим к старым naive datetime из БД.
        """
        if start.tzinfo is None and finish.tzinfo is not None:
            finish = finish.replace(tzinfo=None)

        if start.tzinfo is not None and finish.tzinfo is None:
            start = start.replace(tzinfo=None)

        delta = finish - start
        return int(delta.total_seconds())

    @staticmethod
    def _now_like(value: datetime) -> datetime:
        """
        Возвращает now() в формате, совместимом с value.

        - timezone-aware value -> aware UTC now;
        - naive value -> naive local now.
        """
        if value.tzinfo is None:
            return datetime.now()

        return datetime.now(timezone.utc)