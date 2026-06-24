# src/domain/ticket.py



from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Self

from src.domain.exceptions import DomainOperationError
from src.domain.policy.ticket_workflow_policy import TicketWorkflowPolicy
from src.domain.statuses.ticket_status import (
    TicketStatus,
    is_department_change_locked,
    is_terminal_ticket_status,
)
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.statuses.ticket_status_record_factory import TicketStatusRecordFactory
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
    - защищает локальные инварианты.

    Not responsible for:
    - permissions;
    - actor role checks;
    - department rules;
    - executor.department_id == ticket.department_id;
    - enabled / disabled Admin;
    - enabled / disabled Department;
    - concrete workflow use cases.

    Workflow-сценарии должны жить в: TicketExecutionService, TicketManagementService, TicketReviewService
    """

    ticket_id: int
    client_id: int
    admin_id: int

    text_of_ticket: str = ""
    user_id: int = 0
    contact_user_id: int = 0

    statuses: list[TicketStatusRecord] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)

    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    is_remote: bool = False
    is_closed: bool = False
    date_finished: datetime | None = None

    version: int = 0
    urgency_level: int = 0
    user_ticket_id: int = 0

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
        comment: str = "",
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
            statuses=[
                TicketStatusRecordFactory.created(
                    actor_employee_id=admin_id,
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
        is_remote: bool = False,
        is_closed: bool = False,
        date_finished: datetime | None = None,
        version: int = 0,
        urgency_level: int = 0,
        user_ticket_id: int = 0,
    ) -> Self:
        """
        Восстанавливает Ticket из БД.

        Repository обязан передать полную историю статусов.
        """

        if not statuses:
            raise DomainOperationError("Cannot rehydrate Ticket without status history")

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
            is_remote=is_remote,
            is_closed=is_closed,
            date_finished=date_finished,
            version=version,
            urgency_level=urgency_level,
            user_ticket_id=user_ticket_id,
        )

    def __post_init__(self) -> None:
        self.text_of_ticket = self.text_of_ticket.strip()

        if not self.text_of_ticket:
            raise DomainOperationError("Ticket text_of_ticket cannot be empty")

        self._recompute_closed_state()

    # ----------------------------
    # Queries
    # ----------------------------

    def current_status(self) -> TicketStatus:
        if not self.statuses:
            raise DomainOperationError("Ticket has no status history")

        return self.statuses[-1].status

    def current_status_record(self) -> TicketStatusRecord:
        if not self.statuses:
            raise DomainOperationError("Ticket has no status history")

        return self.statuses[-1]

    def current_executor_id(self) -> int:
        """
        Возвращает текущего ответственного исполнителя.

        0 означает: текущий исполнитель отсутствует.

        Важно:
        источник истины — текущая status-record, а не последняя
        историческая запись с executor_id > 0.

        Например:
            READY_TO_WORK executor_id=10
            SCHEDULED executor_id=0

        После этого текущего исполнителя нет.
        """

        return self.current_status_record().executor_id

    def has_executor(self) -> bool:
        return self.current_executor_id() > 0

    def is_terminal(self) -> bool:
        return is_terminal_ticket_status(
            self.current_status(),
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

    def change_department(self)->None:
        if is_department_change_locked(self.current_status()):
            raise DomainOperationError(
                "Cannot change ticket department in current status"
            )

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
        Добавляет новую workflow-запись в историю заявки.

        Проверяет только локальные инварианты:
        - заявка не terminal;
        - переход допустим по общему графу workflow.

        Не проверяет:
        - permissions;
        - actor kind;
        - actor является текущим executor или нет;
        - executor существует;
        - executor enabled;
        - executor принадлежит department заявки.
        """

        self._ensure_not_terminal()

        TicketWorkflowPolicy.ensure_can_change_status(
            current_status=self.current_status(),
            new_status=record.status,
        )

        self.statuses.append(record)
        self._recompute_closed_state()

    def add_comment(self, comment: Comment) -> None:
        """
        Добавляет обычный комментарий к заявке.

        Это не комментарий к workflow-статусу.
        Комментарии к workflow-событиям лежат в TicketStatusRecord.comment.
        """

        self._ensure_not_terminal()
        self.comments.append(comment)

    # ----------------------------
    # Internal helpers
    # ----------------------------

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
            self.date_finished = self.current_status_record().date_created
        else:
            self.date_finished = None
    # ----------------------------
    # Analytics
    # ----------------------------

    def working_time(self) -> int:
        """
        Возвращает рабочее время в секундах.

        Считаем:
        - AT_WORK по системной истории статусов;
        - OFFLINE_WORK по фактическим actual_started_at / actual_finished_at.

        AT_WORK:
            date_created -> next status date_created
            если AT_WORK текущий статус -> date_created -> now

        OFFLINE_WORK:
            actual_started_at -> actual_finished_at

        Если у OFFLINE_WORK нет actual_finished_at,
        длительность не считаем, потому что она неизвестна.
        """

        if not self.statuses:
            return 0

        total_seconds = 0

        for current_record, next_record in zip(self.statuses, self.statuses[1:]):
            if current_record.status == TicketStatus.AT_WORK:
                total_seconds += self._seconds_between(
                    current_record.date_created,
                    next_record.date_created,
                )

            elif current_record.status == TicketStatus.OFFLINE_WORK:
                total_seconds += self._offline_work_seconds(current_record)

        last_record = self.current_status_record()

        if last_record.status == TicketStatus.AT_WORK:
            total_seconds += self._seconds_between(
                last_record.date_created,
                self._now_like(last_record.date_created),
            )

        elif last_record.status == TicketStatus.OFFLINE_WORK:
            total_seconds += self._offline_work_seconds(last_record)

        return total_seconds

    def _offline_work_seconds(self, record: TicketStatusRecord) -> int:
        if record.actual_started_at is None or record.actual_finished_at is None:
            return 0

        return self._seconds_between(
            record.actual_started_at,
            record.actual_finished_at,
        )


    def belong(self, employee_id: int) -> bool:
        """
        Проверяет, упоминается ли сотрудник в истории заявки.

        Это не permission check.

        Использовать для принятия решений о доступе нельзя.
        Для удаления Admin/User лучше использовать repository-level
        has_admin_reference / has_user_reference.
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
    def _seconds_between(start: datetime, finish: datetime) -> int:
        """
        Возвращает разницу между datetime в секундах.

        Новый код должен использовать timezone-aware UTC datetime.
        Но этот helper терпим к старым naive datetime из БД.
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
        Возвращает now() в формате, совместимом с value:
        - если value timezone-aware, возвращает aware UTC now;
        - если value naive, возвращает naive now.
        """

        if value.tzinfo is None:
            return datetime.now()

        return datetime.now(timezone.utc)