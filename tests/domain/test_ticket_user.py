"""Tests for Ticket User Domain Model."""
import dataclasses
from enum import Enum

import pytest
from datetime import datetime
from unittest.mock import patch


from src.domain.ticket_user import (
    StatusTicketOfClient,
    Status,
    Comment,
    Executor,
    TicketUser,
)
from src.domain.exceptions import DomainOperationError


class TestStatusTicketOfClient:
    """Tests for StatusTicketOfClient enum."""

    def test_enum_values(self):
        """Test all enum values are correctly defined."""
        assert StatusTicketOfClient.CREATED.value == "created"
        assert StatusTicketOfClient.CONFIRMED.value == "confirmed"
        assert StatusTicketOfClient.AT_WORK.value == "at work"
        assert StatusTicketOfClient.EXECUTED.value == "executed"
        assert StatusTicketOfClient.CANCELED_BY_ADMIN.value == "canceled_by_admin"
        assert StatusTicketOfClient.CANCELED_BY_CLIENT.value == "canceled_by_client"

    def test_can_transition_from_created(self):
        """Test valid transitions from CREATED status."""
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CREATED,
            StatusTicketOfClient.CONFIRMED
        ) is True

        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CREATED,
            StatusTicketOfClient.AT_WORK
        ) is True

        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CREATED,
            StatusTicketOfClient.CANCELED_BY_CLIENT
        ) is True

        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CREATED,
            StatusTicketOfClient.CANCELED_BY_ADMIN
        ) is True

        # Invalid transitions
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CREATED,
            StatusTicketOfClient.EXECUTED
        ) is False

    def test_can_transition_from_confirmed(self):
        """Test valid transitions from CONFIRMED status."""
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CONFIRMED,
            StatusTicketOfClient.AT_WORK
        ) is True

        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CONFIRMED,
            StatusTicketOfClient.CANCELED_BY_CLIENT
        ) is True

        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CONFIRMED,
            StatusTicketOfClient.CANCELED_BY_ADMIN
        ) is True

        # Invalid transitions
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CONFIRMED,
            StatusTicketOfClient.CREATED
        ) is False

        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CONFIRMED,
            StatusTicketOfClient.EXECUTED
        ) is False

    def test_can_transition_from_at_work(self):
        """Test valid transitions from AT_WORK status."""
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.AT_WORK,
            StatusTicketOfClient.EXECUTED
        ) is True

        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.AT_WORK,
            StatusTicketOfClient.CANCELED_BY_ADMIN
        ) is True

        # Invalid transitions (note: in your updated transitions, AT_WORK can't go to CREATED)
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.AT_WORK,
            StatusTicketOfClient.CREATED
        ) is False

        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.AT_WORK,
            StatusTicketOfClient.CONFIRMED
        ) is False

        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.AT_WORK,
            StatusTicketOfClient.CANCELED_BY_CLIENT
        ) is False

    def test_can_transition_from_final_statuses(self):
        """Test that final statuses cannot transition to other statuses."""
        final_statuses = [
            StatusTicketOfClient.EXECUTED,
            StatusTicketOfClient.CANCELED_BY_CLIENT,
            StatusTicketOfClient.CANCELED_BY_ADMIN,
        ]

        for final_status in final_statuses:
            for target_status in StatusTicketOfClient:
                assert StatusTicketOfClient.can_transition(
                    final_status,
                    target_status
                ) is False

    def test_invalid_from_status_returns_false(self):
        """Test that invalid from_status returns False."""

        # Using a mock status that's not in the transitions dict
        class MockStatus(Enum):
            UNKNOWN = "unknown"

        assert StatusTicketOfClient.can_transition(
            MockStatus.UNKNOWN,  # type: ignore
            StatusTicketOfClient.CREATED
        ) is False


class TestStatus:
    """Tests for Status dataclass."""

    def test_status_creation(self):
        """Test creating a Status with default timestamp."""
        status = Status(
            employee_id=123,
            status=StatusTicketOfClient.CREATED
        )

        assert status.employee_id == 123
        assert status.status == StatusTicketOfClient.CREATED
        assert isinstance(status.date_created, datetime)

    def test_status_is_frozen(self):
        """Test that Status is immutable."""
        status = Status(
            employee_id=123,
            status=StatusTicketOfClient.CREATED
        )

        # Should not be able to modify attributes
        with pytest.raises(dataclasses.FrozenInstanceError):
            status.employee_id = 456

        with pytest.raises(dataclasses.FrozenInstanceError):
            status.status = StatusTicketOfClient.AT_WORK

    def test_status_equality(self):
        """Test Status equality comparison."""
        status1 = Status(
            employee_id=123,
            status=StatusTicketOfClient.CREATED
        )

        status2 = Status(
            employee_id=123,
            status=StatusTicketOfClient.CREATED
        )

        # Different instances with same values should not be equal
        # (unless __eq__ is overridden, which dataclass does by default)
        assert status1 == status2

        status3 = Status(
            employee_id=456,
            status=StatusTicketOfClient.AT_WORK
        )

        assert status1 != status3


class TestComment:
    """Tests for Comment dataclass."""

    def test_comment_creation(self):
        """Test creating a Comment."""
        comment = Comment(
            employee_id=123,
            comment="This is a test comment"
        )

        assert comment.employee_id == 123
        assert comment.comment == "This is a test comment"
        assert isinstance(comment.date_created, datetime)

    def test_comment_is_frozen(self):
        """Test that Comment is immutable."""
        comment = Comment(
            employee_id=123,
            comment="Test comment"
        )

        with pytest.raises(dataclasses.FrozenInstanceError):
            comment.comment = "Modified comment"


class TestExecutor:
    """Tests for Executor dataclass."""

    def test_executor_creation(self):
        """Test creating an Executor."""
        executor = Executor(id_admin=123)

        assert executor.id_admin == 123
        assert isinstance(executor.date_created, datetime)


class TestTicketUser:
    """Tests for TicketUser entity."""

    def test_ticket_creation_with_default_status(self):
        """Test creating a ticket without providing statuses."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket description"
        )

        assert ticket.ticket_id == 1
        assert ticket.client_id == 100
        assert ticket.description == "Test ticket description"
        assert len(ticket.statuses) == 1
        assert ticket.statuses[0].status == StatusTicketOfClient.CREATED
        assert ticket.statuses[0].employee_id == 50
        assert ticket.version == 0
        assert len(ticket.comments) == 0
        assert len(ticket.executors) == 0

    def test_ticket_creation_with_existing_statuses(self):
        """Test creating a ticket with pre-existing statuses."""
        existing_status = Status(
            employee_id=999,
            status=StatusTicketOfClient.CONFIRMED
        )

        ticket = TicketUser(
            ticket_id=2,
            client_id=200,
            created_by_employee_id=50,  # Ignored since statuses provided
            statuses=[existing_status],
            description="Ticket with existing status"
        )

        assert len(ticket.statuses) == 1
        assert ticket.statuses[0].status == StatusTicketOfClient.CONFIRMED
        assert ticket.statuses[0].employee_id == 999

    def test_change_status_valid_transition(self):
        """Test valid status changes."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket"
        )

        # CREATED -> CONFIRMED
        ticket.change_status(StatusTicketOfClient.CONFIRMED, employee_id=60)
        assert ticket.get_current_state() == StatusTicketOfClient.CONFIRMED
        assert ticket.version == 1

        # CONFIRMED -> AT_WORK
        ticket.change_status(StatusTicketOfClient.AT_WORK, employee_id=70)
        assert ticket.get_current_state() == StatusTicketOfClient.AT_WORK
        assert ticket.version == 2

        # AT_WORK -> EXECUTED
        ticket.change_status(StatusTicketOfClient.EXECUTED, employee_id=80)
        assert ticket.get_current_state() == StatusTicketOfClient.EXECUTED
        assert ticket.version == 3

    def test_change_status_invalid_transition(self):
        """Test invalid status change raises error."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket"
        )

        # Try to jump from CREATED to EXECUTED (invalid)
        with pytest.raises(DomainOperationError) as exc_info:
            ticket.change_status(StatusTicketOfClient.EXECUTED, employee_id=60)

        assert "Cannot change status" in str(exc_info.value)
        assert ticket.get_current_state() == StatusTicketOfClient.CREATED
        assert ticket.version == 0  # Version should not increment

    def test_cancel_by_client_from_created(self):
        """Test canceling by client from CREATED status."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket"
        )

        ticket.change_status(StatusTicketOfClient.CANCELED_BY_CLIENT, employee_id=100)
        assert ticket.get_current_state() == StatusTicketOfClient.CANCELED_BY_CLIENT
        assert ticket.version == 1

    def test_cancel_by_admin_from_confirmed(self):
        """Test canceling by admin from CONFIRMED status."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket"
        )

        ticket.change_status(StatusTicketOfClient.CONFIRMED, employee_id=60)
        ticket.change_status(StatusTicketOfClient.CANCELED_BY_ADMIN, employee_id=1)

        assert ticket.get_current_state() == StatusTicketOfClient.CANCELED_BY_ADMIN
        assert ticket.version == 2

    def test_add_comment(self):
        """Test adding comments to a ticket."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket"
        )

        comment1 = Comment(employee_id=100, comment="First comment")
        comment2 = Comment(employee_id=200, comment="Second comment")

        ticket.add_comment(comment1)
        ticket.add_comment(comment2)

        assert len(ticket.comments) == 2
        assert ticket.comments[0] == comment1
        assert ticket.comments[1] == comment2
        assert ticket.version == 2

    def test_add_and_get_executor(self):
        """Test adding and retrieving executors."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket"
        )

        executor1 = Executor(id_admin=100)
        executor2 = Executor(id_admin=200)

        ticket.add_executor(executor1)
        ticket.add_executor(executor2)

        assert len(ticket.executors) == 2
        assert ticket.get_current_executor() == executor2
        assert ticket.get_current_executor().id_admin == 200

    def test_get_current_executor_no_executors(self):
        """Test getting current executor when none exist."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket"
        )

        with pytest.raises(DomainOperationError) as exc_info:
            ticket.get_current_executor()

        assert "No executor available" in str(exc_info.value)

    def test_get_current_state_multiple_statuses(self):
        """Test getting current state with multiple status changes."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket"
        )

        statuses_to_test = [
            StatusTicketOfClient.CONFIRMED,
            StatusTicketOfClient.AT_WORK,
            StatusTicketOfClient.EXECUTED
        ]

        for i, status in enumerate(statuses_to_test, 1):
            ticket.change_status(status, employee_id=50 + i)
            assert ticket.get_current_state() == status
            assert len(ticket.statuses) == i + 1  # +1 for initial CREATED


    def test_version_increment_on_state_change(self):
        """Test that version increments on state changes."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket"
        )

        assert ticket.version == 0

        ticket.change_status(StatusTicketOfClient.CONFIRMED, employee_id=60)
        assert ticket.version == 1

        ticket.change_status(StatusTicketOfClient.AT_WORK, employee_id=70)
        assert ticket.version == 2

        ticket.change_status(StatusTicketOfClient.EXECUTED, employee_id=80)
        assert ticket.version == 3

    def test_version_increment_on_comment_add(self):
        """Test that version increments when adding comments."""
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test ticket"
        )

        assert ticket.version == 0

        ticket.add_comment(Comment(employee_id=100, comment="Comment 1"))
        assert ticket.version == 1

        ticket.add_comment(Comment(employee_id=200, comment="Comment 2"))
        assert ticket.version == 2

    def test_comprehensive_workflow(self):
        """Test a comprehensive ticket workflow."""
        # Create ticket
        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Server issue"
        )

        assert ticket.get_current_state() == StatusTicketOfClient.CREATED

        # Confirm ticket
        ticket.change_status(StatusTicketOfClient.CONFIRMED, employee_id=60)

        # Add executor
        executor = Executor(id_admin=200)
        ticket.add_executor(executor)

        # Add comment
        ticket.add_comment(Comment(
            employee_id=60,
            comment="Issue confirmed, assigning to team"
        ))

        # Start work
        ticket.change_status(StatusTicketOfClient.AT_WORK, employee_id=200)

        # Add more comments
        ticket.add_comment(Comment(
            employee_id=200,
            comment="Working on the issue"
        ))

        # Complete work
        ticket.change_status(StatusTicketOfClient.EXECUTED, employee_id=200)

        # Final checks
        assert ticket.get_current_state() == StatusTicketOfClient.EXECUTED
        assert ticket.get_current_executor().id_admin == 200
        assert len(ticket.comments) == 2
        assert len(ticket.statuses) == 4  # CREATED, CONFIRMED, AT_WORK, EXECUTED
        assert ticket.version == 5  # 3 status changes + 2 comments

    def test_ticket_equality(self):
        """Test ticket equality based on ticket_id."""
        ticket1 = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test"
        )

        ticket2 = TicketUser(
            ticket_id=1,
            client_id=100,
            created_by_employee_id=50,
            description="Test"
        )

        ticket3 = TicketUser(
            ticket_id=2,
            client_id=100,
            created_by_employee_id=50,
            description="Test"
        )

        # Tickets with same ID should not be equal (different instances)
        # unless __eq__ is overridden
        assert ticket1 != ticket2
        assert ticket1 != ticket3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])