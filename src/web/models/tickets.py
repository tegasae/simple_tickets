# src/web/models/tickets.py

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TicketCreateRequest(BaseModel):
    client_id: int = Field(gt=0)

    text_of_ticket: str = Field(min_length=1)
    description: str = ""

    user_id: int = Field(default=0, ge=0)
    contact_user_id: int = Field(default=0, ge=0)

    department_id: int = Field(default=0, ge=0)

    is_remote: bool = False
    urgency_level: int = Field(default=0, ge=0)

    comment: str = ""


class TicketCommentRequest(BaseModel):
    comment: str = ""


class TicketRequiredCommentRequest(BaseModel):
    comment: str = Field(min_length=1)


class TicketAcceptRequest(TicketCommentRequest):
    pass


class TicketRejectRequest(TicketRequiredCommentRequest):
    pass


class TicketDeferRequest(TicketRequiredCommentRequest):
    pass


class TicketChangeDepartmentRequest(BaseModel):
    department_id:int


class TicketUpdateDetailsRequest(BaseModel):
    description:str=""
    contact_user_id: int = Field(default=0, ge=0)
    is_remote: bool = False

class TicketScheduleRequest(BaseModel):
    planned_start_at: datetime
    planned_finish_at: datetime | None = None
    comment: str = ""


class TicketAssignExecutorRequest(BaseModel):
    executor_id: int = Field(gt=0)
    comment: str = ""


class TicketReadyToWorkRequest(BaseModel):
    executor_id: int = Field(gt=0)
    planned_start_at: datetime
    planned_finish_at: datetime | None = None
    comment: str = ""


class TicketStartWorkRequest(BaseModel):
    comment: str = ""


class TicketPauseWorkRequest(BaseModel):
    comment: str = ""


class TicketResumeWorkRequest(BaseModel):
    comment: str = ""


class TicketSubmitForReviewRequest(BaseModel):
    comment: str = ""


class TicketRecordCompletedWorkForReviewRequest(BaseModel):
    executor_id: int = Field(gt=0)
    actual_started_at: datetime
    actual_finished_at: datetime
    comment: str = ""


class TicketExecuteRequest(BaseModel):
    comment: str = ""


class TicketConfirmExecutionRequest(BaseModel):
    comment: str = ""


class TicketReturnToWorkRequest(BaseModel):
    comment: str = ""


class TicketReturnToAssignedRequest(BaseModel):
    executor_id: int = Field(gt=0)
    comment: str = ""


class TicketReturnToScheduledRequest(BaseModel):
    planned_start_at: datetime
    planned_finish_at: datetime | None = None
    comment: str = ""


class TicketReturnToReadyToWorkRequest(BaseModel):
    executor_id: int = Field(gt=0)
    planned_start_at: datetime
    planned_finish_at: datetime | None = None
    comment: str = ""


class TicketReturnToDeferredRequest(TicketRequiredCommentRequest):
    pass


class TicketCancelRequest(TicketRequiredCommentRequest):
    pass


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket_id: int

    client_id: int
    admin_id: int

    user_id: int
    contact_user_id: int
    user_ticket_id: int

    department_id: int

    text_of_ticket: str
    description: str

    date_created: datetime
    date_finished: datetime | None

    is_remote: bool
    urgency_level: int

    version: int
    is_closed: bool
    time_spent:int
    statuses: list[dict[str, Any]]
    comments: list[dict[str, Any]]