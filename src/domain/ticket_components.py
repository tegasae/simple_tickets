# ============================
# src/domain/ticket_components.py
# Shared components (composition, not inheritance)
# ============================
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from typing import Callable, Generic, Protocol, TypeVar, List, Set

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








@dataclass
class StatusHistory(Generic[S, R]):
    """
    Generic status history component with strict typing.

    Required dependencies:
      - can_transition(from_status, to_status) -> bool
      - get_status(record) -> status
      - make_record(status, actor_id) -> record   <-- positional arguments

    This design avoids keyword-only callable typing issues in type checkers.
    """

    can_transition: Callable[[S, S], bool]
    get_status: Callable[[R], S]
    make_record: Callable[[S, int], R]

    records: List[R] = field(default_factory=list)

    def ensure_initialized(self, *, initial_status: S, actor_id: int) -> None:
        """Add initial record if history is empty."""
        if not self.records:
            self.records.append(self.make_record(initial_status, actor_id))

    def current(self) -> S:
        """Return current (latest) status."""
        if not self.records:
            raise DomainOperationError("Status history is empty")
        return self.get_status(self.records[-1])

    def can_change_to(self, new_status: S) -> bool:
        """Check if the current status can transition to new_status."""
        return self.can_transition(self.current(), new_status)

    def change(self, *, new_status: S, actor_id: int) -> None:
        """Validate transition and append new record."""
        cur = self.current()
        if not self.can_transition(cur, new_status):
            raise DomainOperationError(f"Cannot change status from {cur} to {new_status}")
        self.records.append(self.make_record(new_status, actor_id))

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
