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
            cls.CONFIRMED: [cls.AT_WORK, cls.CANCELED_BY_CLIENT, cls.CANCELED_BY_ADMIN],
            cls.AT_WORK: [cls.CREATED, cls.EXECUTED, cls.CANCELED_BY_ADMIN],
            cls.EXECUTED: [],
            cls.CANCELED_BY_CLIENT: [],
            cls.CANCELED_BY_ADMIN: []
        }
        return to_status in transitions.get(from_status, [])


@dataclass(frozen=True, kw_only=True)
class Status:
    employee_id: int
    status:StatusTicketOfClient
    date_created: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, kw_only=True)
class Comment:
    employee_id: int
    comment: str
    date_created: datetime = field(default_factory=datetime.now)



@dataclass
class Executor:
    id_admin: int
    date_created: datetime = field(default_factory=datetime.now)

@dataclass(kw_only=True)
class TicketUser:
    ticket_id: int
    client_id: int
    created_by_employee_id: InitVar[int]  # передаём, но не храним как поле
    statuses:list[Status]=field(default_factory=list)
    comments:list[Comment]=field(default_factory=list)
    executors:list[Executor]=field(default_factory=list)
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

    def add_comment(self, comment:Comment) -> None:
        self.comments.append(comment)
        self.version += 1



    def get_current_state(self) -> StatusTicketOfClient:
        return self.statuses[-1].status


    def add_executor(self, new_executor:Executor) -> None:
        self.executors.append(new_executor)

    def get_current_executor(self) -> Executor:
        try:
            return self.executors[-1]
        except IndexError:
            raise DomainOperationError(message="No executor available")


