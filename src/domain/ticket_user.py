from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class StatusTicketUser(Enum):
    ACCEPT="accept_ticket",
    CONFIRM="confirm_ticket",
    WORK="work_ticket",
    EXECUTE="execute_ticket",
    CANCEL="cancel_ticket",



@dataclass(kw_only=True)
class TicketUser:
    ticket_id: int
    client_id: int
    user_id: int = 0
    status: StatusTicketUser = StatusTicketUser.ACCEPT
    description:str=""
    date_created:datetime = field(default_factory=datetime.now)
    comment:str=""