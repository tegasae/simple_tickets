# src/web/routers/user/tickets.py

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

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
    contact_user_id: int = Field(default=0, ge=0)

    text_of_ticket: str = Field(min_length=1)
    description: str = ""

    urgency_level: int = Field(default=0, ge=0)
    department_id: int = Field(default=0, ge=0)
    is_remote: bool = False

    comment: str = ""


class UserTicketActionRequest(BaseModel):
    """
    Временный вариант.

    Сейчас TicketUserApplicationService.cancel_by_user()
    и confirm_execution_by_user() требуют оба id:

        ticket_id       -> internal Ticket
        ticket_user_id  -> external TicketUser

    Поэтому ticket_id пока передаётся в body.
    Позже лучше убрать это из web API и искать Ticket внутри сервиса
    через get_by_user_ticket_id(ticket_user_id).
    """

    ticket_id: int = Field(gt=0)
    comment: str = ""


def _domain_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


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
        text_of_ticket=request.text_of_ticket,
        description=request.description,
        urgency_level=request.urgency_level,
        department_id=request.department_id,
        is_remote=request.is_remote,
        comment=request.comment,
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
        text_of_ticket="",
        description="",
        urgency_level=0,
        department_id=0,
        is_remote=False,
        comment=request.comment,
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
        text_of_ticket="",
        description="",
        urgency_level=0,
        department_id=0,
        is_remote=False,
        comment="",
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
        text_of_ticket="",
        description="",
        urgency_level=0,
        department_id=0,
        is_remote=False,
        comment="",
    )


@router.post(
    "/",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
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

        return jsonable_encoder(
            service.create_from_user(ticket_user_dto=dto),
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/",
    response_model=None,
    status_code=status.HTTP_200_OK,
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

        return jsonable_encoder(
            service.get_by_user(ticket_user_dto=dto),
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/{ticket_user_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
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

        return jsonable_encoder(
            service.get_by_id(ticket_user_dto=dto),
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.patch(
    "/{ticket_user_id}/cancel",
    response_model=None,
    status_code=status.HTTP_200_OK,
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

        return jsonable_encoder(
            service.cancel_by_user(ticket_user_dto=dto),
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.patch(
    "/{ticket_user_id}/confirm-execution",
    response_model=None,
    status_code=status.HTTP_200_OK,
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

        return jsonable_encoder(
            service.confirm_execution_by_user(ticket_user_dto=dto),
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc