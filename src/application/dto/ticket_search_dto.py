# src/application/dto/ticket_search_dto.py

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class TicketSearchDTO:
    actor_admin_id: int

    client_id: int = 0
    user_id: int = 0
    admin_id: int = 0
    executor_id: int = 0
    department_id: int = 0

    status: str = ""
    is_closed: bool | None = None

    date_from: datetime | None = None
    date_to: datetime | None = None

    text: str = ""

    limit: int = 100
    offset: int = 0