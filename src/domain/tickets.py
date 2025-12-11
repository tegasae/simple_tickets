from dataclasses import field, dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List

from src.domain.exceptions import DomainOperationError


class TicketStatus(Enum):
    """Ticket status with valid transitions"""
    RECEIVED = "received"
    AT_WORK = "at_work"
    FINISHED = "finished"
    CANCELLED = "cancelled"

    @classmethod
    def can_transition(cls, from_status: 'TicketStatus', to_status: 'TicketStatus') -> bool:
        """Business rule 3: Define valid status transitions"""
        transitions = {
            cls.RECEIVED: [cls.AT_WORK, cls.CANCELLED],
            cls.AT_WORK: [cls.RECEIVED, cls.FINISHED, cls.CANCELLED],
            cls.FINISHED: [],  # Terminal state
            cls.CANCELLED: [],  # Terminal state
        }
        return to_status in transitions.get(from_status, [])


@dataclass
class Ticket:
    ticket_id: int    # ✅ Public field
    text_of_ticket: str
    client_id: int
    manager_id: int
    executor_id: int
    additional_information: str = ""
    comment:str=""
    status: TicketStatus = TicketStatus.RECEIVED
    date_created: datetime = field(default_factory=datetime.now)
    date_finished: Optional[datetime] = None
    date_cancelled: Optional[datetime] = None
    date_last_updated: datetime = field(default_factory=datetime.now)

    # Internal tracking
    _version: int = 1
    _is_empty: bool = field(default=False, init=False, repr=False)
    @property
    def is_empty(self) -> bool:
        return self._is_empty




    @classmethod
    def empty_ticket(cls):
        """Null object pattern for Ticket"""
        ticket = cls(
            ticket_id=0,
            manager_id=0,
            executor_id=0,
            client_id=0,
            text_of_ticket="",
            status=TicketStatus.CANCELLED  # Terminal state
        )
        ticket._is_empty = True
        return ticket

    # ============ BUSINESS METHODS ============

    def change_status(self, new_status: TicketStatus, admin_id: int) -> None:
        """
        Business rule 6: Any admin can change status
        Business rule 3: Enforce valid transitions
        """
        if not TicketStatus.can_transition(self.status, new_status):
            raise DomainOperationError(f"Cannot change status from {self.status.value} to {new_status.value}")

        old_status = self.status
        self.status = new_status
        self.date_last_updated = datetime.now()

        # Set completion timestamps
        if new_status == TicketStatus.FINISHED:
            self.date_finished = datetime.now()
        elif new_status == TicketStatus.CANCELLED:
            self.date_cancelled = datetime.now()

        self._version += 1

        # Could emit domain event here
        # TicketStatusChanged(ticket_id, old_status, new_status, admin_id)

    def update_text(self, new_text: str, admin_id: int) -> None:
        """
        Business rule 7: Any admin can change info only in RECEIVED status
        """
        if self.status != TicketStatus.RECEIVED:
            raise DomainOperationError(
                f"Cannot update ticket text in status {self.status.value}. "
                "Only allowed in 'received' status."
            )

        self.text_of_ticket = new_text
        self.date_last_updated = datetime.now()
        self._version += 1

    def update_comment(self, new_comment: str, admin_id: int) -> None:
        """Comments can be updated in any status (assuming)"""
        self.comment = new_comment
        self.date_last_updated = datetime.now()
        self._version += 1

    def set_additional_information(self, additional_information: str, admin_id: int) -> None:
        """
        Set additional_information when finishing or cancelling
        Should be called with change_status
        """
        if self.status not in [TicketStatus.FINISHED, TicketStatus.CANCELLED]:
            raise DomainOperationError(
                "Explanation can only be set when ticket is finished or cancelled"
            )

        self.additional_information=additional_information
        self.date_last_updated = datetime.now()
        self._version += 1

    def assign_executor(self, executor_id: int, admin_id: int) -> None:
        """Assign someone to work on the ticket"""
        if self.status!=TicketStatus.RECEIVED:
            raise DomainOperationError(
                "An executor can be assignment in RECEIVED"
            )

        self.executor_id = executor_id
        self.date_last_updated = datetime.now()
        self._version += 1

    # ============ QUERY METHODS ============

    @property
    def is_active(self) -> bool:
        """Check if ticket is still active (not finished/cancelled)"""
        return self.status in [TicketStatus.RECEIVED, TicketStatus.AT_WORK]

    @property
    def is_completed(self) -> bool:
        """Check if ticket is completed (finished/cancelled)"""
        return self.status in [TicketStatus.FINISHED, TicketStatus.CANCELLED]

    @property
    def can_be_modified(self) -> bool:
        """Check if ticket content can be modified"""
        return self.status == TicketStatus.RECEIVED

    @property
    def duration(self) -> float:
        """Calculate ticket duration in days"""
        if self.is_completed:
            end_date = self.date_finished or self.date_cancelled or datetime.now()
            return (end_date - self.date_created).total_seconds() / 86400
        return 0




class TicketsAggregate:
    """Aggregate Root for managing Tickets"""

    def __init__(self, tickets: list[Ticket] = None, version: int = 0):
        self.tickets_by_id: dict[int, Ticket] = {}
        self.tickets_by_client: dict[int, list[Ticket]] = {}
        self.tickets_by_admin: dict[int, list[Ticket]] = {}
        self.version: int = version

        if tickets:
            for ticket in tickets:
                self._add_existing_ticket(ticket)

        # ============ PRIVATE METHODS ============

        def _add_existing_ticket(self, ticket: Ticket) -> None:
            """Internal: Add an existing ticket"""
            if ticket.is_empty:
                raise ValueError("Cannot add empty ticket")

            ticket_id = ticket.ticket_id.value
            if ticket_id in self.tickets_by_id:
                raise ValueError(f"Ticket ID {ticket_id} already exists")

            self.tickets_by_id[ticket_id] = ticket

            # Update indexes
            if ticket.client_id not in self.tickets_by_client:
                self.tickets_by_client[ticket.client_id] = []
            self.tickets_by_client[ticket.client_id].append(ticket)

            if ticket.admin_id not in self.tickets_by_admin:
                self.tickets_by_admin[ticket.admin_id] = []
            self.tickets_by_admin[ticket.admin_id].append(ticket)

        # ============ FACTORY METHODS ============

        def create_ticket(
                self,
                admin_id: int,
                client_id: int,
                text: str,
                executor: str = "",
                comment: str = ""
        ) -> Ticket:
            """
            Business rule 4: Create ticket
            Note: Admin and Client enabled check happens at application/service layer
            """
            # Generate new ID (in real system, this comes from DB)
            new_id = max(self.tickets_by_id.keys(), default=0) + 1

            ticket = Ticket(
                ticket_id=TicketId(new_id),
                admin_id=admin_id,
                client_id=client_id,
                text=text,
                executor=executor,
                comment=comment,
                status=TicketStatus.RECEIVED
            )

            self._add_existing_ticket(ticket)
            self.version += 1

            return ticket

        # ============ COMMAND METHODS ============

        def delete_ticket(self, ticket_id: int, admin_id: int) -> None:
            """
            Business rule 5: Delete ticket
            Note: Admin enabled check happens at application/service layer
            """
            ticket = self.get_ticket_by_id(ticket_id)
            if ticket.is_empty:
                raise ValueError(f"Ticket {ticket_id} not found")

            # Remove from indexes
            ticket_id_val = ticket.ticket_id.value
            del self.tickets_by_id[ticket_id_val]

            # Remove from client index
            if ticket.client_id in self.tickets_by_client:
                self.tickets_by_client[ticket.client_id] = [
                    t for t in self.tickets_by_client[ticket.client_id]
                    if t.ticket_id.value != ticket_id_val
                ]

            # Remove from admin index
            if ticket.admin_id in self.tickets_by_admin:
                self.tickets_by_admin[ticket.admin_id] = [
                    t for t in self.tickets_by_admin[ticket.admin_id]
                    if t.ticket_id.value != ticket_id_val
                ]

            self.version += 1

    def change_ticket_status(
            self,
            ticket_id: int,
            new_status: TicketStatus,
            admin_id: int,
            explanation: str = ""
        ) -> Ticket:
            """Business rule 6: Change ticket status"""
        ticket = self.get_ticket_by_id(ticket_id)
        if ticket.is_empty:
            raise ValueError(f"Ticket {ticket_id} not found")

        ticket.change_status(new_status, admin_id)

            if explanation and new_status in [TicketStatus.FINISHED, TicketStatus.CANCELLED]:
                ticket.set_explanation(explanation, admin_id)

            self.version += 1
            return ticket

        def update_ticket_text(
                self,
                ticket_id: int,
                new_text: str,
                admin_id: int
        ) -> Ticket:
            """Business rule 7: Update ticket text (only in received status)"""
            ticket = self.get_ticket_by_id(ticket_id)
            if ticket.is_empty:
                raise ValueError(f"Ticket {ticket_id} not found")

            ticket.update_text(new_text, admin_id)
            self.version += 1
            return ticket

        # ============ QUERY METHODS ============

        def get_ticket_by_id(self, ticket_id: int) -> Ticket:
            return self.tickets_by_id.get(ticket_id, Ticket.empty_ticket())

        def get_tickets_by_client(self, client_id: int) -> List[Ticket]:
            return self.tickets_by_client.get(client_id, [])

        def get_tickets_by_admin(self, admin_id: int) -> List[Ticket]:
            return self.tickets_by_admin.get(admin_id, [])

        def get_active_tickets(self) -> List[Ticket]:
            return [t for t in self.tickets_by_id.values() if t.is_active]

        def get_completed_tickets(self) -> List[Ticket]:
            return [t for t in self.tickets_by_id.values() if t.is_completed]

        def get_tickets_by_status(self, status: TicketStatus) -> List[Ticket]:
            return [t for t in self.tickets_by_id.values() if t.status == status]

        def get_ticket_count(self) -> int:
            return len(self.tickets_by_id)




