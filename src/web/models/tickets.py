# src/web/models/tickets.py

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TicketCreateRequest(BaseModel):
    """
    Request body for creating admin ticket.

    actor_admin_id/admin_id are NOT here.
    They come from JWT / request context.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int

    text_of_ticket: str = ""

    user_id: int = 0
    contact_user_id: int = 0
    user_ticket_id: int = 0

    executor_id: int = 0

    is_remote: bool = False
    urgency_level: int = 0

    comment: str = ""


class TicketDeferRequest(BaseModel):
    """
    Optional body for deferring ticket.

    If your domain does not need comment here,
    you can remove comment field.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int
    comment: str = ""


class TicketStartWorkRequest(BaseModel):
    """
    Request body for moving ticket to AT_WORK.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int
    executor_id: int


class TicketExecuteRequest(BaseModel):
    """
    Request body for executing ticket.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int
    comment: str


class TicketCancelRequest(BaseModel):
    """
    Request body for cancelling ticket.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int
    comment: str


class TicketCommentRequest(BaseModel):
    """
    Request body for adding comment.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int
    comment: str


class TicketAssignExecutorRequest(BaseModel):
    """
    Request body for assigning executor.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int
    executor_id: int


class TicketResponse(BaseModel):
    """
    Web response model.

    It can be created from TicketResponseDTO dataclass using:

        TicketResponse.model_validate(dto)

    because from_attributes=True.

    Some fields are optional/defaulted intentionally:
    your TicketResponseDTO may contain description instead of text_of_ticket,
    or may not expose all history fields yet.
    """

    model_config = ConfigDict(from_attributes=True)

    ticket_id: int = 0
    client_id: int = 0

    admin_id: int = 0
    user_id: int = 0
    contact_user_id: int = 0
    executor_id: int = 0
    user_ticket_id: int = 0

    text_of_ticket: str = ""
    description: str = ""

    status: str = ""
    is_closed: bool = False

    is_remote: bool = False
    urgency_level: int = 0

    comment: str = ""

    date_created: str = ""
    date_finished: str = ""

    version: int = 0

    @field_validator(
        "text_of_ticket",
        "description",
        "status",
        "comment",
        "date_created",
        "date_finished",
        mode="before",
    )
    @classmethod
    def none_to_empty_string(cls, value):
        return "" if value is None else value


    