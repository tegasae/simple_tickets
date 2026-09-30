# src/web/routers/user/tickets.py

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from src.application.dto.ticket_dto import (
    TicketUserDTO,
    TicketUserResponseDTO,
)
from src.application.services.ticket_user_service import TicketUserApplicationService

from src.domain.exceptions import DomainError
from src.domain.ticket import TicketUrgency
from src.web.dependencies.auth import (
    get_current_user,
    get_employee_id_from_request,
)
from src.web.dependencies.services import (
    get_ticket_user_service,
)


router = APIRouter(
    prefix="/user/tickets",
    tags=["user tickets"],
    dependencies=[
        Depends(get_current_user),
    ],
)


# =====================================================================
# Request models
# =====================================================================


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


# =====================================================================
# Response model
# =====================================================================


class UserTicketResponse(BaseModel):
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

    version: int
    is_closed: bool

    statuses: list[dict[str, Any]]
    comments: list[dict[str, Any]]


# =====================================================================
# Error mapping
# =====================================================================


ERROR_STATUS_CODES = {
    "DomainOperationError": status.HTTP_400_BAD_REQUEST,
    "DomainSecurityError": status.HTTP_403_FORBIDDEN,
    "ItemValidationError": status.HTTP_400_BAD_REQUEST,
    "ItemNotFoundError": status.HTTP_404_NOT_FOUND,

    "TicketError": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "TicketNotFoundError": status.HTTP_404_NOT_FOUND,
    "TicketValidationError": status.HTTP_400_BAD_REQUEST,
    "TicketOperationError": status.HTTP_400_BAD_REQUEST,
    "TicketSecurityError": status.HTTP_403_FORBIDDEN,

    "UserNotFoundError": status.HTTP_404_NOT_FOUND,
    "ClientNotFoundError": status.HTTP_404_NOT_FOUND,
    "UserValidationError": status.HTTP_400_BAD_REQUEST,
    "ClientValidationError": status.HTTP_400_BAD_REQUEST,
}


def _domain_error(
    exc: Exception,
) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    status_code = ERROR_STATUS_CODES.get(
        type(exc).__name__,
        status.HTTP_400_BAD_REQUEST,
    )

    return HTTPException(
        status_code=status_code,
        detail=str(exc),
    )


# =====================================================================
# Response mappers
# =====================================================================


def to_user_ticket_response(
    response_dto: TicketUserResponseDTO,
) -> UserTicketResponse:
    return UserTicketResponse.model_validate(
        response_dto
    )


def to_user_ticket_responses(
    response_dtos: list[TicketUserResponseDTO],
) -> list[UserTicketResponse]:
    return [
        to_user_ticket_response(response_dto)
        for response_dto in response_dtos
    ]


# =====================================================================
# Request -> Application DTO mappers
# =====================================================================


def create_request_to_dto(
    *,
    request: UserTicketCreateRequest,
    actor_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        actor_user_id=actor_user_id,
        ticket_user_id=0,
        client_id=request.client_id,
        user_id=actor_user_id,
        text_of_ticket=request.text_of_ticket,
        contact_user_id=request.contact_user_id,
        department_id=request.department_id,
        description=request.description,
        remote_work_recommended=(
            request.remote_work_recommended
        ),
        urgency=request.urgency,
        comment=request.comment,
    )


def actor_to_dto(
    *,
    actor_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        actor_user_id=actor_user_id,
    )


def user_filter_to_dto(
    *,
    actor_user_id: int,
    user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        actor_user_id=actor_user_id,
        user_id=user_id,
    )


def ticket_user_id_to_dto(
    *,
    actor_user_id: int,
    ticket_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        actor_user_id=actor_user_id,
        ticket_user_id=ticket_user_id,
    )


def action_request_to_dto(
    *,
    request: UserTicketActionRequest,
    actor_user_id: int,
    ticket_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        actor_user_id=actor_user_id,
        ticket_user_id=ticket_user_id,
        comment=request.comment,
    )


def comment_request_to_dto(
    *,
    request: UserTicketCommentRequest,
    actor_user_id: int,
    ticket_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        actor_user_id=actor_user_id,
        ticket_user_id=ticket_user_id,
        comment=request.comment,
    )


def description_request_to_dto(
    *,
    request: UserTicketDescriptionRequest,
    actor_user_id: int,
    ticket_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        actor_user_id=actor_user_id,
        ticket_user_id=ticket_user_id,
        description=request.description,
    )


def contact_user_request_to_dto(
    *,
    request: UserTicketContactUserRequest,
    actor_user_id: int,
    ticket_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        actor_user_id=actor_user_id,
        ticket_user_id=ticket_user_id,
        contact_user_id=request.contact_user_id,
    )


# =====================================================================
# Creation
# =====================================================================


@router.post(
    "/",
    response_model=UserTicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user ticket",
)
def create_ticket(
    request: UserTicketCreateRequest,
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = create_request_to_dto(
            request=request,
            actor_user_id=user_id,
        )

        response_dto = service.create_from_user(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(
            response_dto
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


# =====================================================================
# Queries
# =====================================================================


@router.get(
    "/",
    response_model=list[UserTicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user tickets",
)
def get_my_tickets(
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = user_filter_to_dto(
            actor_user_id=user_id,
            user_id=user_id,
        )

        response_dtos = service.get_by_user_id(
            ticket_user_dto=dto,
        )

        return to_user_ticket_responses(
            response_dtos
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/all",
    response_model=list[UserTicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all client user tickets",
)
def get_all_tickets(
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = actor_to_dto(
            actor_user_id=user_id,
        )

        response_dtos = service.get_all(
            ticket_user_dto=dto,
        )

        return to_user_ticket_responses(
            response_dtos
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/open",
    response_model=list[UserTicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get open user tickets",
)
def get_open_tickets(
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = actor_to_dto(
            actor_user_id=user_id,
        )

        response_dtos = service.get_open(
            ticket_user_dto=dto,
        )

        return to_user_ticket_responses(
            response_dtos
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/closed",
    response_model=list[UserTicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get closed user tickets",
)
def get_closed_tickets(
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = actor_to_dto(
            actor_user_id=user_id,
        )

        response_dtos = service.get_closed(
            ticket_user_dto=dto,
        )

        return to_user_ticket_responses(
            response_dtos
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/{ticket_user_id}",
    response_model=UserTicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user ticket by id",
)
def get_ticket(
    ticket_user_id: int,
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = ticket_user_id_to_dto(
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
        )

        response_dto = service.get_by_id(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(
            response_dto
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


# =====================================================================
# TicketUser data
# =====================================================================


@router.post(
    "/{ticket_user_id}/comments",
    response_model=UserTicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Add comment to user ticket",
)
def add_comment(
    ticket_user_id: int,
    request: UserTicketCommentRequest,
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = comment_request_to_dto(
            request=request,
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
        )

        response_dto = service.add_comment(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(
            response_dto
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.patch(
    "/{ticket_user_id}/description",
    response_model=UserTicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user ticket description",
)
def update_description(
    ticket_user_id: int,
    request: UserTicketDescriptionRequest,
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = description_request_to_dto(
            request=request,
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
        )

        response_dto = service.update_description(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(
            response_dto
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.patch(
    "/{ticket_user_id}/contact-user",
    response_model=UserTicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Change user ticket contact user",
)
def change_contact_user(
    ticket_user_id: int,
    request: UserTicketContactUserRequest,
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = contact_user_request_to_dto(
            request=request,
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
        )

        response_dto = service.change_contact_user(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(
            response_dto
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


# =====================================================================
# User workflow
# =====================================================================


@router.patch(
    "/{ticket_user_id}/cancel",
    response_model=UserTicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel user ticket",
)
def cancel_ticket(
    ticket_user_id: int,
    request: UserTicketActionRequest,
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = action_request_to_dto(
            request=request,
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
        )

        response_dto = service.cancel_by_user(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(
            response_dto
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.patch(
    "/{ticket_user_id}/confirm",
    response_model=UserTicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm user ticket completion",
)
def confirm_ticket(
    ticket_user_id: int,
    request: UserTicketActionRequest,
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_ticket_user_service
    ),
):
    try:
        dto = action_request_to_dto(
            request=request,
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
        )

        response_dto = service.confirm_by_user(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(
            response_dto
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc