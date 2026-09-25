# src/domain/ticket.py

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self



from src.domain.exceptions import (
    DomainOperationError,
    ItemValidationError,
)
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.statuses.ticket_status_transitions import TERMINAL_TICKET_STATUSES, EXECUTOR_ACTIVE_STATUSES
from src.domain.ticket_components import Comment
from src.domain.value_objects import CommonComment


from enum import StrEnum


class TicketUrgency(StrEnum):
    NORMAL = "normal"
    URGENT = "urgent"
    MAINTENANCE = "maintenance"

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



    text_of_ticket: str
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

    planned_at: datetime | None = None

    department_id: int = 0
    remote_work_recommended: bool =False

    version: int = 0
    urgency: TicketUrgency = TicketUrgency.NORMAL
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

    """
    class Ticket:

    # Factories
    #create(...)
    #create_from_ticket_user(...)
    #rehydrate(...)

    # Current state
    #current_status_record()
    #current_status()
    #is_terminal()

    # Executor
    #current_executor_id()
    executor_id_at(status_index)

    # Persistence helpers
    is_new()
    new_statuses()
    new_comments()

    # Workflow
    append_status(record)

    # Ticket data
    add_comment(comment)
    change_department(department_id)
    change_contact_user(contact_user_id)
    update_description(description)
    set_remote_work_recommended(value)
    change_urgency(urgency)

    # Planning
    schedule(planned_at)
    clear_schedule()

    # Analytics
    working_time()

    # Internal validation
    _validate_identity()
    _validate_content()
    _validate_status_history()
    _validate_creator()

    # Derived state
    _recompute_closed_state()
    
    
    """

    # ----------------------------
    # Factories
    # ----------------------------

    @staticmethod
    def _resolve_contact_user_id(
            *,
            user_id: int,
            contact_user_id: int,
    ) -> int:
        """
        Resolve the contact User for a new Ticket.

        If contact_user_id is not specified, user_id is used.
        If both values are zero, the Ticket has no contact User.
        """

        if contact_user_id < 0:
            raise ItemValidationError(
                "Contact user id cannot be negative"
            )

        return (
            contact_user_id
            if contact_user_id > 0
            else user_id
        )

    @classmethod
    def _create_new(
            cls,
            *,
            client_id: int,
            text_of_ticket: str,
            initial_status: TicketStatus,
            actor_employee_id: int,
            user_id: int = 0,
            contact_user_id: int = 0,
            user_ticket_id: int = 0,
            department_id: int = 0,
            description: str = "",
            remote_work_recommended: bool = False,
            urgency: TicketUrgency = TicketUrgency.NORMAL,
            planned_at: datetime | None = None,
            comment: str = "",
            date_created: datetime | None = None,
    ) -> Self:
        """
        Common factory implementation for a new Ticket.

        Public factories define the business scenario and provide:

        - initial_status;
        - actor_employee_id.

        This method performs only common Ticket construction.
        """

        now = date_created or datetime.now(UTC)

        resolved_contact_user_id = cls._resolve_contact_user_id(
            user_id=user_id,
            contact_user_id=contact_user_id,
        )

        ticket = cls(
            ticket_id=0,
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=resolved_contact_user_id,
            user_ticket_id=user_ticket_id,
            department_id=department_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            date_created=now,
            version=0,
            statuses=[
                TicketStatusRecord(
                    status=initial_status,
                    actor_employee_id=actor_employee_id,
                    date_created=now,
                ),
            ],
        )

        if comment.strip():
            ticket.add_comment(
                Comment(
                    employee_id=actor_employee_id,
                    comment=CommonComment(comment),
                    date_created=now,
                )
            )

        return ticket

    @classmethod
    def create(
            cls,
            *,
            client_id: int,
            admin_id: int,
            text_of_ticket: str,
            user_id: int = 0,
            contact_user_id: int = 0,
            department_id: int = 0,
            user_ticket_id: int = 0,
            description: str = "",
            remote_work_recommended: bool = False,
            urgency: TicketUrgency = TicketUrgency.NORMAL,
            planned_at: datetime | None = None,
            comment: str = "",
            date_created: datetime | None = None,
    ) -> Self:
        """
        Create a new internal Ticket by an Admin.

        The first workflow record is CREATED.

        admin_id is not stored as a separate Ticket field.
        The Admin who created the Ticket is recorded as
        actor_employee_id of the CREATED status record.

        text_of_ticket is required and cannot be changed after creation.
        """

        if admin_id <= 0:
            raise ItemValidationError(
                "Admin id must be positive"
            )

        return cls._create_new(
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            initial_status=TicketStatus.CREATED,
            actor_employee_id=admin_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            user_ticket_id=user_ticket_id,
            department_id=department_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            comment=comment,
            date_created=date_created,
        )

    @classmethod
    def create_from_ticket_user(
            cls,
            *,
            client_id: int,
            user_id: int,
            user_ticket_id: int,
            text_of_ticket: str,
            contact_user_id: int = 0,
            description: str = "",
            department_id: int = 0,
            remote_work_recommended: bool = False,
            urgency: TicketUrgency = TicketUrgency.NORMAL,
            planned_at: datetime | None = None,
            comment: str = "",
            date_created: datetime | None = None,
    ) -> Self:
        """
        Create an internal Ticket from a TicketUser.

        Ticket and TicketUser remain independent aggregates.
        Their creation and linking are coordinated by the application layer.

        The first workflow record is CREATED_FROM_TICKET_USER.

        The User who created the corresponding TicketUser is recorded as
        actor_employee_id of the first status record.

        If contact_user_id is not specified, user_id is used as the
        contact User.
        """

        if user_id <= 0:
            raise ItemValidationError(
                "User id must be positive"
            )

        if user_ticket_id <= 0:
            raise ItemValidationError(
                "User ticket id must be positive"
            )

        return cls._create_new(
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            initial_status=TicketStatus.CREATED_FROM_TICKET_USER,
            actor_employee_id=user_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            user_ticket_id=user_ticket_id,
            department_id=department_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            comment=comment,
            date_created=date_created,
        )

    @classmethod
    def rehydrate(
            cls,
            *,
            ticket_id: int,
            client_id: int,
            text_of_ticket: str,
            statuses: list[TicketStatusRecord],
            date_created: datetime,
            user_id: int = 0,
            contact_user_id: int = 0,
            comments: list[Comment] | None = None,
            department_id: int = 0,
            user_ticket_id: int = 0,
            description: str = "",
            remote_work_recommended: bool = False,
            urgency: TicketUrgency = TicketUrgency.NORMAL,
            planned_at: datetime | None = None,
            version: int = 0,
    ) -> Self:
        """
        Rehydrate a persisted Ticket.

        Repository must provide:

        - persisted ticket_id > 0;
        - complete status history;
        - status history in persistence order.

        Creator information is restored from the first status record.

        Unlike the creation factories, rehydrate does not resolve or
        normalize contact_user_id. Persisted domain state is restored
        exactly as stored and then validated by the aggregate.

        is_closed and date_finished are not loaded as independent domain
        state because they are derived from status history.
        """

        if ticket_id <= 0:
            raise DomainOperationError(
                "Cannot rehydrate Ticket with non-positive ticket_id"
            )

        if not statuses:
            raise DomainOperationError(
                "Cannot rehydrate Ticket without status history"
            )

        return cls(
            ticket_id=ticket_id,
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=contact_user_id,
            statuses=statuses,
            comments=comments if comments is not None else [],
            date_created=date_created,
            department_id=department_id,
            user_ticket_id=user_ticket_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            version=version,
        )

    # ----------------------------
    # Current state
    # ----------------------------

    def current_status_record(self) -> TicketStatusRecord:
        """
        Return the current Ticket status record.

        The current state of the Ticket is always defined by the last
        record in the complete status history.
        """

        if not self.statuses:
            raise DomainOperationError(
                "Ticket has no status history"
            )

        return self.statuses[-1]

    def current_status(self) -> TicketStatus:
        """
        Return the current Ticket status.
        """

        return self.current_status_record().status

    def is_terminal(self) -> bool:
        """
        Return True if the Ticket is in a terminal state.
        """

        return self.current_status() in TERMINAL_TICKET_STATUSES

    # Executor
    def current_executor_id(self) -> int:
        """
        Return the currently assigned executor.

        The executor is considered active only while Ticket is in one of:

        - ASSIGNED
        - AT_WORK
        - PAUSED
        - READY_FOR_REVIEW

        ACCEPTED, DEFERRED and SUSPENDED clear the assignment.
        Terminal statuses do not have a current executor.

        The executor is resolved from the nearest preceding ASSIGNED
        status record.
        """

        if self.current_status() not in EXECUTOR_ACTIVE_STATUSES:
            return 0

        for record in reversed(self.statuses):
            if record.status == TicketStatus.ASSIGNED:
                return record.executor_id

        raise DomainOperationError(
            "Ticket is in executor-active status "
            "but has no preceding ASSIGNED record"
        )


    # ----------------------------
    # Queries
    # ----------------------------

    def is_new(self) -> bool:
        return self.ticket_id == 0



    def has_executor(self) -> bool:
        return self.current_executor_id() > 0


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