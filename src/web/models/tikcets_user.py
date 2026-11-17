from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.domain.ticket_components import TicketUrgency
from src.web.models.base_response import BaseResponse


class UserTicketRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )


class UserTicketCreateRequest(UserTicketRequest):
    client_id: int = Field(
        gt=0,
    )

    text_of_ticket: str = Field(
        min_length=1,
    )

    contact_user_id: int = Field(
        default=0,
        ge=0,
    )

    department_id: int = Field(
        default=0,
        ge=0,
    )

    description: str = ""

    remote_work_recommended: bool = False

    urgency: TicketUrgency = TicketUrgency.NORMAL

    comment: str = ""


class UserTicketActionRequest(UserTicketRequest):
    comment: str = ""


class UserTicketCommentRequest(UserTicketRequest):
    comment: str = Field(
        min_length=1,
    )


class UserTicketDescriptionRequest(UserTicketRequest):
    description: str = ""


class UserTicketContactUserRequest(UserTicketRequest):
    contact_user_id: int = Field(
        ge=0,
    )


class TicketUserResponse(BaseResponse):
    model_config = ConfigDict(
        from_attributes=True,
    )

    ticket_user_id: int

    client_id: int
    user_id: int
    contact_user_id: int

    text_of_ticket: str
    description: str

    current_status: str

    date_created: datetime
    date_finished: datetime | None

    is_closed: bool

    statuses: list[dict[str, Any]]
    comments: list[dict[str, Any]]
