# ============================
# src/domain/ticket_components.py
# Shared components (composition, not inheritance)
# ============================
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from typing import Generic, Protocol, TypeVar, List, Set

from src.domain.exceptions import DomainOperationError



S = TypeVar("S")  # status enum type
R = TypeVar("R")  # status record type




@dataclass(frozen=True, kw_only=True)
class Comment:
    employee_id: int
    comment: str
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, kw_only=True)
class ExecutorAssignment:
    """
    Executor assignment uses an admin id in your model.
    Naming it explicitly reduces confusion between 'employee' and 'admin'.
    """
    admin_id: int
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))





class TransitionPolicy(Protocol[S]):
    def can_transition(self, from_status: S, to_status: S) -> bool: ...


class RecordFactory(Protocol[S, R]):
    def __call__(self, *, status: S, actor_id: int) -> R: ...

class StatusGetter(Protocol[R, S]):
    def __call__(self, record: R) -> S: ...

@dataclass
class StatusHistory(Generic[S, R]):
    """
         Status history with explicit interfaces (Protocol-based).

         You inject:
           - transition_policy: TransitionPolicy[S]
           - record_factory: RecordFactory[S, R]  (keyword-only)
           - get_status: StatusGetter[R, S]

         This is clear and explicit (strongly-typed style). """

    transition_policy: TransitionPolicy[S]
    record_factory: RecordFactory[S, R]
    get_status: StatusGetter[R, S]

    records: List[R] = field(default_factory=list)

    def ensure_initialized(self, *, initial_status: S, actor_id: int) -> None:
        if not self.records:
            self.records.append(self.record_factory(status=initial_status, actor_id=actor_id))

    def current(self) -> S:
        if not self.records:
            raise DomainOperationError("Status history is empty")
        return self.get_status(self.records[-1])

    def change(self, *, new_status: S, actor_id: int) -> None:
        cur = self.current()
        if not self.transition_policy.can_transition(cur, new_status):
            raise DomainOperationError(f"Cannot change status from {cur} to {new_status}")
        self.records.append(self.record_factory(status=new_status, actor_id=actor_id))

    def unique_statuses(self) -> Set[S]:
        """Return set of all statuses ever used."""
        return {self.get_status(r) for r in self.records}

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self):
        return iter(self.records)




@dataclass
class CommentThread:
    comments: list[Comment] = field(default_factory=list)

    def add(self, comment: Comment) -> None:
        self.comments.append(comment)


@dataclass
class ExecutorAssignments:
    """
    Stores executor assignments over time.
    In your model executor is an admin id, so the VO is ExecutorAssignment(admin_id=...).
    """
    assignments: list[ExecutorAssignment] = field(default_factory=list)

    def add(self, assignment: ExecutorAssignment) -> None:
        self.assignments.append(assignment)

    def current(self) -> ExecutorAssignment:
        try:
            return self.assignments[-1]
        except IndexError:
            raise DomainOperationError("No executor available")
