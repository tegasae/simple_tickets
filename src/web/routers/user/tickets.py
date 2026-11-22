# src/web/routers/user/tickets.py

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.dto.ticket_dto import (
    TicketUserDTO,
    TicketUserResponseDTO,
)
from src.application.services.ticket_user_service import TicketUserApplicationService

from src.domain.exceptions import DomainError
from src.web.dependencies.auth import (
    get_current_user,
    get_employee_id_from_request,
)
from src.web.dependencies.services import (
    get_application_ticket_user_service,
)
from src.web.models.tikcets_user import UserTicketCreateRequest, UserTicketActionRequest, UserTicketCommentRequest, \
    UserTicketDescriptionRequest, UserTicketContactUserRequest, TicketUserResponse

router = APIRouter(
    prefix="/user/tickets",
    tags=["user tickets"],
    dependencies=[
        Depends(get_current_user),
    ],
)


# =====================================================================
# Response model
# =====================================================================


# =====================================================================
# Error mapping
# =====================================================================
ERROR_STATUS_CODES = {}
"""
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
"""

def _domain_error(
    exc: Exception,
) -> HTTPException:
    raise exc
    #if isinstance(exc, PermissionError):
    #    return HTTPException(
    #        status_code=status.HTTP_403_FORBIDDEN,
    #        detail=str(exc),
    #    )

    #status_code = ERROR_STATUS_CODES.get(
    #    type(exc).__name__,
    #    status.HTTP_400_BAD_REQUEST,
    #)


    #return HTTPException(
    #    status_code=status_code,
    #    detail=str(exc),
    #)


# =====================================================================
# Response mappers
# =====================================================================


def to_user_ticket_response(
    response_dto: TicketUserResponseDTO,
) -> TicketUserResponse:
    return TicketUserResponse.model_validate(
        response_dto
    )


def to_user_ticket_responses(
    response_dtos: list[TicketUserResponseDTO],
) -> list[TicketUserResponse]:
    return [
        to_user_ticket_response(response_dto)
        for response_dto in response_dtos
    ]




# =====================================================================
# Creation
# =====================================================================


@router.post(
    "/",
    response_model=TicketUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user ticket",
)
def create_ticket(
    request: UserTicketCreateRequest,
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_application_ticket_user_service
    ),
)->TicketUserResponse:
    try:
        dto = TicketUserDTO(
            actor_user_id=user_id,
            **request.model_dump(),
        )

        response_dto = service.create_from_user(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dto(
            response_dto
        )

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


# =====================================================================
# Queries
# =====================================================================


@router.get(
    "/",
    response_model=list[TicketUserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user tickets",
)
def get_my_tickets(
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_application_ticket_user_service
    ),
)->list[TicketUserResponse]:
    try:


        dto=TicketUserDTO(actor_user_id=user_id,user_id=user_id)

        response_dtos = service.get_by_user_id(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dtos(response_dtos)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/all",
    response_model=list[TicketUserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all client user tickets",
)
def get_all_tickets(
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_application_ticket_user_service
    ),
)->list[TicketUserResponse]:
    try:


        dto = TicketUserDTO(
            actor_user_id=user_id,
        )
        response_dtos = service.get_all(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dtos(response_dtos)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/open",
    response_model=list[TicketUserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get open user tickets",
)
def get_open_tickets(
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_application_ticket_user_service
    ),
)->list[TicketUserResponse]:
    try:
        dto = TicketUserDTO(
            actor_user_id=user_id,

        )
        response_dtos = service.get_open(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dtos(response_dtos)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/closed",
    response_model=list[TicketUserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get closed user tickets",
)
def get_closed_tickets(
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_application_ticket_user_service
    ),
)->list[TicketUserResponse]:
    try:

        dto = TicketUserDTO(
            actor_user_id=user_id,
        )
        response_dtos = service.get_closed(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dtos(response_dtos)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.get(
    "/{ticket_user_id}",
    response_model=TicketUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user ticket by id",
)
def get_ticket(
    ticket_user_id: int,
    user_id: int = Depends(
        get_employee_id_from_request
    ),
    service: TicketUserApplicationService = Depends(
        get_application_ticket_user_service
    ),
)->TicketUserResponse:
    try:
        dto = TicketUserDTO(
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
        )
        response_dto = service.get_by_id(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dto(response_dto)
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


# =====================================================================
# TicketUser data
# =====================================================================


@router.post(
    "/{ticket_user_id}/comments",
    response_model=TicketUserResponse,
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
        get_application_ticket_user_service
    ),
)->TicketUserResponse:
    try:

        dto = TicketUserDTO(
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
            **request.model_dump()
        )

        response_dto = service.add_comment(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dto(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.patch(
    "/{ticket_user_id}/description",
    response_model=TicketUserResponse,
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
        get_application_ticket_user_service
    ),
)->TicketUserResponse:
    try:


        dto = TicketUserDTO(
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
            **request.model_dump()
        )

        response_dto = service.update_description(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dto(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.patch(
    "/{ticket_user_id}/contact-user",
    response_model=TicketUserResponse,
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
        get_application_ticket_user_service
    ),
)->TicketUserResponse:
    try:


        dto = TicketUserDTO(
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
            **request.model_dump()
        )

        response_dto = service.change_contact_user(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dto(response_dto)
    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


# =====================================================================
# User workflow
# =====================================================================


@router.patch(
    "/{ticket_user_id}/cancel",
    response_model=TicketUserResponse,
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
        get_application_ticket_user_service
    ),
)->TicketUserResponse:
    try:

        dto = TicketUserDTO(
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
            **request.model_dump()
        )

        response_dto = service.cancel_by_user(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dto(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc


@router.patch(
    "/{ticket_user_id}/confirm",
    response_model=TicketUserResponse,
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
        get_application_ticket_user_service
    ),
)->TicketUserResponse:
    try:
        dto = TicketUserDTO(
            actor_user_id=user_id,
            ticket_user_id=ticket_user_id,
            **request.model_dump()
        )

        response_dto = service.confirm_by_user(
            ticket_user_dto=dto,
        )

        return TicketUserResponse.from_dto(response_dto)

    except (DomainError, PermissionError) as exc:
        raise _domain_error(exc) from exc