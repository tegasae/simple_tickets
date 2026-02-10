# tests/domain/test_ticket.py
import pytest
from datetime import datetime, timezone
from src.domain.ticket import Ticket, TicketStatus, TicketStatusRecord
from src.domain.ticket_components import Comment, ExecutorAssignment
from src.domain.exceptions import DomainOperationError


class TestTicketStatus:
    """Test TicketStatus enum and transitions."""

    def test_transition_created_to_at_work(self):
        assert TicketStatus.can_transition(TicketStatus.CREATED, TicketStatus.AT_WORK)

    def test_transition_created_to_cancelled(self):
        assert TicketStatus.can_transition(TicketStatus.CREATED, TicketStatus.CANCELLED)

    def test_transition_created_to_deferred(self):
        assert TicketStatus.can_transition(TicketStatus.CREATED, TicketStatus.DEFERRED)

    def test_transition_at_work_to_executed(self):
        assert TicketStatus.can_transition(TicketStatus.AT_WORK, TicketStatus.EXECUTED)

    def test_transition_deferred_to_at_work(self):
        assert TicketStatus.can_transition(TicketStatus.DEFERRED, TicketStatus.AT_WORK)

    def test_invalid_transition_created_to_executed(self):
        assert not TicketStatus.can_transition(TicketStatus.CREATED, TicketStatus.EXECUTED)

    def test_terminal_statuses_cannot_transition(self):
        assert not TicketStatus.can_transition(TicketStatus.EXECUTED, TicketStatus.AT_WORK)
        assert not TicketStatus.can_transition(TicketStatus.CANCELLED, TicketStatus.AT_WORK)


class TestTicketStatusRecord:
    """Test TicketStatusRecord value object."""

    def test_record_creation(self):
        record = TicketStatusRecord(
            actor_employee_id=1,
            status=TicketStatus.CREATED
        )
        assert record.actor_employee_id == 1
        assert record.status == TicketStatus.CREATED
        assert isinstance(record.created_at, datetime)

    def test_record_equality_by_status(self):
        record1 = TicketStatusRecord(actor_employee_id=1, status=TicketStatus.CREATED)
        record2 = TicketStatusRecord(actor_employee_id=2, status=TicketStatus.CREATED)
        record3 = TicketStatusRecord(actor_employee_id=1, status=TicketStatus.AT_WORK)

        assert record1 == record2  # Same status
        assert record1 != record3  # Different status


class TestTicket:
    """Test Ticket aggregate root."""

    @pytest.fixture
    def sample_ticket(self):
        return Ticket(
            ticket_id=1,
            client_id=100,
            admin_id=200,
            description="Test ticket"
        )

    def test_ticket_creation(self, sample_ticket):
        """Test basic ticket creation."""
        assert sample_ticket.ticket_id == 1
        assert sample_ticket.client_id == 100
        assert sample_ticket.admin_id == 200
        assert sample_ticket.description == "Test ticket"
        assert sample_ticket.created_by_client is False
        assert sample_ticket.is_remote is False
        assert sample_ticket.is_closed is False
        assert sample_ticket.finished_at is None
        assert sample_ticket.version == 0
        assert sample_ticket.urgency_level == 0

    def test_initial_status_created(self, sample_ticket):
        """Test that ticket gets initial CREATED status."""
        assert sample_ticket.current_status() == TicketStatus.CREATED
        assert len(sample_ticket.statuses) == 1
        assert sample_ticket.statuses[0].actor_employee_id == 200  # admin_id

    def test_change_status_valid_transition(self, sample_ticket):
        """Test valid status change."""
        sample_ticket.change_status(TicketStatus.AT_WORK, actor_employee_id=300)

        assert sample_ticket.current_status() == TicketStatus.AT_WORK
        assert len(sample_ticket.statuses) == 2
        assert sample_ticket.version == 1

    def test_change_status_invalid_transition(self, sample_ticket):
        """Test invalid status transition raises error."""
        with pytest.raises(DomainOperationError, match="Cannot change status"):
            sample_ticket.change_status(TicketStatus.EXECUTED, actor_employee_id=300)

    def test_change_status_when_closed(self, sample_ticket):
        """Test that closed tickets cannot change status."""
        sample_ticket.change_status(TicketStatus.CANCELLED, actor_employee_id=300)

        assert sample_ticket.is_closed is True
        assert sample_ticket.finished_at is not None

        with pytest.raises(DomainOperationError, match="Ticket is closed"):
            sample_ticket.change_status(TicketStatus.AT_WORK, actor_employee_id=300)

    def test_terminal_status_closes_ticket(self, sample_ticket):
        """Test that EXECUTED and CANCELLED close the ticket."""
        sample_ticket.change_status(TicketStatus.AT_WORK, actor_employee_id=300)
        sample_ticket.change_status(TicketStatus.EXECUTED, actor_employee_id=300)

        assert sample_ticket.is_closed is True
        assert sample_ticket.finished_at is not None
        assert sample_ticket.current_status() == TicketStatus.EXECUTED

    def test_add_comment(self, sample_ticket):
        """Test adding comments to open ticket."""
        comment = Comment(employee_id=400, comment="Test comment")
        sample_ticket.add_comment(comment)

        assert len(sample_ticket.comments) == 1
        assert sample_ticket.comments[0].employee_id == 400
        assert sample_ticket.version == 1

    def test_add_comment_to_closed_ticket(self, sample_ticket):
        """Test that closed tickets cannot receive comments."""
        sample_ticket.change_status(TicketStatus.CANCELLED, actor_employee_id=300)

        comment = Comment(employee_id=400, comment="Test comment")
        with pytest.raises(DomainOperationError, match="Ticket is closed"):
            sample_ticket.add_comment(comment)

    def test_add_executor(self, sample_ticket):
        """Test adding executor assignment."""
        assignment = ExecutorAssignment(admin_id=500)
        sample_ticket.add_executor(assignment)

        assert len(sample_ticket.executors) == 1
        assert sample_ticket.executors[0].admin_id == 500
        assert sample_ticket.version == 1

    def test_add_executor_to_closed_ticket(self, sample_ticket):
        """Test that closed tickets cannot receive executor assignments."""
        sample_ticket.change_status(TicketStatus.CANCELLED, actor_employee_id=300)

        assignment = ExecutorAssignment(admin_id=500)
        with pytest.raises(DomainOperationError, match="Ticket is closed"):
            sample_ticket.add_executor(assignment)

    def test_current_executor(self, sample_ticket):
        """Test retrieving current executor."""
        assignment1 = ExecutorAssignment(admin_id=500)
        assignment2 = ExecutorAssignment(admin_id=600)

        sample_ticket.add_executor(assignment1)
        sample_ticket.add_executor(assignment2)

        current = sample_ticket.current_executor()
        assert current.admin_id == 600  # Last assignment

    def test_current_executor_no_executors(self, sample_ticket):
        """Test error when no executors exist."""
        with pytest.raises(DomainOperationError, match="No executor available"):
            sample_ticket.current_executor()

    def test_convenience_methods(self, sample_ticket):
        """Test convenience methods for status changes."""
        sample_ticket.start_work(actor_employee_id=300)
        assert sample_ticket.current_status() == TicketStatus.AT_WORK

        sample_ticket.defer(actor_employee_id=300)
        assert sample_ticket.current_status() == TicketStatus.DEFERRED

        sample_ticket.start_work(actor_employee_id=300)
        sample_ticket.execute(actor_employee_id=300)
        assert sample_ticket.current_status() == TicketStatus.EXECUTED

        # Reset for cancel test
        sample_ticket2 = Ticket(
            ticket_id=2,
            client_id=100,
            admin_id=200,
            description="Test ticket 2"
        )
        sample_ticket2.cancel(actor_employee_id=300)
        assert sample_ticket2.current_status() == TicketStatus.CANCELLED

    def test_rehydration_from_storage(self):
        """Test that ticket correctly rehydrates from stored data."""
        statuses = [
            TicketStatusRecord(
                actor_employee_id=200,
                status=TicketStatus.CREATED,
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
            ),
            TicketStatusRecord(
                actor_employee_id=300,
                status=TicketStatus.CANCELLED,
                created_at=datetime(2024, 1, 2, tzinfo=timezone.utc)
            )
        ]

        ticket = Ticket(
            ticket_id=1,
            client_id=100,
            admin_id=200,
            description="Rehydrated ticket",
            statuses=statuses
        )

        assert ticket.is_closed is True
        assert ticket.finished_at == statuses[-1].created_at
        assert ticket.current_status() == TicketStatus.CANCELLED

    def test_remote_ticket(self):
        """Test remote ticket creation."""
        ticket = Ticket(
            ticket_id=1,
            client_id=100,
            admin_id=200,
            description="Remote ticket",
            is_remote=True
        )

        assert ticket.is_remote is True