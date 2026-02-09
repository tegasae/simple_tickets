# ============================
# src/domain/ticket.py
# Admin/manager-side ticket aggregate using shared components
# ============================
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Self

from src.domain.exceptions import DomainOperationError
from src.domain.ticket_components import StatusHistory, Comment, ExecutorAssignment, CommentThread


########
# ============================
# src/domain/ticket.py
# Admin/manager-side ticket aggregate using StatusHistory (positional factory)
# ============================





class AdminTicketStatus(Enum):
    """Ticket status for admin/manager workflow."""
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
class AdminTicketStatusRecord:
    """Immutable record of an admin ticket status change."""
    actor_admin_id: int
    status: AdminTicketStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, AdminTicketStatusRecord) and self.status == other.status


# ✅ positional factory (matches Callable[[S, int], R])
def make_admin_record(status: AdminTicketStatus, actor_id: int) -> AdminTicketStatusRecord:
    return AdminTicketStatusRecord(status=status, actor_admin_id=actor_id)



@dataclass(kw_only=True)
class Ticket:
    """
        Admin/manager-side ticket aggregate.

        Note:
          - Authorization checks (RBAC) should be done in application services.
          - This aggregate enforces domain invariants and state transitions.
        """
    ticket_id: int
    client_id: int
    manager_admin_id: int
    description: str

    # Optional fields you had
    text_of_ticket: str = ""
    created_by_client: bool = False

    # Components
    status_history: StatusHistory[AdminTicketStatus, AdminTicketStatusRecord] = field(
        default_factory=lambda: StatusHistory(
            can_transition=AdminTicketStatus.can_transition,
            get_status=lambda r: r.status,
            make_record=make_admin_record,
        )
    )
    comments: CommentThread = field(default_factory=CommentThread)
    executors: list[ExecutorAssignment] = field(default_factory=list)

    # Lifecycle / tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_closed: bool = False
    finished_at: Optional[datetime] = None
    version: int = 0

    def __post_init__(self) -> None:
        self.status_history.ensure_initialized(
            initial_status=AdminTicketStatus.CREATED,
            actor_id=self.manager_admin_id,
        )

    def change_status(self, new_status: AdminTicketStatus, actor_admin_id: int) -> None:
        self.status_history.change(new_status=new_status, actor_id=actor_admin_id)
        self.version += 1

        # Optional rule: close on terminal states
        if new_status in (AdminTicketStatus.EXECUTED, AdminTicketStatus.CANCELLED):
            self.is_closed = True
            self.finished_at = datetime.now(timezone.utc)

    def current_status(self) -> AdminTicketStatus:
        return self.status_history.current()

    def add_comment(self, comment: Comment) -> None:
        self.comments.add(comment)
        self.version += 1

    def add_executor(self, assignment: ExecutorAssignment) -> None:
        self.executors.append(assignment)
        self.version += 1

    def current_executor(self) -> ExecutorAssignment:
        try:
            return self.executors[-1]
        except IndexError:
            raise DomainOperationError("No executor available")


