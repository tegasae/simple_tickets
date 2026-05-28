# src/web/routers/admin/tickets.py

from fastapi import APIRouter, Depends, status

from src.application.dto.ticket_dto import TicketDTO
from src.web.dependencies.auth import (
    get_current_admin,
    get_employee_id_from_request,
)
from src.web.dependencies.services import get_application_service_factory
from src.web.models.tickets import (
    TicketAssignExecutorRequest,
    TicketCancelRequest,
    TicketCommentRequest,
    TicketCreateRequest,
    TicketDeferRequest,
    TicketExecuteRequest,
    TicketResponse,
    TicketStartWorkRequest,
)


router = APIRouter(
    prefix="/admin/tickets",
    tags=["admin tickets"],

    # This dependency protects the whole router.
    # Every endpoint below requires current admin authentication.
    dependencies=[Depends(get_current_admin)],
)


# Exception mapping for ExceptionHandlerRegistry.
#
# Example in main.py:
#
#     registry.add_all_handlers_from_module(
#         module_name="src.domain.exceptions",
#         exceptions=admin.tickets.handlers,
#     )
#
handlers = {
    # common domain errors
    "DomainOperationError": 400,
    "DomainSecurityError": 403,
    "ItemValidationError": 400,
    "ItemNotFoundError": 404,

    # ticket-related errors if they exist in src.domain.exceptions
    "TicketError": 500,
    "TicketNotFoundError": 404,
    "TicketAlreadyExistsError": 409,
    "TicketValidationError": 400,
    "TicketOperationError": 400,
    "TicketSecurityError": 403,

    # admin/client/user errors that may happen during reference validation
    "AdminNotFoundError": 404,
    "ClientNotFoundError": 404,
    "UserNotFoundError": 404,
    "AdminValidationError": 400,
    "ClientValidationError": 400,
    "UserValidationError": 400,
}


# ---------------------------------------------------------------------
# Response mappers
# ---------------------------------------------------------------------

def to_ticket_response(response_dto) -> TicketResponse:
    """
    Convert application TicketResponseDTO to web TicketResponse.
    """
    return TicketResponse.model_validate(response_dto)


def to_ticket_responses(response_dtos) -> list[TicketResponse]:
    """
    Convert list[TicketResponseDTO] to list[TicketResponse].
    """
    return [
        to_ticket_response(response_dto)
        for response_dto in response_dtos
    ]


# ---------------------------------------------------------------------
# Request -> Application DTO mappers
# ---------------------------------------------------------------------

def ticket_create_request_to_dto(
    *,
    request: TicketCreateRequest,
    actor_admin_id: int,
) -> TicketDTO:
    """
    Convert create request to application TicketDTO.

    Important:
        admin_id is taken from authenticated admin.
        Do not accept admin_id from request body.
    """
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        client_id=request.client_id,
        text_of_ticket=request.text_of_ticket,
        user_id=request.user_id,
        contact_user_id=request.contact_user_id,
        user_ticket_id=request.user_ticket_id,
        executor_id=request.executor_id,
        is_remote=request.is_remote,
        urgency_level=request.urgency_level,
        comment=request.comment,
    )


def ticket_defer_request_to_dto(
    *,
    request: TicketDeferRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        ticket_id=ticket_id,
        client_id=request.client_id,
        comment=request.comment,
    )


def ticket_start_work_request_to_dto(
    *,
    request: TicketStartWorkRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        ticket_id=ticket_id,
        client_id=request.client_id,
        executor_id=request.executor_id,
    )


def ticket_execute_request_to_dto(
    *,
    request: TicketExecuteRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        ticket_id=ticket_id,
        client_id=request.client_id,
        comment=request.comment,
    )


def ticket_cancel_request_to_dto(
    *,
    request: TicketCancelRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        ticket_id=ticket_id,
        client_id=request.client_id,
        comment=request.comment,
    )


def ticket_comment_request_to_dto(
    *,
    request: TicketCommentRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        ticket_id=ticket_id,
        client_id=request.client_id,
        comment=request.comment,
    )


def ticket_assign_executor_request_to_dto(
    *,
    request: TicketAssignExecutorRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        ticket_id=ticket_id,
        client_id=request.client_id,
        executor_id=request.executor_id,
    )


def ticket_id_to_dto(
    *,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    """
    Build TicketDTO for operations that need only ticket id.

    Warning:
        Your current TicketApplicationService.delete() calls _validate_references(),
        and _validate_references() requires client_id/admin_id.

        If delete/get_by_id later require client_id, use a request body or
        load ticket before _validate_references() inside application service.
    """
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------

@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ticket",
    description="Create a new admin ticket.",
)
def create_ticket(
    ticket_request: TicketCreateRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_create_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
    )

    response_dto = asf.ticket_service().create_ticket(ticket_dto=dto)

    return to_ticket_response(response_dto)


@router.get(
    "/",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all tickets",
    description="Get all tickets.",
)
def get_all_tickets(
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
    )

    response_dtos = asf.ticket_service().get_all(ticket_dto=dto)

    return to_ticket_responses(response_dtos)


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ticket by id",
    description="Get ticket by id.",
)
def get_ticket(
    ticket_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_id_to_dto(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().get_by_id(ticket_dto=dto)

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/defer",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Defer ticket",
    description="Move ticket to deferred status.",
)
def defer_ticket(
    ticket_id: int,
    ticket_request: TicketDeferRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_defer_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().defer(ticket_dto=dto)

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/at-work",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Start ticket work",
    description="Move ticket to at-work status and assign executor.",
)
def start_work(
    ticket_id: int,
    ticket_request: TicketStartWorkRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_start_work_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().at_work(ticket_dto=dto)

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/execute",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute ticket",
    description="Execute ticket.",
)
def execute_ticket(
    ticket_id: int,
    ticket_request: TicketExecuteRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_execute_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().execute(ticket_dto=dto)

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/cancel",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel ticket",
    description="Cancel ticket.",
)
def cancel_ticket(
    ticket_id: int,
    ticket_request: TicketCancelRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_cancel_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().cancel(ticket_dto=dto)

    return to_ticket_response(response_dto)


@router.post(
    "/{ticket_id}/comments",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Add ticket comment",
    description="Add comment to ticket.",
)
def add_comment(
    ticket_id: int,
    ticket_request: TicketCommentRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_comment_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().add_comment(ticket_dto=dto)

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/executor",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign ticket executor",
    description="Assign executor to ticket.",
)
def assign_executor(
    ticket_id: int,
    ticket_request: TicketAssignExecutorRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_assign_executor_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().assign_executor(ticket_dto=dto)

    return to_ticket_response(response_dto)


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ticket",
    description="Delete ticket.",
)
def delete_ticket(
    ticket_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_id_to_dto(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    asf.ticket_service().delete(ticket_dto=dto)

    return None