from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from src.application.dto.ticket_dto import TicketUserDTO
from src.domain.exceptions import DomainError
from src.web.dependencies.auth import require_current_user
from src.web.dependencies.services import get_ticket_user_service

router = APIRouter(prefix="/user/tickets", tags=["user tickets"])


class UserTicketCreateRequest(BaseModel):
    client_id: int
    description: str
    contact_user_id: int = 0


class UserTicketCommentRequest(BaseModel):
    client_id: int
    comment: str


class UserTicketCancelRequest(BaseModel):
    client_id: int
    comment: str = ""


def _domain_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/", response_model=None)
def create_ticket(
    request: UserTicketCreateRequest,
    actor_user_id: int = Depends(require_current_user),
    service = Depends(get_ticket_user_service),
):
    try:
        dto = TicketUserDTO(
            ticket_id=0,
            client_id=request.client_id,
            user_id=actor_user_id,
            contact_user_id=request.contact_user_id or actor_user_id,
            description=request.description,
        )
        return jsonable_encoder(service.create_ticket(ticket_user_dto=dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.get("/", response_model=None)
def get_my_tickets(
    client_id: int = Query(...),
    actor_user_id: int = Depends(require_current_user),
    service = Depends(get_ticket_user_service),
):
    try:
        dto = TicketUserDTO(
            ticket_id=0,
            client_id=client_id,
            user_id=actor_user_id,
            contact_user_id=actor_user_id,
        )
        return jsonable_encoder(service.get_all_own(ticket_user_dto=dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.get("/{ticket_id}", response_model=None)
def get_ticket(
    ticket_id: int,
    client_id: int = Query(...),
    actor_user_id: int = Depends(require_current_user),
    service = Depends(get_ticket_user_service),
):
    try:
        dto = TicketUserDTO(
            ticket_id=ticket_id,
            client_id=client_id,
            user_id=actor_user_id,
            contact_user_id=actor_user_id,
        )
        return jsonable_encoder(service.get_by_ticket_id(ticket_user_dto=dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.post("/{ticket_id}/comments", response_model=None)
def add_comment(
    ticket_id: int,
    request: UserTicketCommentRequest,
    actor_user_id: int = Depends(require_current_user),
    service = Depends(get_ticket_user_service),
):
    try:
        dto = TicketUserDTO(
            ticket_id=ticket_id,
            client_id=request.client_id,
            user_id=actor_user_id,
            contact_user_id=actor_user_id,
            comment=request.comment,
        )
        return jsonable_encoder(service.add_comment(ticket_user_dto=dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.patch("/{ticket_id}/cancel", response_model=None)
def cancel_ticket(
    ticket_id: int,
    request: UserTicketCancelRequest,
    actor_user_id: int = Depends(require_current_user),
    service = Depends(get_ticket_user_service),
):
    try:
        dto = TicketUserDTO(
            ticket_id=ticket_id,
            client_id=request.client_id,
            user_id=actor_user_id,
            contact_user_id=actor_user_id,
            comment=request.comment,
        )
        return jsonable_encoder(service.cancel(ticket_user_dto=dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.delete("/{ticket_id}", response_model=None)
def delete_ticket(
    ticket_id: int,
    client_id: int = Query(...),
    actor_user_id: int = Depends(require_current_user),
    service = Depends(get_ticket_user_service),
):
    try:
        dto = TicketUserDTO(
            ticket_id=ticket_id,
            client_id=client_id,
            user_id=actor_user_id,
            contact_user_id=actor_user_id,
        )
        service.delete(ticket_user_dto=dto)
        return {"status": "deleted", "ticket_id": ticket_id}
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)
