from src.web.models.ticket_input import TicketDescriptionText
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.domain.ticket_components import TicketUrgency
from src.web.models.base_response import BaseResponse
from src.web.models.ticket_input import (
    RequiredTicketCommentText, TicketCommentText, TicketText,
)


class UserTicketRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )


class UserTicketCreateRequest(UserTicketRequest):
    text_of_ticket: TicketText

    contact_user_id: int = Field(
        default=0,
        ge=0,
    )


    description: TicketDescriptionText = ""

    remote_work_recommended: bool = False

    urgency: TicketUrgency = TicketUrgency.NORMAL

    comment: TicketCommentText = ""


class UserTicketActionRequest(UserTicketRequest):
    comment: TicketCommentText = ""


class UserTicketCommentRequest(UserTicketRequest):
    comment: RequiredTicketCommentText


class UserTicketDescriptionRequest(UserTicketRequest):
    description: TicketDescriptionText = ""


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
