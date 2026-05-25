from fastapi import APIRouter, Depends, HTTPException, status

from src.application.dto.client_dto import ClientDTO
from src.domain.exceptions import DomainError

from src.web.dependencies.auth import (
    get_current_admin,
    get_employee_id_from_request,
)
from src.web.dependencies.services import get_application_service_factory
from src.web.models.clients import (
    ClientCreateRequest,
    ClientResponse,
    ClientUpdateContactRequest,
)


router = APIRouter(
    prefix="/admin/clients",
    tags=["admin clients"],
    dependencies=[Depends(get_current_admin)],
)

handlers = {
    'AdminError': 500,
    'DomainSecurityError':403,
    'AdminNotFoundError': 404,
    'AdminAlreadyExistsError': 409,
    'AdminValidationError': 400,
    'AdminOperationError': 400,
    'AdminSecurityError': 403
}



def _domain_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


def client_create_request_to_dto(
    *,
    request: ClientCreateRequest,
    actor_admin_id: int,
) -> ClientDTO:
    return ClientDTO(
        actor_admin_id=actor_admin_id,
        **request.model_dump(),
    )


def client_update_contact_request_to_dto(
    *,
    request: ClientUpdateContactRequest,
    actor_admin_id: int,
    client_id: int,
) -> ClientDTO:
    return ClientDTO(
        actor_admin_id=actor_admin_id,
        client_id=client_id,
        **request.model_dump(),
    )


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
    description="Create a new client.",
)
def create_client(
    client_request: ClientCreateRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    try:
        dto = client_create_request_to_dto(
            request=client_request,
            actor_admin_id=actor_admin_id,
        )

        response_dto = asf.client_service().create_client(dto_client=dto)

        return ClientResponse.model_validate(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.get(
    "/",
    response_model=list[ClientResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all clients",
    description="Get all clients.",
)
def get_all_clients(
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    try:
        dto = ClientDTO(actor_admin_id=actor_admin_id)

        client_response_dtos = asf.client_service().get_all(dto)

        return [
            ClientResponse.model_validate(dto)
            for dto in client_response_dtos
        ]

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a client",
    description="Get a client by id.",
)
def get_client(
    client_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    try:
        dto = ClientDTO(
            actor_admin_id=actor_admin_id,
            client_id=client_id,
        )

        response_dto = asf.client_service().get_by_id(dto_client=dto)

        return ClientResponse.model_validate(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.put(
    "/{client_id}/contact",
    response_model=ClientResponse,
    status_code=status.HTTP_200_OK,
    summary="Update client contact",
    description="Update client contact data.",
)
def update_contact(
    client_id: int,
    request: ClientUpdateContactRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    try:
        dto = client_update_contact_request_to_dto(
            request=request,
            actor_admin_id=actor_admin_id,
            client_id=client_id,
        )

        response_dto = asf.client_service().update_contact(dto_client=dto)

        return ClientResponse.model_validate(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.patch(
    "/{client_id}/disable",
    response_model=ClientResponse,
    status_code=status.HTTP_200_OK,
    summary="Disable a client",
    description="Disable a client.",
)
def disable_client(
    client_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    try:
        dto = ClientDTO(
            actor_admin_id=actor_admin_id,
            client_id=client_id,
        )

        response_dto = asf.client_service().disable(dto_client=dto)

        return ClientResponse.model_validate(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.patch(
    "/{client_id}/enable",
    response_model=ClientResponse,
    status_code=status.HTTP_200_OK,
    summary="Enable a client",
    description="Enable a client.",
)
def enable_client(
    client_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    try:
        dto = ClientDTO(
            actor_admin_id=actor_admin_id,
            client_id=client_id,
        )

        response_dto = asf.client_service().enable(dto_client=dto)

        return ClientResponse.model_validate(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a client",
    description="Delete a client.",
)
def delete_client(
    client_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    try:
        dto = ClientDTO(
            actor_admin_id=actor_admin_id,
            client_id=client_id,
            name="",
        )

        asf.client_service().delete(dto_client=dto)

        return None

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc)





























