# src/domain/ticket_user.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Self

from src.domain.exceptions import DomainOperationError
from src.domain.ticket_components import Comment, ExecutorAssignment


class StatusTicketOfClient(Enum):
    """
    Client-side ticket workflow statuses.

    NOTE: Your current choice (CANCELED_BY_*) is OK.
    Just be consistent with spelling across the project.
    """
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
class StatusRecordTicketUser:
    """
    Immutable record of a TicketUser status change.
    actor_employee_id: who changed status (employee or admin).
    """
    actor_employee_id: int
    status: StatusTicketOfClient
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __eq__(self, other: Any) -> bool:
        # Equality by status only (optional; remove if you don't need it).
        return isinstance(other, StatusRecordTicketUser) and self.status == other.status


@dataclass(kw_only=True)
class TicketUser:
    """
    Employee-created (client-side) TicketUser aggregate.

    Invariants:
      - Initial status is CREATED (by user_id)
      - Status changes must follow StatusTicketOfClient.can_transition
      - Terminal statuses close the ticket (EXECUTED, CANCELED_BY_CLIENT, CANCELED_BY_ADMIN)
      - version increments on every change (optimistic locking)
    """
    ticket_id: int
    client_id: int
    user_id: int
    description: str

    # User-only fields you mentioned
    created_by_client: bool = False


    # Optional cross-link for future transformation (can be unused now)
    0

    statuses: list[StatusRecordTicketUser] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    executors: list[ExecutorAssignment] = field(default_factory=list)

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_closed: bool = False
    finished_at: Optional[datetime] = None
    version: int = 0

    def __post_init__(self) -> None:
        # Ensure initial status exists
        if not self.statuses:
            self.statuses.append(
                StatusRecordTicketUser(status=StatusTicketOfClient.CREATED, actor_employee_id=self.user_id)
            )

        # Recompute closure from status history (robust when rehydrating from storage)
        current = self.current_status()
        if current in (StatusTicketOfClient.EXECUTED,
                       StatusTicketOfClient.CANCELED_BY_ADMIN,
                       StatusTicketOfClient.CANCELED_BY_CLIENT):
            self.is_closed = True
            if self.finished_at is None:
                self.finished_at = self.statuses[-1].created_at
        else:
            self.is_closed = False

    # ----------------------------
    # Queries
    # ----------------------------

    def current_status(self) -> StatusTicketOfClient:
        if not self.statuses:
            raise DomainOperationError("TicketUser has no status history")
        return self.statuses[-1].status

    def current_executor(self) -> ExecutorAssignment:
        try:
            return self.executors[-1]
        except IndexError:
            raise DomainOperationError("No executor available")

    # ----------------------------
    # Commands (business methods)
    # ----------------------------

    def change_status(self, new_status: StatusTicketOfClient, actor_employee_id: int) -> None:
        if self.is_closed:
            raise DomainOperationError("TicketUser is closed; status cannot be changed")

        cur = self.current_status()
        if not StatusTicketOfClient.can_transition(cur, new_status):
            raise DomainOperationError(f"Cannot change status from {cur.value} to {new_status.value}")

        self.statuses.append(StatusRecordTicketUser(status=new_status, actor_employee_id=actor_employee_id))
        self.version += 1

        if new_status in (
            StatusTicketOfClient.EXECUTED,
            StatusTicketOfClient.CANCELED_BY_ADMIN,
            StatusTicketOfClient.CANCELED_BY_CLIENT,
        ):
            self.is_closed = True
            self.finished_at = datetime.now(timezone.utc)

    def add_comment(self, comment: Comment) -> None:
        if self.is_closed:
            raise DomainOperationError("TicketUser is closed; cannot add comments")
        self.comments.append(comment)
        self.version += 1

    def add_executor(self, assignment: ExecutorAssignment) -> None:
        if self.is_closed:
            raise DomainOperationError("TicketUser is closed; cannot assign executors")
        self.executors.append(assignment)
        self.version += 1

    # Convenience methods (optional)

    def confirm(self, actor_employee_id: int) -> None:
        self.change_status(StatusTicketOfClient.CONFIRMED, actor_employee_id)

    def start_work(self, actor_employee_id: int) -> None:
        self.change_status(StatusTicketOfClient.AT_WORK, actor_employee_id)

    def execute(self, actor_employee_id: int) -> None:
        self.change_status(StatusTicketOfClient.EXECUTED, actor_employee_id)

    def cancel_by_client(self, actor_employee_id: int) -> None:
        self.change_status(StatusTicketOfClient.CANCELED_BY_CLIENT, actor_employee_id)

    def cancel_by_admin(self, actor_employee_id: int) -> None:
        self.change_status(StatusTicketOfClient.CANCELED_BY_ADMIN, actor_employee_id)
