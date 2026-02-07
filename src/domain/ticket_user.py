#src/domain/ticket_user.py
"""Ticket User Domain Model.

This module defines the domain entities for a ticket management system,
including status transitions, comments, and executors.
"""

from dataclasses import dataclass, field, InitVar
from datetime import datetime
from enum import Enum
from typing import Self, Any

from src.domain.exceptions import DomainOperationError


class StatusTicketOfClient(Enum):
    """Enum representing possible ticket statuses.

    Attributes:
        CREATED: Initial status when ticket is created
        CONFIRMED: Ticket has been confirmed
        AT_WORK: Ticket is being worked on
        EXECUTED: Ticket work is completed
        CANCELED_BY_ADMIN: Ticket canceled by administrator
        CANCELED_BY_CLIENT: Ticket canceled by client
    """
    CREATED = "created"
    CONFIRMED = "confirmed"
    AT_WORK = "at work"
    EXECUTED = "executed"
    CANCELED_BY_ADMIN = "canceled_by_admin"
    CANCELED_BY_CLIENT = "canceled_by_client"

    @classmethod
    def can_transition(cls, from_status: Self, to_status: Self) -> bool:
        """Check if a status transition is valid.

        Args:
            from_status: Current status
            to_status: Desired new status

        Returns:
            True if transition is allowed, False otherwise

        Note:
            Business rule: Defines valid status transitions
        """
        transitions = {
            cls.CREATED: [cls.CONFIRMED, cls.AT_WORK,
                          cls.CANCELED_BY_CLIENT, cls.CANCELED_BY_ADMIN],
            cls.CONFIRMED: [cls.AT_WORK, cls.CANCELED_BY_CLIENT,
                            cls.CANCELED_BY_ADMIN],
            cls.AT_WORK: [cls.EXECUTED, cls.CANCELED_BY_ADMIN],
            cls.EXECUTED: [],
            cls.CANCELED_BY_CLIENT: [],
            cls.CANCELED_BY_ADMIN: []
        }
        return to_status in transitions.get(from_status, [])


@dataclass(frozen=True, kw_only=True)
class Status:
    """Immutable record of a status change.

    Attributes:
        employee_id: ID of employee who changed the status
        status: The new status value
        date_created: When the status was changed
    """
    employee_id: int
    status: StatusTicketOfClient
    date_created: datetime = field(default_factory=datetime.now)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Status):
            return self.status==other.status
        return False

@dataclass(frozen=True, kw_only=True)
class Comment:
    """Immutable comment on a ticket.

    Attributes:
        employee_id: ID of employee who added the comment
        comment: The comment text
        date_created: When the comment was added
    """
    employee_id: int
    comment: str
    date_created: datetime = field(default_factory=datetime.now)


@dataclass
class Executor:
    """Ticket executor assignment.

    Attributes:
        id_admin: ID of the administrator assigned as executor
        date_created: When the assignment was made
    """
    id_admin: int
    date_created: datetime = field(default_factory=datetime.now)


@dataclass(kw_only=True)
class TicketUser:
    """Main ticket entity with status history, comments, and executors.

    Attributes:
        ticket_id: Unique identifier for the ticket
        client_id: ID of the client who owns the ticket
        created_by_employee_id: ID of employee who created the ticket (transient)
        statuses: History of status changes
        comments: List of comments on the ticket
        executors: History of executor assignments
        description: Ticket description
        date_created: When the ticket was created
        version: Optimistic concurrency control version

    Note:
        The created_by_employee_id is an InitVar used only during initialization
        to set the initial status and is not stored as a field.
    """
    ticket_id: int
    client_id: int
    created_by_employee_id: InitVar[int]
    statuses: list[Status] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    executors: list[Executor] = field(default_factory=list)
    description: str
    date_created: datetime = field(default_factory=datetime.now)
    version: int = 0

    def __post_init__(self, created_by_employee_id: int) -> None:
        """Initialize ticket with CREATED status if no statuses provided.

        Args:
            created_by_employee_id: ID of employee creating the ticket
        """
        if not self.statuses:
            self.statuses.append(
                Status(
                    status=StatusTicketOfClient.CREATED,
                    employee_id=created_by_employee_id,
                )
            )

    @classmethod
    def create(
            cls,
            ticket_id: int,
            client_id: int,
            created_by_employee_id: int,
            description: str,
            initial_comment: str | None = None,
            initial_executor_id: int | None = None
    ) -> Self:
        """Create a new ticket.

        Args:
            ticket_id: Unique identifier for the ticket
            client_id: ID of the client who owns the ticket
            created_by_employee_id: ID of employee creating the ticket
            description: Ticket description
            initial_comment: Optional initial comment
            initial_executor_id: Optional initial executor ID

        Returns:
            New TicketUser instance

        Example:
            ticket = TicketUser.create(
                ticket_id=1,
                client_id=100,
                created_by_employee_id=50,
                description="Server is down",
                initial_comment="Reported by client via phone",
                initial_executor_id=200
            )
        """
        # Create empty lists
        statuses: list[Status] = []
        comments: list[Comment] = []
        executors: list[Executor] = []

        # Add initial comment if provided
        if initial_comment:
            comments.append(
                Comment(
                    employee_id=created_by_employee_id,
                    comment=initial_comment
                )
            )

        # Add initial executor if provided
        if initial_executor_id is not None:
            executors.append(
                Executor(id_admin=initial_executor_id)
            )

        # Create and return ticket
        return cls(
            ticket_id=ticket_id,
            client_id=client_id,
            created_by_employee_id=created_by_employee_id,
            description=description,
            statuses=statuses,  # Will be initialized in __post_init__
            comments=comments,
            executors=executors,
        )

    def change_status(self, new_status: StatusTicketOfClient, employee_id: int) -> None:
        """Change the ticket status with validation.

        Args:
            new_status: The desired new status
            employee_id: ID of employee making the change

        Raises:
            DomainOperationError: If the status transition is not allowed
        """
        if not StatusTicketOfClient.can_transition(self.statuses[-1].status, new_status):
            raise DomainOperationError(
                f"Cannot change status from {self.statuses[-1].status.value} "
                f"to {new_status.value}"
            )

        self.statuses.append(Status(status=new_status, employee_id=employee_id))
        self.version += 1

    def add_comment(self, comment: Comment) -> None:
        """Add a comment to the ticket.

        Args:
            comment: The comment to add
        """
        self.comments.append(comment)
        self.version += 1

    def get_current_state(self) -> StatusTicketOfClient:
        """Get the current status of the ticket.

        Returns:
            The most recent status
        """
        return self.statuses[-1].status

    def add_executor(self, new_executor: Executor) -> None:
        """Add an executor assignment to the ticket.

        Args:
            new_executor: The executor to add
        """
        self.executors.append(new_executor)

    def get_current_executor(self) -> Executor:
        """Get the current executor of the ticket.

        Returns:
            The most recent executor

        Raises:
            DomainOperationError: If no executors have been assigned
        """
        try:
            return self.executors[-1]
        except IndexError:
            raise DomainOperationError(message="No executor available")

