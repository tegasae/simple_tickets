from dataclasses import dataclass, field, InitVar
from datetime import datetime
from enum import Enum
from typing import Self

from src.domain.exceptions import DomainOperationError


class StatusTicketOfClient(Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    AT_WORK = "at work"
    EXECUTED = "executed"
    CANCELED_BY_ADMIN = "canceled_by_admin"
    CANCELED_BY_CLIENT = "canceled_by_client"

    @classmethod
    def can_transition(cls, from_status: Self, to_status: Self) -> bool:
        """Business rule 3: Define valid status transitions"""
        transitions = {
            cls.CREATED: [cls.AT_WORK, cls.CANCELED_BY_CLIENT, cls.CANCELED_BY_ADMIN],
            cls.AT_WORK: [cls.CREATED, cls.EXECUTED, cls.CANCELED_BY_ADMIN],
            cls.EXECUTED: [],
            cls.CANCELED_BY_CLIENT: [],
            cls.CANCELED_BY_ADMIN: []
        }
        return to_status in transitions.get(from_status, [])


@dataclass(frozen=True, kw_only=True)
class Status:
    date_created: datetime = field(default_factory=datetime.now)
    status:StatusTicketOfClient
    employee_id:int

@dataclass(frozen=True, kw_only=True)
class Comment:
    date_created: datetime = field(default_factory=datetime.now)
    comment:str
    employee_id:int




@dataclass(kw_only=True)
class TicketUser:
    ticket_id: int
    client_id: int
    created_by_employee_id: InitVar[int]  # передаём, но не храним как поле
    statuses:list[Status]=field(default_factory=list)
    comments:list[Comment]=field(default_factory=list)
    description:str
    date_created:datetime = field(default_factory=datetime.now)
    version=0

    def __post_init__(self, created_by_employee_id: int) -> None:
        if not self.statuses:
            self.statuses.append(
                Status(
                    status=StatusTicketOfClient.CREATED,
                    employee_id=created_by_employee_id,
                )
            )

    def change_status(self, new_status: StatusTicketOfClient,employee_id:int) -> None:
        if not StatusTicketOfClient.can_transition(self.statuses[-1].status, new_status):
            raise DomainOperationError(f"Cannot change status from {self.statuses[-1].status} to {new_status.value}")

        self.statuses.append(Status(status=new_status,employee_id=employee_id))
        self.version += 1


if __name__=="__main__":
    ticket_user=TicketUser(ticket_id=1, client_id=1,created_by_employee_id=10,description="111")
    print(ticket_user)