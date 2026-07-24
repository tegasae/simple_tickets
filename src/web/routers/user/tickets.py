# src/web/routers/user/tickets.py

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from src.application.dto.ticket_dto import TicketUserDTO
from src.domain.exceptions import DomainError
from src.web.dependencies.auth import (
    get_current_user,
    get_employee_id_from_request,
)
from src.web.dependencies.services import get_ticket_user_service


router = APIRouter(
    prefix="/user/tickets",
    tags=["user tickets"],
    dependencies=[Depends(get_current_user)],
)


class UserTicketCreateRequest(BaseModel):
    client_id: int = Field(gt=0)

    text_of_ticket: str = Field(min_length=1)
    description: str = ""

    contact_user_id: int = Field(default=0, ge=0)
    department_id: int = Field(default=0, ge=0)

    is_remote: bool = False
    urgency_level: int = Field(default=0, ge=0)

    comment: str = ""


class UserTicketActionRequest(BaseModel):
    """
    Временный web-контракт.

    Сейчас TicketUserApplicationService.cancel_by_user()
    и TicketUserApplicationService.confirm_execution_by_user()
    требуют два id:

        ticket_id       -> внутренняя Ticket
        ticket_user_id  -> пользовательская TicketUser

    Поэтому internal ticket_id пока передаётся в body.

    Позже лучше убрать ticket_id из пользовательского API и внутри
    application service искать внутреннюю Ticket так:

        uow.tickets.get_by_user_ticket_id(ticket_user_id)
    """

    ticket_id: int = Field(gt=0)
    comment: str = ""


class UserTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket_id: int

    client_id: int
    user_id: int
    contact_user_id: int

    text_of_ticket: str
    description: str
    urgency_level: int

    current_status: str
    is_closed: bool

    date_created: str
    date_finished: str | None

    statuses: list[dict[str, Any]]
    comments: list[dict[str, Any]]


handlers = {
    "DomainOperationError": 400,
    "DomainSecurityError": 403,
    "ItemValidationError": 400,
    "ItemNotFoundError": 404,

    "TicketError": 500,
    "TicketNotFoundError": 404,
    "TicketValidationError": 400,
    "TicketOperationError": 400,
    "TicketSecurityError": 403,

    "UserNotFoundError": 404,
    "ClientNotFoundError": 404,
    "UserValidationError": 400,
    "ClientValidationError": 400,
}


# ---------------------------------------------------------------------
# Error mapper
# ---------------------------------------------------------------------

def _domain_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# ---------------------------------------------------------------------
# Response mappers
# ---------------------------------------------------------------------

def to_user_ticket_response(response_dto) -> UserTicketResponse:
    return UserTicketResponse.model_validate(response_dto)


def to_user_ticket_responses(response_dtos) -> list[UserTicketResponse]:
    return [
        to_user_ticket_response(response_dto)
        for response_dto in response_dtos
    ]


# ---------------------------------------------------------------------
# Request -> Application DTO mappers
# ---------------------------------------------------------------------

def create_request_to_dto(
    *,
    request: UserTicketCreateRequest,
    actor_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        ticket_id=0,
        ticket_user_id=0,
        actor_user_id=actor_user_id,
        client_id=request.client_id,
        contact_user_id=request.contact_user_id,
        department_id=request.department_id,
        is_remote=request.is_remote,
        text_of_ticket=request.text_of_ticket,
        description=request.description,
        urgency_level=request.urgency_level,
        comment=request.comment,
    )


def user_filter_to_dto(
    *,
    actor_user_id: int,
    client_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        ticket_id=0,
        ticket_user_id=0,
        actor_user_id=actor_user_id,
        client_id=client_id,
        contact_user_id=0,
        department_id=0,
        is_remote=False,
        text_of_ticket="",
        description="",
        urgency_level=0,
        comment="",
    )


def ticket_user_id_to_dto(
    *,
    actor_user_id: int,
    ticket_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        ticket_id=0,
        ticket_user_id=ticket_user_id,
        actor_user_id=actor_user_id,
        client_id=0,
        contact_user_id=0,
        department_id=0,
        is_remote=False,
        text_of_ticket="",
        description="",
        urgency_level=0,
        comment="",
    )


def action_request_to_dto(
    *,
    request: UserTicketActionRequest,
    actor_user_id: int,
    ticket_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        ticket_id=request.ticket_id,
        ticket_user_id=ticket_user_id,
        actor_user_id=actor_user_id,
        client_id=0,
        contact_user_id=0,
        department_id=0,
        is_remote=False,
        text_of_ticket="",
        description="",
        urgency_level=0,
        comment=request.comment,
    )


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------

@router.post(
    "/",
    response_model=UserTicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user ticket",
)
def create_ticket(
    request: UserTicketCreateRequest,
    actor_user_id: int = Depends(get_employee_id_from_request),
    service=Depends(get_ticket_user_service),
):
    try:
        dto = create_request_to_dto(
            request=request,
            actor_user_id=actor_user_id,
        )

        response_dto = service.create_from_user(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/",
    response_model=list[UserTicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user tickets",
)
def get_my_tickets(
    client_id: int = Query(..., gt=0),
    actor_user_id: int = Depends(get_employee_id_from_request),
    service=Depends(get_ticket_user_service),
):
    try:
        dto = user_filter_to_dto(
            actor_user_id=actor_user_id,
            client_id=client_id,
        )

        response_dtos = service.get_by_user(
            ticket_user_dto=dto,
        )

        return to_user_ticket_responses(response_dtos)

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
    actor_user_id: int = Depends(get_employee_id_from_request),
    service=Depends(get_ticket_user_service),
):
    try:
        dto = ticket_user_id_to_dto(
            actor_user_id=actor_user_id,
            ticket_user_id=ticket_user_id,
        )

        response_dto = service.get_by_id(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.patch(
    "/{ticket_user_id}/cancel",
    response_model=UserTicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel user ticket",
)
def cancel_ticket(
    ticket_user_id: int,
    request: UserTicketActionRequest,
    actor_user_id: int = Depends(get_employee_id_from_request),
    service=Depends(get_ticket_user_service),
):
    try:
        dto = action_request_to_dto(
            request=request,
            actor_user_id=actor_user_id,
            ticket_user_id=ticket_user_id,
        )

        response_dto = service.cancel_by_user(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.patch(
    "/{ticket_user_id}/confirm-execution",
    response_model=UserTicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm ticket execution",
)
def confirm_execution(
    ticket_user_id: int,
    request: UserTicketActionRequest,
    actor_user_id: int = Depends(get_employee_id_from_request),
    service=Depends(get_ticket_user_service),
):
    try:
        dto = action_request_to_dto(
            request=request,
            actor_user_id=actor_user_id,
            ticket_user_id=ticket_user_id,
        )

        response_dto = service.confirm_execution_by_user(
            ticket_user_dto=dto,
        )

        return to_user_ticket_response(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc