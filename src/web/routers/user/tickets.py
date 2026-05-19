from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.application.dto.ticket_dto import TicketUserDTO
from src.application.services.ticket_user_service import TicketUserApplicationService
from src.domain.exceptions import DomainOperationError
from src.web.dependicies.auth import require_current_user
from src.web.dependicies.services import get_ticket_user_service

router = APIRouter(
    prefix="/user/tickets",
    tags=["user tickets"],
)


class UserTicketCreateRequest(BaseModel):
    client_id: int
    contact_user_id: int = 0
    description: str


class UserTicketCancelRequest(BaseModel):
    comment: str


@router.post("/",response_model=None)
def create_ticket(
    request: UserTicketCreateRequest,
    actor_user_id: int = Depends(require_current_user),
    service: TicketUserApplicationService = Depends(get_ticket_user_service),
):
    try:
        dto = TicketUserDTO(
            ticket_id=0,
            user_id=actor_user_id,
            contact_user_id=request.contact_user_id or actor_user_id,
            client_id=request.client_id,
            description=request.description,
        )

        return service.create_ticket(ticket_user_dto=dto)

    except DomainOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{ticket_id}",response_model=None)
def get_ticket(
    ticket_id: int,
    client_id: int,
    actor_user_id: int = Depends(require_current_user),
    service: TicketUserApplicationService = Depends(get_ticket_user_service),
):
    try:
        dto = TicketUserDTO(
            ticket_id=ticket_id,
            user_id=actor_user_id,
            client_id=client_id,
        )

        return service.get_by_ticket_id(ticket_user_dto=dto)

    except DomainOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{ticket_id}/cancel",response_model=None)
def cancel_ticket(
    ticket_id: int,
    client_id: int,
    request: UserTicketCancelRequest,
    actor_user_id: int = Depends(require_current_user),
    service: TicketUserApplicationService = Depends(get_ticket_user_service),
):
    try:
        dto = TicketUserDTO(
            ticket_id=ticket_id,
            user_id=actor_user_id,
            client_id=client_id,
            comment=request.comment,
        )

        return service.cancel(ticket_user_dto=dto)

    except DomainOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))