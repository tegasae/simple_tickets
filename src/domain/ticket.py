# src/domain/ticket.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Self

from src.domain.exceptions import DomainOperationError
from src.domain.ticket_components import Comment, ExecutorAssignment


class TicketStatus(Enum):
    """
    Admin-side ticket workflow statuses.
    NOTE: Pick one spelling and use it everywhere: CANCELLED (UK) or CANCELED (US).
    """
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


@dataclass(frozen=True, kw_only=True)
class TicketStatusRecord:
    """
    Immutable record of a status change.
    Stores who changed it (admin/manager/executor) and when.
    """
    actor_employee_id: int
    status: TicketStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __eq__(self, other: Any) -> bool:
        # Equality by status only (optional; remove if you don't need it).
        return isinstance(other, TicketStatusRecord) and self.status == other.status


@dataclass(kw_only=True)
class Ticket:
    """
    Admin-created (or admin-owned) Ticket aggregate.

    Invariants:
      - Initial status is CREATED
      - Status changes must follow TicketStatus.can_transition
      - EXECUTED/CANCELLED are terminal -> ticket becomes closed, finished_at is set
      - version increments on every state change (optimistic locking)
    """
    ticket_id: int
    client_id: int
    admin_id: int
    description: str

    text_of_ticket: str = ""
    user_id:int=0
    contact_user_id:int=0



    statuses: list[TicketStatusRecord] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    executors: list[ExecutorAssignment] = field(default_factory=list)

    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_remote:bool=False
    is_closed: bool = False
    date_finished: Optional[datetime] = None
    version: int = 0
    urgency_level: int = 0
    user_ticket_id: int = 0
    def __post_init__(self) -> None:
        # Ensure initial status exists
        if not self.statuses:
            self.statuses.append(
                TicketStatusRecord(status=TicketStatus.CREATED, actor_employee_id=self.admin_id)
            )

        # Recompute closure from status history (robust when rehydrating from storage)
        current = self.current_status()
        if current in (TicketStatus.EXECUTED, TicketStatus.CANCELLED):
            self.is_closed = True
            if self.date_finished is None:
                # If not stored, infer at least "now" (or use last record time if preferred)
                self.date_finished = self.statuses[-1].created_at
        else:
            self.is_closed = False

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
    # Commands (business methods)
    # ----------------------------

    def change_status(self, new_status: TicketStatus, actor_employee_id: int) -> None:
        if self.is_closed:
            raise DomainOperationError("Ticket is closed; status cannot be changed")

        cur = self.current_status()
        if not TicketStatus.can_transition(cur, new_status):
            raise DomainOperationError(f"Cannot change status from {cur.value} to {new_status.value}")

        self.statuses.append(TicketStatusRecord(status=new_status, actor_employee_id=actor_employee_id))
        self.version += 1

        if new_status in (TicketStatus.EXECUTED, TicketStatus.CANCELLED):
            self.is_closed = True
            self.date_finished = datetime.now(timezone.utc)

    def add_comment(self, comment: Comment) -> None:
        if self.is_closed:
            raise DomainOperationError("Ticket is closed; cannot add comments")
        self.comments.append(comment)
        self.version += 1

    def add_executor(self, assignment: ExecutorAssignment) -> None:
        if self.is_closed:
            raise DomainOperationError("Ticket is closed; cannot assign executors")
        self.executors.append(assignment)
        self.version += 1

    def defer(self, actor_employee_id: int) -> None:
        """Convenience method."""
        self.change_status(TicketStatus.DEFERRED, actor_employee_id)

    def start_work(self, actor_employee_id: int) -> None:
        """Convenience method."""
        self.change_status(TicketStatus.AT_WORK, actor_employee_id)

    def execute(self, actor_employee_id: int) -> None:
        """Convenience method."""
        self.change_status(TicketStatus.EXECUTED, actor_employee_id)

    def cancel(self, actor_employee_id: int) -> None:
        """Convenience method."""
        self.change_status(TicketStatus.CANCELLED, actor_employee_id)
