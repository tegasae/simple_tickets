from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Self

from src.domain.exceptions import DomainOperationError

from src.domain.policy.ticket_workflow_policy import TicketWorkflowPolicy
from src.domain.statuses.ticket_status import TicketStatus, TERMINAL_TICKET_STATUSES
from src.domain.statuses.ticket_status_record import StatusRecordTicket
from src.domain.statuses.ticket_status_record_factory import TicketStatusRecordFactory
from src.domain.ticket_components import Comment


@dataclass(kw_only=True)
class Ticket:
    """
    Ticket aggregate.

    Responsibilities:
    - store ticket data;
    - store status history;
    - store plain comments;
    - compute current status and current executor from history;
    - protect local invariants.

    Not responsible for:
    - actor permissions;
    - department rules;
    - executor-department compatibility;
    - concrete workflow use cases.

    Workflow operations should live in TicketWorkflowService.
    """

    ticket_id: int
    client_id: int
    admin_id: int

    text_of_ticket: str = ""
    user_id: int = 0
    contact_user_id: int = 0

    statuses: list[StatusRecordTicket] = field(default_factory=list)
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
        statuses: list[StatusRecordTicket],
        comments: list[Comment] | None = None,
        date_created: datetime,
        is_remote: bool = False,
        is_closed: bool = False,
        date_finished: datetime | None = None,
        version: int = 0,
        urgency_level: int = 0,
        user_ticket_id: int = 0,
    ) -> Self:
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

    def current_status_record(self) -> StatusRecordTicket:
        if not self.statuses:
            raise DomainOperationError("Ticket has no status history")

        return self.statuses[-1]

    def current_executor_id(self) -> int:
        """
        Returns current responsible executor.

        0 means: no current executor.

        Source of truth:
        last status record with executor_id > 0.
        """
        for record in reversed(self.statuses):
            if record.executor_id > 0:
                return record.executor_id

        return 0

    def has_executor(self) -> bool:
        return self.current_executor_id() > 0

    def is_terminal(self) -> bool:
        return self.current_status() in TERMINAL_TICKET_STATUSES

    def new_statuses(self) -> list[StatusRecordTicket]:
        return [
            status
            for status in self.statuses
            if status.status_id == 0
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

    def append_status(self, record: StatusRecordTicket) -> None:
        """
        Adds new status record to ticket history.

        This method checks only local invariants:
        - ticket is not terminal;
        - transition is allowed by workflow graph.

        It does not check:
        - actor permissions;
        - department rules;
        - executor availability;
        - executor belongs to ticket department.
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
        Adds plain ticket comment.

        Comment is not a workflow status comment.
        Status-related comments are stored inside StatusRecordTicket.comment.
        """
        self._ensure_not_terminal()
        self.comments.append(comment)

    # ----------------------------
    # Internal helpers
    # ----------------------------

    def _ensure_not_terminal(self) -> None:
        if self.is_terminal():
            raise DomainOperationError(
                f"The ticket {self.ticket_id} is in terminal status {self.current_status()}"
            )

    def _recompute_closed_state(self) -> None:
        if not self.statuses:
            self.is_closed = False
            self.date_finished = None
            return

        current = self.current_status()

        if current in TERMINAL_TICKET_STATUSES:
            self.is_closed = True

            if self.date_finished is None:
                self.date_finished = self.current_status_record().date_created
        else:
            self.is_closed = False
            self.date_finished = None

    # ----------------------------
    # Analytics
    # ----------------------------

    def working_time(self) -> int:
        """
        Returns total working time in seconds.

        Counts only periods where status was AT_WORK.

        AT_WORK interval:
        - starts at AT_WORK record date_created;
        - ends at next status record date_created;
        - if AT_WORK is current status, ends at now.
        """
        if len(self.statuses) <= 1:
            return 0

        total_seconds = 0

        for current_record, next_record in zip(self.statuses, self.statuses[1:]):
            if current_record.status == TicketStatus.AT_WORK:
                delta = next_record.date_created - current_record.date_created
                total_seconds += int(delta.total_seconds())

        if self.current_status() == TicketStatus.AT_WORK:
            delta = datetime.now(timezone.utc) - self.current_status_record().date_created
            total_seconds += int(delta.total_seconds())

        return total_seconds

    def belong(self, employee_id: int) -> bool:
        """
        Checks whether employee is mentioned in ticket history.

        Note:
        This method is only a historical/reference check.
        It should not be used for permission decisions.
        """
        if employee_id == self.admin_id:
            return True

        for comment in self.comments:
            if employee_id == comment.employee_id:
                return True

        for status in self.statuses:
            if employee_id == status.actor_employee_id:
                return True

            if status.executor_id == employee_id:
                return True

        return False