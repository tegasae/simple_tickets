from dataclasses import field, dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from src.domain.exceptions import DomainOperationError


class TicketStatus(Enum):
    """Ticket status with valid transitions"""
    RECEIVED = "received"
    AT_WORK = "at_work"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"
    @classmethod
    def can_transition(cls, from_status: 'TicketStatus', to_status: 'TicketStatus') -> bool:
        """Business rule 3: Define valid status transitions"""
        transitions = {
            cls.RECEIVED: [cls.AT_WORK, cls.CANCELLED,cls.DEFERRED],
            cls.AT_WORK: [cls.RECEIVED, cls.FINISHED, cls.CANCELLED, cls.DEFERRED],
            cls.DEFERRED: [cls.RECEIVED, cls.AT_WORK, cls.CANCELLED],
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




