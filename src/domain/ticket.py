# src/domain/ticket.py

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from src.domain.exceptions import (
    DomainOperationError,
    ItemValidationError,
)
from src.domain.statuses.ticket_status_record import TicketStatusRecord


@dataclass(kw_only=True)
class Comment:
    comment_id: int = 0
    employee_id: int
    comment: str
    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )


@dataclass(kw_only=True)
class Ticket:
    """
    Aggregate внутренней заявки.

    Ticket:
    - хранит данные заявки;
    - хранит полную историю workflow;
    - хранит обычные комментарии;
    - определяет текущее состояние через последнюю status-record;
    - проверяет корректность workflow history;
    - координирует добавление новых status-record;
    - вычисляет derived state заявки.

    admin_id:
    - Admin, который создал внутреннюю Ticket;
    - для Ticket, созданной непосредственно Admin,
      admin_id > 0;
    - для Ticket, созданной из TicketUser,
      admin_id == 0;
    - после создания Ticket значение admin_id
      никогда не изменяется.

    Сотрудник, выполняющий workflow-операцию,
    включая ACCEPTED, фиксируется в
    TicketStatusRecord.actor_employee_id.

    Ticket не знает:
    - RBAC;
    - permissions;
    - роли actor;
    - существование и enabled-state Admin/Department;
    - правила между разными aggregates.

    Семантика конкретного workflow-состояния находится
    в TicketStatusRecord / TicketState.
    """

    ticket_id: int
    client_id: int

    admin_id: int = 0

    text_of_ticket: str = ""
    user_id: int = 0
    contact_user_id: int = 0

    statuses: list[TicketStatusRecord] = field(
        default_factory=list,
    )
    comments: list[Comment] = field(
        default_factory=list,
    )

    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    department_id: int = 0
    is_remote: bool = False

    version: int = 0
    urgency_level: int = 0
    user_ticket_id: int = 0

    description: str = ""

    # Derived state.
    # Извне эти значения задавать нельзя.
    is_closed: bool = field(
        init=False,
        default=False,
    )
    date_finished: datetime | None = field(
        init=False,
        default=None,
    )

    def __post_init__(self) -> None:
        self.text_of_ticket = self.text_of_ticket.strip()
        self.description = self.description.strip()

        self._validate_identity()
        self._validate_content()
        self._validate_status_history()
        self._validate_creator_admin()

        self._recompute_closed_state()

    # ----------------------------
    # Factories
    # ----------------------------

    @classmethod
    def create(
        cls,
        *,
        ticket_id: int = 0,
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
        date_created: datetime | None = None,
    ) -> Self:
        """
        Создаёт новую внутреннюю Ticket,
        зарегистрированную Admin.

        admin_id фиксирует Admin,
        создавшего внутреннюю Ticket.
        """
        if ticket_id != 0:
            raise ItemValidationError(
                "New Ticket ticket_id must be 0",
            )

        if admin_id <= 0:
            raise ItemValidationError(
                "Admin id must be positive",
            )

        now = date_created or datetime.now(UTC)

        ticket = cls(
            ticket_id=0,
            client_id=client_id,
            admin_id=admin_id,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=contact_user_id,
            date_created=now,
            department_id=department_id,
            is_remote=is_remote,
            version=0,
            urgency_level=urgency_level,
            user_ticket_id=user_ticket_id,
            description=description,
            statuses=[
                TicketStatusRecord.create_new(
                    actor_employee_id=admin_id,
                    date_created=now,
                ),
            ],
        )

        comment = comment.strip()

        if comment:
            ticket.add_comment(
                Comment(
                    employee_id=admin_id,
                    comment=comment,
                    date_created=now,
                ),
            )

        return ticket

    @classmethod
    def create_from_ticket_user(
        cls,
        *,
        ticket_id: int = 0,
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
    ) -> Self:
        """
        Создаёт внутреннюю Ticket из TicketUser.

        Ticket и TicketUser остаются независимыми aggregates.
        Их создание координирует application service.

        Так как внутреннюю Ticket не создавал Admin:
            admin_id == 0.
        """
        if ticket_id != 0:
            raise ItemValidationError(
                "New Ticket ticket_id must be 0",
            )

        if user_id <= 0:
            raise ItemValidationError(
                "User id must be positive",
            )

        if user_ticket_id <= 0:
            raise ItemValidationError(
                "User ticket id must be positive",
            )

        now = date_created or datetime.now(UTC)

        return cls(
            ticket_id=0,
            client_id=client_id,
            admin_id=0,
            user_id=user_id,
            contact_user_id=contact_user_id,
            text_of_ticket=text_of_ticket,
            date_created=now,
            department_id=department_id,
            is_remote=is_remote,
            version=0,
            urgency_level=urgency_level,
            user_ticket_id=user_ticket_id,
            description=description,
            statuses=[
                TicketStatusRecord.create_from_ticket_user(
                    date_created=now,
                ),
            ],
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        ticket_id: int,
        client_id: int,
        admin_id: int,
        text_of_ticket: str,
        statuses: list[TicketStatusRecord],
        date_created: datetime,
        user_id: int = 0,
        contact_user_id: int = 0,
        comments: list[Comment] | None = None,
        department_id: int = 0,
        description: str = "",
        is_remote: bool = False,
        version: int = 0,
        urgency_level: int = 0,
        user_ticket_id: int = 0,
    ) -> Self:
        """
        Восстанавливает Ticket из persistence.

        Repository обязан передать:
        - persisted ticket_id > 0;
        - полную status history;
        - history в правильном порядке.

        admin_id должен соответствовать actor_employee_id
        первой status-record:
        - CREATED -> admin_id > 0;
        - CREATED_FROM_TICKET_USER -> admin_id == 0.

        is_closed и date_finished не загружаются как
        domain state, потому что вычисляются из history.
        """
        if ticket_id <= 0:
            raise DomainOperationError(
                "Cannot rehydrate Ticket with non-positive ticket_id",
            )

        if not statuses:
            raise DomainOperationError(
                "Cannot rehydrate Ticket without status history",
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
            version=version,
            urgency_level=urgency_level,
            user_ticket_id=user_ticket_id,
        )

    # ----------------------------
    # Queries
    # ----------------------------

    def is_new(self) -> bool:
        return self.ticket_id == 0

    def current_status_record(self) -> TicketStatusRecord:
        if not self.statuses:
            raise DomainOperationError(
                "Ticket has no status history",
            )

        return self.statuses[-1]

    def current_executor_id(self) -> int:
        """
        Текущий исполнитель определяется исключительно
        текущей status-record.

        0 означает отсутствие текущего исполнителя.
        """
        return self.current_status_record().executor_id

    def has_executor(self) -> bool:
        return self.current_executor_id() > 0

    def is_terminal(self) -> bool:
        return self.current_status_record().is_terminal()

    def new_statuses(self) -> list[TicketStatusRecord]:
        return [
            record
            for record in self.statuses
            if record.is_new()
        ]

    def new_comments(self) -> list[Comment]:
        return [
            comment
            for comment in self.comments
            if comment.comment_id == 0
        ]

    # ----------------------------
    # Commands
    # ----------------------------

    def append_status(
        self,
        record: TicketStatusRecord,
    ) -> None:
        """
        Добавляет новую workflow-record.

        Проверяются:
        - допустимость перехода;
        - context-dependent payload перехода.

        admin_id при workflow-переходах
        никогда не изменяется.
        """
        current_record = self.current_status_record()

        if not current_record.can_move_to_next_record(record):
            raise DomainOperationError(
                "Ticket status transition is not allowed: "
                f"{current_record.status.value} -> "
                f"{record.status.value}",
            )

        current_record.validate_review_transition(
            record,
        )

        self.statuses.append(record)

        self._recompute_closed_state()

    def add_comment(
        self,
        comment: Comment,
    ) -> None:
        if self.is_terminal():
            raise DomainOperationError(
                f"Cannot add comment to terminal Ticket "
                f"{self.ticket_id}",
            )

        comment.comment = comment.comment.strip()

        if not comment.comment:
            raise DomainOperationError(
                "Comment cannot be empty",
            )

        self.comments.append(comment)

    def change_department(
        self,
        *,
        department_id: int,
    ) -> None:
        if department_id < 0:
            raise DomainOperationError(
                "Ticket department_id cannot be negative",
            )

        if self.is_terminal():
            raise DomainOperationError(
                f"Cannot change department of terminal Ticket "
                f"{self.ticket_id}",
            )

        if not self.current_status_record().can_change_department():
            raise DomainOperationError(
                "Cannot change ticket department in current status",
            )

        self.department_id = department_id

    def update_details(
        self,
        *,
        actor_employee_id: int,
        description: str = "",
        contact_user_id: int = 0,
        is_remote: bool = False,
    ) -> None:
        if actor_employee_id <= 0:
            raise DomainOperationError(
                "actor_employee_id must be positive",
            )

        if self.is_terminal():
            raise DomainOperationError(
                "Cannot update details of terminal Ticket",
            )

        if contact_user_id < 0:
            raise DomainOperationError(
                "contact_user_id cannot be negative",
            )

        self.description = description.strip()
        self.contact_user_id = contact_user_id
        self.is_remote = is_remote

    def update_ticket_text(
        self,
        *,
        text_of_ticket: str,
    ) -> None:
        text_of_ticket = text_of_ticket.strip()

        if not text_of_ticket:
            raise DomainOperationError(
                "Ticket text cannot be empty",
            )

        if not self.current_status_record().can_update_text():
            raise DomainOperationError(
                "Ticket text cannot be changed "
                "in the current status",
            )

        self.text_of_ticket = text_of_ticket

    def update_description(
        self,
        *,
        description: str,
    ) -> None:
        if self.is_terminal():
            raise DomainOperationError(
                "Ticket description cannot be changed "
                "after ticket completion",
            )

        description = description.strip()

        if not description:
            raise DomainOperationError(
                "Ticket description cannot be empty",
            )

        self.description = description

    # ----------------------------
    # Validation
    # ----------------------------

    def _validate_identity(self) -> None:
        if self.ticket_id < 0:
            raise DomainOperationError(
                "Ticket ticket_id cannot be negative",
            )

        if self.client_id <= 0:
            raise DomainOperationError(
                "Ticket client_id must be positive",
            )

        if self.admin_id < 0:
            raise DomainOperationError(
                "Ticket admin_id cannot be negative",
            )

        if self.user_id < 0:
            raise DomainOperationError(
                "Ticket user_id cannot be negative",
            )

        if self.contact_user_id < 0:
            raise DomainOperationError(
                "Ticket contact_user_id cannot be negative",
            )

        if self.department_id < 0:
            raise DomainOperationError(
                "Ticket department_id cannot be negative",
            )

        if self.version < 0:
            raise DomainOperationError(
                "Ticket version cannot be negative",
            )

        if self.urgency_level < 0:
            raise DomainOperationError(
                "Ticket urgency_level cannot be negative",
            )

        if self.user_ticket_id < 0:
            raise DomainOperationError(
                "Ticket user_ticket_id cannot be negative",
            )

    def _validate_content(self) -> None:
        if not self.text_of_ticket:
            raise DomainOperationError(
                "Ticket text_of_ticket cannot be empty",
            )

    def _validate_status_history(self) -> None:
        """
        Проверяет persisted и вновь созданную workflow history.

        Проверяется:
        - наличие первой записи;
        - допустимость первого состояния;
        - каждый переход между соседними records;
        - context-dependent payload перехода.
        """
        if not self.statuses:
            raise DomainOperationError(
                "Ticket must have status history",
            )

        first_record = self.statuses[0]

        if not first_record.is_first_status():
            raise DomainOperationError(
                "Ticket cannot start with status "
                f"{first_record.status.value}",
            )

        for index in range(1, len(self.statuses)):
            previous_record = self.statuses[index - 1]
            current_record = self.statuses[index]

            if not previous_record.can_move_to_next_record(
                current_record,
            ):
                raise DomainOperationError(
                    "Invalid Ticket status history: "
                    f"{previous_record.status.value} -> "
                    f"{current_record.status.value}",
                )

            previous_record.validate_review_transition(
                current_record,
            )

    def _validate_creator_admin(self) -> None:
        """
        Проверяет согласованность admin_id
        с происхождением Ticket.

        admin_id хранит только Admin,
        создавшего внутреннюю Ticket.

        Поэтому он всегда должен совпадать
        с actor_employee_id первой status-record:

        CREATED:
            actor_employee_id > 0
            admin_id > 0

        CREATED_FROM_TICKET_USER:
            actor_employee_id == 0
            admin_id == 0
        """
        first_record = self.statuses[0]

        if self.admin_id != first_record.actor_employee_id:
            raise DomainOperationError(
                f"Ticket admin_id {self.admin_id} "
                "does not match creator in first status record "
                f"{first_record.actor_employee_id}",
            )

    # ----------------------------
    # Derived state
    # ----------------------------

    def _recompute_closed_state(self) -> None:
        """
        is_closed и date_finished полностью выводятся
        из текущей status-record.
        """
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
        Суммарное фактическое рабочее время в секундах.

        Онлайн-работа:
            record содержит actual_started_at,
            но не содержит actual_finished_at.

            Интервал заканчивается временем следующей
            status-record либо текущим временем.

        Ретроспективная работа:
            record содержит одновременно
            actual_started_at и actual_finished_at.

        READY_FOR_REVIEW после обычного AT_WORK содержит
        только actual_finished_at и отдельно не считается:
        соответствующий интервал уже учтён через AT_WORK.
        """
        total_seconds = 0

        for index, record in enumerate(self.statuses):
            if (
                record.has_actual_started()
                and not record.has_actual_finished()
            ):
                next_record = (
                    self.statuses[index + 1]
                    if index + 1 < len(self.statuses)
                    else None
                )

                finish_at = (
                    next_record.date_created
                    if next_record is not None
                    else datetime.now(UTC)
                )

                total_seconds += self._seconds_between(
                    record.date_created,
                    finish_at,
                )

            elif (
                record.has_actual_started()
                and record.has_actual_finished()
            ):
                total_seconds += self._seconds_between(
                    record.actual_started_at,
                    record.actual_finished_at,
                )

        return total_seconds

    # ----------------------------
    # References
    # ----------------------------

    def belong(
        self,
        employee_id: int,
    ) -> bool:
        """
        Проверяет, упоминается ли employee в Ticket.

        Это не permission check.
        """
        if employee_id <= 0:
            return False

        if employee_id == self.admin_id:
            return True

        for comment in self.comments:
            if comment.employee_id == employee_id:
                return True

        for record in self.statuses:
            if record.actor_employee_id == employee_id:
                return True

            if record.executor_id == employee_id:
                return True

        return False

    def is_in_work(self) -> bool:
        return self.current_status_record().state.work_in_progress

    # ----------------------------
    # Helpers
    # ----------------------------

    @staticmethod
    def _seconds_between(
        start: datetime,
        finish: datetime,
    ) -> int:
        return int(
            (finish - start).total_seconds()
        )