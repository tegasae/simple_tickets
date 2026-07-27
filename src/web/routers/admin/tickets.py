# src/web/routers/admin/tickets.py

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from src.application.dto.ticket_dto import TicketDTO
from src.application.dto.ticket_search_dto import TicketSearchDTO
from src.web.dependencies.auth import (
    get_current_admin,
    get_employee_id_from_request,
)
from src.web.dependencies.services import get_application_service_factory
from src.web.models.tickets import (
    TicketAcceptRequest,
    TicketAssignExecutorRequest,
    TicketCancelRequest,
    TicketChangeDepartmentRequest,
    TicketCommentRequest,
    TicketConfirmExecutionRequest,
    TicketCreateRequest,
    TicketDeferRequest,
    TicketExecuteRequest,
    TicketPauseWorkRequest,
    TicketReadyToWorkRequest,
    TicketRecordCompletedWorkForReviewRequest,
    TicketRejectRequest,
    TicketResumeWorkRequest,
    TicketReturnToAssignedRequest,
    TicketReturnToDeferredRequest,
    TicketReturnToReadyToWorkRequest,
    TicketReturnToScheduledRequest,
    TicketReturnToWorkRequest,
    TicketScheduleRequest,
    TicketStartWorkRequest,
    TicketSubmitForReviewRequest,
    TicketUpdateDetailsRequest,
    TicketResponse,
)


router = APIRouter(
    prefix="/admin/tickets",
    tags=["admin tickets"],
    dependencies=[Depends(get_current_admin)],
)


handlers = {
    "DomainOperationError": 400,
    "DomainSecurityError": 403,
    "ItemValidationError": 400,
    "ItemNotFoundError": 404,

    "TicketError": 500,
    "TicketNotFoundError": 404,
    "TicketAlreadyExistsError": 409,
    "TicketValidationError": 400,
    "TicketOperationError": 400,
    "TicketSecurityError": 403,

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
    return TicketResponse.model_validate(response_dto)


def to_ticket_responses(response_dtos) -> list[TicketResponse]:
    return [
        to_ticket_response(response_dto)
        for response_dto in response_dtos
    ]


# ---------------------------------------------------------------------
# Request -> Application DTO mappers
# ---------------------------------------------------------------------

def ticket_search_query_to_dto(
    *,
    actor_admin_id: int,
    client_id: int,
    user_id: int,
    admin_id: int,
    executor_id: int,
    department_id: int,
    ticket_status: str,
    is_closed: bool | None,
    date_from: datetime | None,
    date_to: datetime | None,
    text: str,
    limit: int,
    offset: int,
) -> TicketSearchDTO:
    return TicketSearchDTO(
        actor_admin_id=actor_admin_id,
        client_id=client_id,
        user_id=user_id,
        admin_id=admin_id,
        executor_id=executor_id,
        department_id=department_id,
        status=ticket_status,
        is_closed=is_closed,
        date_from=date_from,
        date_to=date_to,
        text=text,
        limit=limit,
        offset=offset,
    )


def ticket_create_request_to_dto(
    *,
    request: TicketCreateRequest,
    actor_admin_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=0,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        client_id=request.client_id,
        user_id=request.user_id,
        contact_user_id=request.contact_user_id,
        user_ticket_id=0,
        department_id=request.department_id,
        text_of_ticket=request.text_of_ticket,
        description=request.description,
        is_remote=request.is_remote,
        urgency_level=request.urgency_level,
        comment=request.comment,
    )


def ticket_id_to_dto(
    *,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )


def ticket_update_details_request_to_dto(
    *,
    request: TicketUpdateDetailsRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        description=request.description,
        contact_user_id=request.contact_user_id,
        is_remote=request.is_remote,
    )


def ticket_change_department_request_to_dto(
    *,
    request: TicketChangeDepartmentRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        department_id=request.department_id,
    )


def ticket_comment_request_to_dto(
    *,
    request: TicketCommentRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_accept_request_to_dto(
    *,
    request: TicketAcceptRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_reject_request_to_dto(
    *,
    request: TicketRejectRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_defer_request_to_dto(
    *,
    request: TicketDeferRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_schedule_request_to_dto(
    *,
    request: TicketScheduleRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        planned_start_at=request.planned_start_at,
        planned_finish_at=request.planned_finish_at,
        comment=request.comment,
    )


def ticket_assign_executor_request_to_dto(
    *,
    request: TicketAssignExecutorRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        executor_id=request.executor_id,
        comment=request.comment,
    )


def ticket_ready_to_work_request_to_dto(
    *,
    request: TicketReadyToWorkRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        executor_id=request.executor_id,
        planned_start_at=request.planned_start_at,
        planned_finish_at=request.planned_finish_at,
        comment=request.comment,
    )


def ticket_start_work_request_to_dto(
    *,
    request: TicketStartWorkRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_pause_work_request_to_dto(
    *,
    request: TicketPauseWorkRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_resume_work_request_to_dto(
    *,
    request: TicketResumeWorkRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_submit_for_review_request_to_dto(
    *,
    request: TicketSubmitForReviewRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_record_completed_work_for_review_request_to_dto(
    *,
    request: TicketRecordCompletedWorkForReviewRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        executor_id=request.executor_id,
        actual_started_at=request.actual_started_at,
        actual_finished_at=request.actual_finished_at,
        comment=request.comment,
    )


def ticket_confirm_execution_request_to_dto(
    *,
    request: TicketConfirmExecutionRequest | TicketExecuteRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_return_to_work_request_to_dto(
    *,
    request: TicketReturnToWorkRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_return_to_assigned_request_to_dto(
    *,
    request: TicketReturnToAssignedRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        executor_id=request.executor_id,
        comment=request.comment,
    )


def ticket_return_to_scheduled_request_to_dto(
    *,
    request: TicketReturnToScheduledRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        planned_start_at=request.planned_start_at,
        planned_finish_at=request.planned_finish_at,
        comment=request.comment,
    )


def ticket_return_to_ready_to_work_request_to_dto(
    *,
    request: TicketReturnToReadyToWorkRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        executor_id=request.executor_id,
        planned_start_at=request.planned_start_at,
        planned_finish_at=request.planned_finish_at,
        comment=request.comment,
    )


def ticket_return_to_deferred_request_to_dto(
    *,
    request: TicketReturnToDeferredRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


def ticket_cancel_request_to_dto(
    *,
    request: TicketCancelRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
        comment=request.comment,
    )


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------

@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ticket",
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

    response_dto = asf.ticket_service().create_ticket(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.get(
    "/",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Search tickets",
)
def search_tickets(
    client_id: int = 0,
    user_id: int = 0,
    admin_id: int = 0,
    executor_id: int = 0,
    department_id: int = 0,
    ticket_status: str = Query("", alias="status"),
    is_closed: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    text: str = "",
    limit: int = 100,
    offset: int = 0,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_search_query_to_dto(
        actor_admin_id=actor_admin_id,
        client_id=client_id,
        user_id=user_id,
        admin_id=admin_id,
        executor_id=executor_id,
        department_id=department_id,
        ticket_status=ticket_status,
        is_closed=is_closed,
        date_from=date_from,
        date_to=date_to,
        text=text,
        limit=limit,
        offset=offset,
    )

    response_dtos = asf.ticket_search_service().search(
        search_dto=dto,
    )

    return to_ticket_responses(response_dtos)


@router.get(
    "/all",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all tickets",
    description="Legacy endpoint. Prefer GET /admin/tickets with filters.",
)
def get_all_tickets(
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = TicketDTO(
        actor_admin_id=actor_admin_id,
        admin_id=actor_admin_id,
    )

    response_dtos = asf.ticket_service().get_all(
        ticket_dto=dto,
    )

    return to_ticket_responses(response_dtos)


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ticket by id",
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

    response_dto = asf.ticket_service().get_by_id(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/details",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Update ticket details",
)
def update_ticket_details(
    ticket_id: int,
    ticket_request: TicketUpdateDetailsRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_update_details_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().update_details(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/department",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Change ticket department",
)
def change_ticket_department(
    ticket_id: int,
    ticket_request: TicketChangeDepartmentRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_change_department_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().change_department(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/accept",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept ticket",
)
def accept_ticket(
    ticket_id: int,
    ticket_request: TicketAcceptRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_accept_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().accept(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/reject",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject ticket",
)
def reject_ticket(
    ticket_id: int,
    ticket_request: TicketRejectRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_reject_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().reject(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/defer",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Defer ticket",
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

    response_dto = asf.ticket_service().defer(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/schedule",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Schedule ticket",
)
def schedule_ticket(
    ticket_id: int,
    ticket_request: TicketScheduleRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_schedule_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().schedule(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/executor",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign ticket executor",
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

    response_dto = asf.ticket_service().assign_executor(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/ready-to-work",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark ticket ready to work",
)
def ready_to_work(
    ticket_id: int,
    ticket_request: TicketReadyToWorkRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_ready_to_work_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().ready_to_work(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/at-work",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Start ticket work",
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

    response_dto = asf.ticket_service().at_work(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/pause",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Pause ticket work",
)
def pause_work(
    ticket_id: int,
    ticket_request: TicketPauseWorkRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_pause_work_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().pause_work(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/resume",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Resume ticket work",
)
def resume_work(
    ticket_id: int,
    ticket_request: TicketResumeWorkRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_resume_work_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().resume_work(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/submit-for-review",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit ticket for review",
)
def submit_for_review(
    ticket_id: int,
    ticket_request: TicketSubmitForReviewRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_submit_for_review_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().submit_for_review(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/record-completed-work-for-review",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Record completed work and submit ticket for review",
)
def record_completed_work_for_review(
    ticket_id: int,
    ticket_request: TicketRecordCompletedWorkForReviewRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_record_completed_work_for_review_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().record_completed_work_for_review(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/confirm-execution",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm ticket execution",
)
def confirm_execution(
    ticket_id: int,
    ticket_request: TicketConfirmExecutionRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_confirm_execution_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().confirm_execution(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/execute",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute ticket",
    description="Legacy alias for confirm-execution.",
)
def execute_ticket(
    ticket_id: int,
    ticket_request: TicketExecuteRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_confirm_execution_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().execute(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/return-to-work",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Return ticket to work",
)
def return_to_work(
    ticket_id: int,
    ticket_request: TicketReturnToWorkRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_return_to_work_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().return_to_work(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/return-to-assigned",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Return ticket to assigned",
)
def return_to_assigned(
    ticket_id: int,
    ticket_request: TicketReturnToAssignedRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_return_to_assigned_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().return_to_assigned(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/return-to-scheduled",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Return ticket to scheduled",
)
def return_to_scheduled(
    ticket_id: int,
    ticket_request: TicketReturnToScheduledRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_return_to_scheduled_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().return_to_scheduled(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/return-to-ready-to-work",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Return ticket to ready-to-work",
)
def return_to_ready_to_work(
    ticket_id: int,
    ticket_request: TicketReturnToReadyToWorkRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_return_to_ready_to_work_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().return_to_ready_to_work(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/return-to-deferred",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Return ticket to deferred",
)
def return_to_deferred(
    ticket_id: int,
    ticket_request: TicketReturnToDeferredRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = ticket_return_to_deferred_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = asf.ticket_service().return_to_deferred(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.patch(
    "/{ticket_id}/cancel",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel ticket",
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

    response_dto = asf.ticket_service().cancel(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.post(
    "/{ticket_id}/comments",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Add ticket comment",
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

    response_dto = asf.ticket_service().add_comment(
        ticket_dto=dto,
    )

    return to_ticket_response(response_dto)


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ticket",
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

    asf.ticket_service().delete(
        ticket_dto=dto,
    )

    return None