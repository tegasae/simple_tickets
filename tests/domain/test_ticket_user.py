# tests/domain/test_ticket_user.py
import pytest
from datetime import datetime, timezone
from src.domain.ticket_user import (
    TicketUser,
    StatusTicketOfClient,
    StatusRecordTicketUser
)
from src.domain.ticket_components import Comment, ExecutorAssignment
from src.domain.exceptions import DomainOperationError


class TestStatusTicketOfClient:
    """Test client-side ticket status enum and transitions."""

    def test_transition_created_to_confirmed(self):
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CREATED,
            StatusTicketOfClient.CONFIRMED
        )

    def test_transition_created_to_canceled_by_client(self):
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CREATED,
            StatusTicketOfClient.CANCELED_BY_CLIENT
        )

    def test_transition_confirmed_to_at_work(self):
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CONFIRMED,
            StatusTicketOfClient.AT_WORK
        )

    def test_transition_at_work_to_executed(self):
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.AT_WORK,
            StatusTicketOfClient.EXECUTED
        )

    def test_invalid_transition_created_to_executed(self):
        assert not StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CREATED,
            StatusTicketOfClient.EXECUTED
        )

    def test_canceled_by_admin_from_multiple_states(self):
        # Can be canceled by admin from CREATED, CONFIRMED, AT_WORK
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CREATED,
            StatusTicketOfClient.CANCELED_BY_ADMIN
        )
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.CONFIRMED,
            StatusTicketOfClient.CANCELED_BY_ADMIN
        )
        assert StatusTicketOfClient.can_transition(
            StatusTicketOfClient.AT_WORK,
            StatusTicketOfClient.CANCELED_BY_ADMIN
        )

    def test_terminal_statuses_cannot_transition(self):
        terminal_statuses = [
            StatusTicketOfClient.EXECUTED,
            StatusTicketOfClient.CANCELED_BY_CLIENT,
            StatusTicketOfClient.CANCELED_BY_ADMIN
        ]

        for status in terminal_statuses:
            assert not StatusTicketOfClient.can_transition(
                status,
                StatusTicketOfClient.AT_WORK
            )


class TestTicketUser:
    """Test TicketUser aggregate root."""

    @pytest.fixture
    def sample_ticket_user(self):
        return TicketUser(
            ticket_id=1,
            client_id=100,
            user_id=300,
            description="Test user ticket"
        )

    def test_ticket_user_creation(self, sample_ticket_user):
        """Test basic TicketUser creation."""
        assert sample_ticket_user.ticket_id == 1
        assert sample_ticket_user.client_id == 100
        assert sample_ticket_user.user_id == 300
        assert sample_ticket_user.description == "Test user ticket"
        assert sample_ticket_user.created_by_client is False
        assert sample_ticket_user.is_closed is False
        assert sample_ticket_user.date_finished is None
        assert sample_ticket_user.version == 0

    def test_initial_status_created(self, sample_ticket_user):
        """Test that TicketUser gets initial CREATED status."""
        assert sample_ticket_user.current_status() == StatusTicketOfClient.CREATED
        assert len(sample_ticket_user.statuses) == 1
        assert sample_ticket_user.statuses[0].actor_employee_id == 300  # user_id

    def test_change_status_valid_transition(self, sample_ticket_user):
        """Test valid status change."""
        sample_ticket_user.change_status(
            StatusTicketOfClient.CONFIRMED,
            actor_employee_id=400
        )

        assert sample_ticket_user.current_status() == StatusTicketOfClient.CONFIRMED
        assert len(sample_ticket_user.statuses) == 2
        assert sample_ticket_user.version == 1

    def test_change_status_invalid_transition(self, sample_ticket_user):
        """Test invalid status transition raises error."""
        with pytest.raises(DomainOperationError, match="Cannot change status"):
            sample_ticket_user.change_status(
                StatusTicketOfClient.EXECUTED,
                actor_employee_id=400
            )

    def test_change_status_when_closed(self, sample_ticket_user):
        """Test that closed TicketUsers cannot change status."""
        sample_ticket_user.change_status(
            StatusTicketOfClient.CANCELED_BY_CLIENT,
            actor_employee_id=300
        )

        assert sample_ticket_user.is_closed is True

        with pytest.raises(DomainOperationError, match="TicketUser is closed"):
            sample_ticket_user.change_status(
                StatusTicketOfClient.CONFIRMED,
                actor_employee_id=400
            )

    def test_terminal_statuses_close_ticket(self, sample_ticket_user):
        """Test that terminal statuses close the ticket."""
        terminal_statuses = [
            StatusTicketOfClient.EXECUTED,
            StatusTicketOfClient.CANCELED_BY_CLIENT,
            StatusTicketOfClient.CANCELED_BY_ADMIN
        ]

        for terminal_status in terminal_statuses:
            # Create fresh ticket for each test
            ticket = TicketUser(
                ticket_id=2,
                client_id=100,
                user_id=300,
                description="Test ticket"
            )

            if terminal_status != StatusTicketOfClient.CANCELED_BY_CLIENT:
                # Need to transition through intermediate states
                ticket.change_status(StatusTicketOfClient.CONFIRMED, actor_employee_id=400)
                if terminal_status != StatusTicketOfClient.CANCELED_BY_ADMIN:
                    ticket.change_status(StatusTicketOfClient.AT_WORK, actor_employee_id=400)

            ticket.change_status(terminal_status, actor_employee_id=400)

            assert ticket.is_closed is True
            assert ticket.date_finished is not None
            assert ticket.current_status() == terminal_status

    def test_convenience_methods(self, sample_ticket_user):
        """Test convenience methods for status changes."""
        sample_ticket_user.confirm(actor_employee_id=400)
        assert sample_ticket_user.current_status() == StatusTicketOfClient.CONFIRMED

        sample_ticket_user.start_work(actor_employee_id=400)
        assert sample_ticket_user.current_status() == StatusTicketOfClient.AT_WORK

        sample_ticket_user.execute(actor_employee_id=400)
        assert sample_ticket_user.current_status() == StatusTicketOfClient.EXECUTED

    def test_cancel_methods(self):
        """Test cancellation convenience methods."""
        # Test cancel by client
        ticket1 = TicketUser(
            ticket_id=1,
            client_id=100,
            user_id=300,
            description="Test ticket 1"
        )
        ticket1.cancel_by_client(actor_employee_id=300)
        assert ticket1.current_status() == StatusTicketOfClient.CANCELED_BY_CLIENT

        # Test cancel by admin
        ticket2 = TicketUser(
            ticket_id=2,
            client_id=100,
            user_id=300,
            description="Test ticket 2"
        )
        ticket2.confirm(actor_employee_id=400)
        ticket2.cancel_by_admin(actor_employee_id=400)
        assert ticket2.current_status() == StatusTicketOfClient.CANCELED_BY_ADMIN

    def test_add_comment_and_executor(self, sample_ticket_user):
        """Test adding comments and executors."""
        # Add comment
        comment = Comment(employee_id=500, comment="Test comment")
        sample_ticket_user.add_comment(comment)
        assert len(sample_ticket_user.comments) == 1
        assert sample_ticket_user.version == 1

        # Add executor
        assignment = ExecutorAssignment(admin_id=600)
        sample_ticket_user.add_executor(assignment)
        assert len(sample_ticket_user.executors) == 1
        assert sample_ticket_user.version == 2

    def test_rehydration_from_storage(self):
        """Test that TicketUser correctly rehydrates from stored data."""
        statuses = [
            StatusRecordTicketUser(
                actor_employee_id=300,
                status=StatusTicketOfClient.CREATED,
                date_created=datetime(2024, 1, 1, tzinfo=timezone.utc)
            ),
            StatusRecordTicketUser(
                actor_employee_id=400,
                status=StatusTicketOfClient.CANCELED_BY_ADMIN,
                date_created=datetime(2024, 1, 2, tzinfo=timezone.utc)
            )
        ]

        ticket = TicketUser(
            ticket_id=1,
            client_id=100,
            user_id=300,
            description="Rehydrated ticket",
            statuses=statuses
        )

        assert ticket.is_closed is True
        assert ticket.date_finished == statuses[-1].date_created
        assert ticket.current_status() == StatusTicketOfClient.CANCELED_BY_ADMIN


class TestStatusRecordTicketUser:
    """Test StatusRecordTicketUser value object."""

    def test_record_creation(self):
        record = StatusRecordTicketUser(
            actor_employee_id=1,
            status=StatusTicketOfClient.CREATED
        )
        assert record.actor_employee_id == 1
        assert record.status == StatusTicketOfClient.CREATED
        assert isinstance(record.date_created, datetime)

    def test_record_equality_by_status(self):
        record1 = StatusRecordTicketUser(
            actor_employee_id=1,
            status=StatusTicketOfClient.CREATED
        )
        record2 = StatusRecordTicketUser(
            actor_employee_id=2,
            status=StatusTicketOfClient.CREATED
        )
        record3 = StatusRecordTicketUser(
            actor_employee_id=1,
            status=StatusTicketOfClient.CONFIRMED
        )

        assert record1 == record2  # Same status
        assert record1 != record3  # Different status