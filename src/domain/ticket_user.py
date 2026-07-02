# src/domain/ticket_user.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Self

from src.domain.exceptions import DomainOperationError
from src.domain.ticket_components import Comment


# --------------------------------
# Status Enum
# --------------------------------

class StatusTicketOfClient(Enum):

    CREATED = "created" # создана пользователем
    CONFIRMED = "confirmed" # потдверждена, на ее осонове создани Ticket
    AT_WORK = "at_work" # в работе, все состояния Ticket после
    EXECUTED = "executed" # выполнена
    CANCELED_BY_ADMIN = "canceled_by_admin" # отменена Admin
    CANCELED_BY_CLIENT = "canceled_by_client" # отменена User

    @classmethod
    def can_transition(cls, from_status: Self, to_status: Self) -> bool:

        transitions = {
            cls.CREATED: [
                cls.CONFIRMED,
                cls.CANCELED_BY_CLIENT,
                cls.CANCELED_BY_ADMIN,
            ],
            cls.CONFIRMED: [
                cls.AT_WORK,
                cls.CANCELED_BY_CLIENT,
                cls.CANCELED_BY_ADMIN,
            ],
            cls.AT_WORK: [
                cls.EXECUTED,
                cls.CANCELED_BY_ADMIN,
            ],
            cls.EXECUTED: [],
            cls.CANCELED_BY_CLIENT: [],
            cls.CANCELED_BY_ADMIN: [],
        }
    
        return to_status in transitions.get(from_status, [])

    @classmethod
    def status_is_frozen(cls,status:Self)->bool:
        if status in [cls.EXECUTED,cls.CANCELED_BY_CLIENT,cls.CANCELED_BY_ADMIN]:
            return True
        else:
            return False
# --------------------------------
# Status record
# --------------------------------

@dataclass(frozen=True, kw_only=True)
class StatusRecordTicketUser:

    status_id: int = 0
    actor_employee_id: int
    status: StatusTicketOfClient
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, StatusRecordTicketUser) and self.status == other.status


# --------------------------------
# Aggregate
# --------------------------------

@dataclass(kw_only=True)
class TicketUser:

    ticket_id: int
    client_id: int
    user_id: int
    contact_user_id: int
    description: str

    statuses: list[StatusRecordTicketUser] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)

    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    is_closed: bool = False
    date_finished: Optional[datetime] = None

    version: int = 0

    # --------------------------------
    # Aggregate creation
    # --------------------------------

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
        description = description.strip()

        if not description:
            raise DomainOperationError("Ticket description cannot be empty")

        return cls(
            ticket_id=ticket_id,
            client_id=client_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            description=description,
            statuses=[
                StatusRecordTicketUser(
                    actor_employee_id=user_id,
                    status=StatusTicketOfClient.CREATED,
                )
            ],
        )

    @classmethod
    def rehydrate(
            cls,
            *,
            ticket_id: int,
            client_id: int,
            user_id: int,
            contact_user_id: int,
            description: str,
            statuses: list[StatusRecordTicketUser],
            comments: list[Comment] | None = None,
            date_created: datetime,
            is_closed: bool = False,
            date_finished: Optional[datetime] = None,
            version: int = 0,
    ) -> Self:
        if not statuses:
            raise DomainOperationError("Cannot rehydrate TicketUser without status history")

        return cls(
            ticket_id=ticket_id,
            client_id=client_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            description=description,
            statuses=statuses,
            comments=comments or [],
            date_created=date_created,
            is_closed=is_closed,
            date_finished=date_finished,
            version=version,
        )

    def __post_init__(self) -> None:
        """
        Validate and recompute derived state only.

        Important:
        - do not append CREATED here;
        - creation belongs to create();
        - loading from DB belongs to rehydrate().
        """
        self.description = self.description.strip()

        if not self.description:
            raise DomainOperationError("Ticket description cannot be empty")

        if not self.statuses:
            self.is_closed = False
            self.date_finished = None
            return

        current = self.current_status()

        if current in (
                StatusTicketOfClient.EXECUTED,
                StatusTicketOfClient.CANCELED_BY_ADMIN,
                StatusTicketOfClient.CANCELED_BY_CLIENT,
        ):
            self.is_closed = True

            if self.date_finished is None:
                self.date_finished = self.statuses[-1].date_created
        else:
            self.is_closed = False
            self.date_finished = None


    def _ensure_not_closed(self):
        if StatusTicketOfClient.status_is_frozen(self.statuses[-1].status):
            raise DomainOperationError(f"The user ticket {self.ticket_id} is frozen")

    # --------------------------------
    # Queries
    # --------------------------------

    def current_status(self) -> StatusTicketOfClient:

        if not self.statuses:
            raise DomainOperationError("TicketUser has no status history")

        return self.statuses[-1].status

    # --------------------------------
    # Commands
    # --------------------------------

    def change_status(
        self,
        new_status: StatusTicketOfClient,
        actor_employee_id: int,
    ) -> None:

        self._ensure_not_closed()

        current = self.current_status()

        if not StatusTicketOfClient.can_transition(current, new_status):
            raise DomainOperationError(
                f"Cannot change status from {current.value} to {new_status.value}"
            )

        record = StatusRecordTicketUser(
            actor_employee_id=actor_employee_id,
            status=new_status,
        )

        self.statuses.append(record)



        if new_status in (
            StatusTicketOfClient.EXECUTED,
            StatusTicketOfClient.CANCELED_BY_ADMIN,
            StatusTicketOfClient.CANCELED_BY_CLIENT,
        ):
            self.is_closed = True
            self.date_finished = datetime.now(timezone.utc)

    # --------------------------------
    # Comments
    # --------------------------------

    def add_comment(self, comment: Comment) -> None:
        self._ensure_not_closed()


        self.comments.append(comment)



    # --------------------------------
    # Convenience methods
    # --------------------------------

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

    def belong(self, employee_id: int) -> bool:
        if employee_id == self.user_id:
            return True
        if employee_id==self.contact_user_id:
            return True
        for status in self.statuses:
            if status.actor_employee_id == employee_id:
                return True
        for comment in self.comments:
            if comment.employee_id == employee_id:
                return True
        return False
