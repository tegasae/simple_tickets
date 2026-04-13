from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Self

from src.domain.exceptions import DomainOperationError
from src.domain.ticket_components import Comment, ExecutorAssignment


class TicketStatus(Enum):
    CREATED = "created"
    AT_WORK = "at_work"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"

    @classmethod
    def can_transition(cls, from_status: Self, to_status: Self) -> bool:
        transitions = {
            cls.CREATED: [cls.AT_WORK, cls.CANCELLED, cls.DEFERRED],
            cls.AT_WORK: [cls.EXECUTED, cls.CANCELLED, cls.DEFERRED],
            cls.DEFERRED: [cls.AT_WORK, cls.CANCELLED],
            cls.EXECUTED: [],
            cls.CANCELLED: [],
        }
        return to_status in transitions.get(from_status, [])


@dataclass(kw_only=True)
class TicketStatusRecord:
    status_id: int=0
    actor_employee_id: int
    status: TicketStatus
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, TicketStatusRecord) and self.status == other.status


@dataclass(kw_only=True)
class Ticket:
    """
    Ticket aggregate.

    Important:
    - __post_init__ does NOT create CREATED automatically anymore.
    - CREATED is added only by Ticket.create(...).
    - Repository may rehydrate with full history safely.
    """
    ticket_id: int
    client_id: int
    admin_id: int
    description: str

    text_of_ticket: str = ""
    user_id: int = 0
    contact_user_id: int = 0

    statuses: list[TicketStatusRecord] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    executors: list[ExecutorAssignment] = field(default_factory=list)

    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_remote: bool = False
    is_closed: bool = False
    date_finished: Optional[datetime] = None
    version: int = 0
    urgency_level: int = 0
    user_ticket_id: int = 0

    def __post_init__(self) -> None:
        """
        Only normalize / recompute state from loaded fields.
        Do NOT create history entries here.
        """
        if not self.statuses:
            self.statuses.append(
                TicketStatusRecord(
                    actor_employee_id=self.user_id,
                    status=TicketStatus.CREATED,
                )
            )

        current = self.current_status()

        if current in (TicketStatus.EXECUTED, TicketStatus.CANCELLED):
            self.is_closed = True
            if self.date_finished is None:
                self.date_finished = self.statuses[-1].date_created
            else:
                self.is_closed = False

    @classmethod
    def create(
        cls,
        *,
        ticket_id: int,
        client_id: int,
        admin_id: int,
        description: str,
        text_of_ticket: str = "",
        user_id: int = 0,
        contact_user_id: int = 0,
        is_remote: bool = False,
        urgency_level: int = 0,
        user_ticket_id: int = 0,
        executor_id:int=0,
        comment:str=""
    ) -> Self:
        ticket = cls(
            ticket_id=ticket_id,
            client_id=client_id,
            admin_id=admin_id,
            description=description,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=contact_user_id,
            is_remote=is_remote,
            urgency_level=urgency_level,
            user_ticket_id=user_ticket_id,
        )
        ticket.statuses.append(
            TicketStatusRecord(
                status=TicketStatus.CREATED,
                actor_employee_id=admin_id,
            )
        )

        if executor_id:
            ticket.add_executor(ExecutorAssignment(executor_id=executor_id, admin_id=admin_id))

        if comment:
            ticket.add_comment(comment=Comment(employee_id=admin_id, comment=comment))

        return ticket

    # ----------------------------
    # Queries
    # ----------------------------

    def current_status(self) -> TicketStatus:
        if not self.statuses:
            raise DomainOperationError("Ticket has no status history")
        return self.statuses[-1].status

    def current_executor(self) -> ExecutorAssignment:
        try:
            return self.executors[-1]
        except IndexError:
            raise DomainOperationError("No executor available")

    # ----------------------------
    # Commands
    # ----------------------------

    def change_status(self, new_status: TicketStatus, actor_employee_id: int) -> None:
        if self.is_closed:
            raise DomainOperationError("Ticket is closed; status cannot be changed")

        cur = self.current_status()
        if not TicketStatus.can_transition(cur, new_status):
            raise DomainOperationError(
                f"Cannot change status from {cur.value} to {new_status.value}"
            )

        self.statuses.append(
            TicketStatusRecord(
                status=new_status,
                actor_employee_id=actor_employee_id,
            )
        )


        if new_status in (TicketStatus.EXECUTED, TicketStatus.CANCELLED):
            self.is_closed = True
            self.date_finished = datetime.now(timezone.utc)

    def add_comment(self, comment: Comment) -> None:
        if self.is_closed:
            raise DomainOperationError("Ticket is closed; cannot add comments")
        self.comments.append(comment)


    def add_executor(self, assignment: ExecutorAssignment) -> None:
        if self.is_closed:
            raise DomainOperationError("Ticket is closed; cannot assign executors")
        self.executors.append(assignment)


    def defer(self, actor_employee_id: int) -> None:
        self.change_status(TicketStatus.DEFERRED, actor_employee_id)

    def start_work(self, actor_employee_id: int) -> None:
        self.change_status(TicketStatus.AT_WORK, actor_employee_id)

    def execute(self, actor_employee_id: int) -> None:
        self.change_status(TicketStatus.EXECUTED, actor_employee_id)

    def cancel(self, actor_employee_id: int,comment:str) -> None:
        self.change_status(TicketStatus.CANCELLED, actor_employee_id)

    def belong(self,employee_id: int) -> bool:
        if employee_id==self.admin_id:
            return True
        for comment in self.comments:
            if employee_id==comment.employee_id:
                return True
        for status in self.statuses:
            if employee_id==status.actor_employee_id:
                return True

        for executor in self.executors:
            if employee_id==executor.executor_id:
                return True
        return False
