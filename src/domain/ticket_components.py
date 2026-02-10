# ============================
# src/domain/ticket_components.py
# Shared components (composition, not inheritance)
# ============================
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from typing import TypeVar

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
