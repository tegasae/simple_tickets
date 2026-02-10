# tests/domain/test_ticket_components.py
import pytest
from datetime import datetime

from src.domain.ticket_components import (
    Comment,
    ExecutorAssignment,
    CommentThread,
    ExecutorAssignments,
)
from src.domain.exceptions import DomainOperationError



class TestComment:
    """Test Comment value object."""

    def test_comment_creation(self):
        comment = Comment(employee_id=1, comment="Test comment")
        assert comment.employee_id == 1
        assert comment.comment == "Test comment"
        assert isinstance(comment.date_created, datetime)


class TestExecutorAssignment:
    """Test ExecutorAssignment value object."""

    def test_executor_assignment_creation(self):
        assignment = ExecutorAssignment(admin_id=1)
        assert assignment.admin_id == 1
        assert isinstance(assignment.date_created, datetime)


class TestCommentThread:
    """Test CommentThread entity."""

    def test_add_comment(self):
        thread = CommentThread()
        comment = Comment(employee_id=1, comment="Test comment")

        thread.add(comment)
        assert len(thread.comments) == 1
        assert thread.comments[0] == comment

    def test_multiple_comments(self):
        thread = CommentThread()

        for i in range(3):
            comment = Comment(employee_id=i, comment=f"Comment {i}")
            thread.add(comment)

        assert len(thread.comments) == 3


class TestExecutorAssignments:
    """Test ExecutorAssignments entity."""

    def test_add_assignment(self):
        assignments = ExecutorAssignments()
        assignment = ExecutorAssignment(admin_id=1)

        assignments.add(assignment)
        assert len(assignments.assignments) == 1
        assert assignments.assignments[0] == assignment

    def test_current_assignment(self):
        assignments = ExecutorAssignments()

        assignment1 = ExecutorAssignment(admin_id=1)
        assignment2 = ExecutorAssignment(admin_id=2)

        assignments.add(assignment1)
        assignments.add(assignment2)

        current = assignments.current()
        assert current.admin_id == 2

    def test_current_no_assignments(self):
        assignments = ExecutorAssignments()

        with pytest.raises(DomainOperationError, match="No executor available"):
            assignments.current()






