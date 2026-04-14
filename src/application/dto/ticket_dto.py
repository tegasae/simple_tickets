from dataclasses import dataclass
from src.domain.ticket import TicketStatus


@dataclass(kw_only=True,frozen=True)
class TicketDTO:
    actor_admin_id: int
    client_id: int=0
    admin_id: int=0
    description: str=""
    text_of_ticket: str=""
    user_id: int=0
    contact_user_id: int=0
    is_remote: bool = False
    urgency_level: int=0
    user_ticket_id: int=0
    executor_id: int=0
    comment: str=""
    status:TicketStatus=TicketStatus.CREATED


@dataclass(kw_only=True,frozen=True)
class TicketResponseDTO:
    ticket_id: int
    date_created: str
    date_finished: str
    description:str
    text_of_ticket:str
    user_id: int
    contact_user_id: int
    is_remote: bool
    urgency_level: int
    user_ticket_id: int
    statuses: list[dict]
    comments: list[dict]
    executors: list[dict]

