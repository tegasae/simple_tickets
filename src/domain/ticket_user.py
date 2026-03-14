# src/domain/ticket_user.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Self

from src.domain.exceptions import DomainOperationError
from src.domain.ticket_components import Comment


class StatusTicketOfClient(Enum):
    """
    Client-side ticket workflow statuses.

    NOTE: Your current choice (CANCELED_BY_*) is OK.
    Just be consistent with spelling across the project.
    """
    CREATED = "created"
    CONFIRMED = "confirmed"
    AT_WORK = "at_work"
    EXECUTED = "executed"
    CANCELED_BY_ADMIN = "canceled_by_admin"
    CANCELED_BY_CLIENT = "canceled_by_client"

    @classmethod
    def can_transition(cls, from_status: Self, to_status: Self) -> bool:
        transitions = {
            cls.CREATED: [cls.CONFIRMED, cls.AT_WORK, cls.CANCELED_BY_CLIENT, cls.CANCELED_BY_ADMIN],
            cls.CONFIRMED: [cls.AT_WORK, cls.CANCELED_BY_CLIENT, cls.CANCELED_BY_ADMIN],
            cls.AT_WORK: [cls.EXECUTED, cls.CANCELED_BY_ADMIN],
            cls.EXECUTED: [],
            cls.CANCELED_BY_CLIENT: [],
            cls.CANCELED_BY_ADMIN: [],
        }
        return to_status in transitions.get(from_status, [])


@dataclass(frozen=True, kw_only=True)
class StatusRecordTicketUser:
    """
    Immutable record of a TicketUser status change.
    actor_employee_id: who changed status (employee or admin).
    """
    status_id: int=0
    actor_employee_id: int
    status: StatusTicketOfClient
    status: StatusTicketOfClient
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __eq__(self, other: Any) -> bool:
        # Equality by status only (optional; remove if you don't need it).
        return isinstance(other, StatusRecordTicketUser) and self.status == other.status


@dataclass(kw_only=True)
class TicketUser:
    """
    Employee-created (client-side) TicketUser aggregate.

    Invariants:
      - Initial status is CREATED (by user_id)
      - Status changes must follow StatusTicketOfClient.can_transition
      - Terminal statuses close the ticket (EXECUTED, CANCELED_BY_CLIENT, CANCELED_BY_ADMIN)
      - version increments on every change (optimistic locking)
    """
    ticket_id: int
    client_id: int
    user_id: int
    contact_user_id: int
    description: str
    # Optional cross-link for future transformation (can be unused now)
    statuses: list[StatusRecordTicketUser] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_closed: bool = False
    date_finished: Optional[datetime] = None
    version: int = 0

    @classmethod
    def create(
            cls,
            *,
            ticket_id: int,
            client_id: int,
            user_id: int,
            contact_user_id: int = 0,
            description: str,
    ) -> Self:
        """
        Create a new user ticket.

        Invariants:
            - initial status must be CREATED
            - version starts from 0
        """

        ticket = cls(
            ticket_id=ticket_id,
            client_id=client_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            description=description,
        )

        ticket.statuses.append(
            StatusRecordTicketUser(
                actor_employee_id=user_id,
                status=StatusTicketOfClient.CREATED,
            )
        )

        return ticket
    # ----------------------------
    # Queries
    # ----------------------------

    def current_status(self) -> StatusTicketOfClient:
        if not self.statuses:
            raise DomainOperationError("TicketUser has no status history")
        return self.statuses[-1].status


    # ----------------------------
    # Commands (business methods)
    # ----------------------------

    def change_status(self, new_status: StatusTicketOfClient, actor_employee_id: int) -> None:
        if self.is_closed:
            raise DomainOperationError("TicketUser is closed; status cannot be changed")

        cur = self.current_status()
        if not StatusTicketOfClient.can_transition(cur, new_status):
            raise DomainOperationError(f"Cannot change status from {cur.value} to {new_status.value}")

        self.statuses.append(StatusRecordTicketUser(status=new_status, actor_employee_id=actor_employee_id))


        if new_status in (
            StatusTicketOfClient.EXECUTED,
            StatusTicketOfClient.CANCELED_BY_ADMIN,
            StatusTicketOfClient.CANCELED_BY_CLIENT,
        ):
            self.is_closed = True
            self.date_finished = datetime.now(timezone.utc)

    def add_comment(self, comment: Comment) -> None:
        if self.is_closed:
            raise DomainOperationError("TicketUser is closed; cannot add comments")
        self.comments.append(comment)



    # Convenience methods (optional)

    def confirm(self, actor_employee_id: int) -> None:
        self.change_status(StatusTicketOfClient.CONFIRMED, actor_employee_id)

    def start_work(self, actor_employee_id: int) -> None:
        self.change_status(StatusTicketOfClient.AT_WORK, actor_employee_id)

    def execute(self, actor_employee_id: int) -> None:
        self.change_status(StatusTicketOfClient.EXECUTED, actor_employee_id)

    def cancel_by_client(self, actor_employee_id: int) -> None:
        self.change_status(StatusTicketOfClient.CANCELED_BY_CLIENT, actor_employee_id)

    def cancel_by_admin(self, actor_employee_id: int) -> None:
        self.change_status(StatusTicketOfClient.CANCELED_BY_ADMIN, actor_employee_id)
