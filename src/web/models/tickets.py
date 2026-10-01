# src/web/models/tickets.py

from datetime import datetime, UTC
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.ticket import TicketUrgency


# =====================================================================
# Creation
# =====================================================================


class TicketCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: int
    text_of_ticket: str
    description: str = ""

    user_id: int = 0
    contact_user_id: int = 0
    department_id: int = 0

    remote_work_recommended: bool = False
    urgency: str = "normal"

    planned_at: datetime | None = None

    comment: str = ""

    @field_validator("planned_at")
    @classmethod
    def normalize_planned_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError(
                "planned_at must contain timezone"
            )

        return value.astimezone(UTC)

class TicketCreateForUserRequest(TicketCreateRequest):
    """
    Admin creates TicketUser and corresponding internal Ticket.
    """

    user_id: int = Field(gt=0)


# =====================================================================
# Ticket data
# =====================================================================






class TicketCommentBaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str = ""


class TicketCommentRequest(TicketCommentBaseRequest):
    pass


class TicketRequiredCommentRequest(TicketCommentBaseRequest):
    comment: str = Field(min_length=1)


class TicketAcceptRequest(TicketCommentRequest):
    pass


class TicketRejectRequest(TicketRequiredCommentRequest):
    pass


class TicketDeferRequest(TicketRequiredCommentRequest):
    pass


class TicketDescriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = ""


class TicketContactUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contact_user_id: int = Field(ge=0)


class TicketChangeDepartmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    department_id: int = Field(ge=0)


class TicketRemoteWorkRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remote_work_recommended: bool


class TicketUrgencyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    urgency: TicketUrgency


# =====================================================================
# Planning
# =====================================================================


class TicketScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    planned_at: datetime


# =====================================================================
# Workflow
# =====================================================================




class TicketAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executor_id: int = Field(gt=0)
    comment: str = ""


# =====================================================================
# Work
# =====================================================================


class TicketStartWorkRequest(BaseModel):
    """
    Normal ASSIGNED -> AT_WORK.

    work_is_remote describes this concrete work episode.
    """

    model_config = ConfigDict(extra="forbid")

    work_is_remote: bool = False
    comment: str = ""


class TicketStartRemoteWorkRequest(BaseModel):
    """
    Special operation for Ticket where remote work is recommended.

    Work mode is always remote, therefore work_is_remote is not supplied.
    """

    model_config = ConfigDict(extra="forbid")

    comment: str = ""


class TicketPauseWorkRequest(TicketCommentRequest):
    pass


class TicketResumeWorkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_is_remote: bool = False
    comment: str = ""


class TicketFinishWorkRequest(TicketCommentRequest):
    """
    Finish current work.

    Application layer may additionally perform EXECUTED when actor
    has TICKET_EXECUTED.
    """

    pass


class TicketCompleteWorkRetroactivelyRequest(BaseModel):
    """
    Register already completed work.

    Domain validates that either:

        actual_started_at + actual_finished_at

    or:

        positive duration

    is supplied.
    """

    model_config = ConfigDict(extra="forbid")

    work_is_remote: bool = False

    actual_started_at: datetime | None = None
    actual_finished_at: datetime | None = None

    duration: int=0

    comment: str = ""


# =====================================================================
# Finalization
# =====================================================================


class TicketExecuteRequest(TicketCommentRequest):
    pass


class TicketCancelRequest(TicketRequiredCommentRequest):
    pass


# =====================================================================
# Response
# =====================================================================


class TicketResponse(BaseModel):
    """
    Web representation of internal Ticket.

    Field names must correspond to TicketResponseDTO.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    ticket_id: int

    client_id: int

    user_id: int
    contact_user_id: int
    user_ticket_id: int

    department_id: int

    text_of_ticket: str
    description: str

    date_created: datetime
    date_finished: datetime | None

    planned_at: datetime | None = None

    remote_work_recommended: bool

    urgency: TicketUrgency

    version: int
    is_closed: bool

    time_spent: int = 0

    statuses: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    comments: list[dict[str, Any]] = Field(
        default_factory=list,
    )