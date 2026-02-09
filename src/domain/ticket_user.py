# ============================
# src/domain/ticket_user.py
# Client-side ticket aggregate using shared components
# ============================
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Self


from src.domain.ticket_components import StatusHistory, Comment, ExecutorAssignment, CommentThread, ExecutorAssignments




class ClientTicketStatus(Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    AT_WORK = "at_work"
    EXECUTED = "executed"
    CANCELED_BY_ADMIN = "canceled_by_admin"
    CANCELED_BY_CLIENT = "canceled_by_client"

    @classmethod
    def can_transition(cls, from_status: Self, to_status: Self) -> bool:
        transitions = {
            cls.CREATED: [cls.CONFIRMED, cls.AT_WORK, cls.CANCELED_BY_CLIENT, cls.CANCELED_BY_ADMIN],
            cls.CONFIRMED: [cls.AT_WORK, cls.CANCELED_BY_CLIENT, cls.CANCELED_BY_ADMIN],
            cls.AT_WORK: [cls.EXECUTED, cls.CANCELED_BY_ADMIN],
            cls.EXECUTED: [],
            cls.CANCELED_BY_CLIENT: [],
            cls.CANCELED_BY_ADMIN: [],
        }
        return to_status in transitions.get(from_status, [])


@dataclass(frozen=True, kw_only=True)
class ClientTicketStatusRecord:
    actor_employee_id: int
    status: ClientTicketStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ClientTicketStatusRecord) and self.status == other.status


# ✅ FIX: positional factory (no "*", no keyword-only parameters)
def make_client_record(status: ClientTicketStatus, actor_id: int) -> ClientTicketStatusRecord:
    return ClientTicketStatusRecord(status=status, actor_employee_id=actor_id)







@dataclass(kw_only=True)
class TicketUser:
    """
    Client-owned ticket aggregate.
    Note: roles/permissions checks should live in application services, not here.
    """
    ticket_id: int
    client_id: int
    user_id: int  # employee who created the ticket (client-side actor)
    description: str

    status_history: StatusHistory[ClientTicketStatus, ClientTicketStatusRecord] = field(
        default_factory=lambda: StatusHistory(
            can_transition=ClientTicketStatus.can_transition,
            get_status=lambda r: r.status,
            make_record=make_client_record,  # ✅ matches Callable[[S, int], R]
        )
    )

    comments: CommentThread = field(default_factory=CommentThread)
    executors: ExecutorAssignments = field(default_factory=ExecutorAssignments)

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 0


    def __post_init__(self) -> None:
        self.status_history.ensure_initialized(initial_status=ClientTicketStatus.CREATED, actor_id=self.user_id)

    def change_status(self, new_status: ClientTicketStatus, actor_employee_id: int) -> None:
        self.status_history.change(new_status=new_status, actor_id=actor_employee_id)
        self.version += 1

    def current_status(self) -> ClientTicketStatus:
        return self.status_history.current()

    @classmethod
    def create(
        cls,
        *,
        ticket_id: int,
        client_id: int,
        user_id: int,
        description: str,
        initial_comment: str | None = None,
        initial_executor_admin_id: int | None = None,
    ) -> Self:
        ticket = cls(ticket_id=ticket_id, client_id=client_id, user_id=user_id, description=description)

        if initial_comment:
            ticket.add_comment(Comment(employee_id=user_id, comment=initial_comment))

        if initial_executor_admin_id is not None:
            ticket.add_executor(ExecutorAssignment(admin_id=initial_executor_admin_id))

        return ticket


    def add_comment(self, comment: Comment) -> None:
        self.comments.add(comment)
        self.version += 1

    def add_executor(self, assignment: ExecutorAssignment) -> None:
        self.executors.add(assignment)
        self.version += 1


    def current_executor(self) -> ExecutorAssignment:
        return self.executors.current()
