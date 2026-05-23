from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from src.application.dto.client_dto import ClientDTO
from src.domain.exceptions import DomainError
from src.web.dependencies.auth import require_current_admin
from src.web.dependencies.services import get_client_service

router = APIRouter(prefix="/admin/clients", tags=["admin clients"], dependencies=[])


class ClientCreateRequest(BaseModel):
    name: str
    email: str = ""
    address: str = ""
    phone: str = ""


class ClientUpdateContactRequest(BaseModel):
    email: str = ""
    address: str = ""
    phone: str = ""


def _domain_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/", response_model=None)
def create_client(
    request: ClientCreateRequest,
    actor_admin_id: int = Depends(require_current_admin),
    service = Depends(get_client_service),
):
    try:
        dto = ClientDTO(
            actor_admin_id=actor_admin_id,
            name=request.name,
            email=request.email,
            address=request.address,
            phone=request.phone,
        )
        return jsonable_encoder(service.create_client(dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.get("/", response_model=None)
def get_all_clients(
    actor_admin_id: int = Depends(require_current_admin),
    service = Depends(get_client_service),
):
    try:
        dto = ClientDTO(actor_admin_id=actor_admin_id, name="")
        return jsonable_encoder(service.get_all(dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.get("/{client_id}", response_model=None)
def get_client(
    client_id: int,
    actor_admin_id: int = Depends(require_current_admin),
    service = Depends(get_client_service),
):
    try:
        dto = ClientDTO(actor_admin_id=actor_admin_id, client_id=client_id, name="")
        return jsonable_encoder(service.get_by_id(dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.patch("/{client_id}/contact", response_model=None)
def update_contact(
    client_id: int,
    request: ClientUpdateContactRequest,
    actor_admin_id: int = Depends(require_current_admin),
    service = Depends(get_client_service),
):
    try:
        dto = ClientDTO(
            actor_admin_id=actor_admin_id,
            client_id=client_id,
            name="",
            email=request.email,
            address=request.address,
            phone=request.phone,
        )
        return jsonable_encoder(service.update_contact(dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.patch("/{client_id}/disable", response_model=None)
def disable_client(
    client_id: int,
    actor_admin_id: int = Depends(require_current_admin),
    service = Depends(get_client_service),
):
    try:
        dto = ClientDTO(actor_admin_id=actor_admin_id, client_id=client_id, name="")
        return jsonable_encoder(service.disable(dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.patch("/{client_id}/enable", response_model=None)
def enable_client(
    client_id: int,
    actor_admin_id: int = Depends(require_current_admin),
    service = Depends(get_client_service),
):
    try:
        dto = ClientDTO(actor_admin_id=actor_admin_id, client_id=client_id, name="")
        return jsonable_encoder(service.enable(dto))
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.delete("/{client_id}", response_model=None)
def delete_client(
    client_id: int,
    actor_admin_id: int = Depends(require_current_admin),
    service = Depends(get_client_service),
):
    try:
        dto = ClientDTO(actor_admin_id=actor_admin_id, client_id=client_id, name="")
        service.delete(dto_client=dto)
        return {"status": "deleted", "client_id": client_id}
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)
