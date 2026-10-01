# src/web/routers/admin/tickets.py

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, status

from src.application.dto.ticket_dto import TicketDTO
from src.web.dependencies.auth import (
    get_current_admin,
    get_employee_id_from_request,
)
from src.web.dependencies.services import (
    get_application_service_factory,
)
from src.web.models.tickets import (
    TicketAcceptRequest,
    TicketAssignRequest,
    TicketCancelRequest,
    TicketChangeDepartmentRequest,
    TicketCommentRequest,
    TicketCompleteWorkRetroactivelyRequest,
    TicketContactUserRequest,
    TicketCreateForUserRequest,
    TicketCreateRequest,
    TicketDeferRequest,
    TicketDescriptionRequest,
    TicketExecuteRequest,
    TicketFinishWorkRequest,
    TicketPauseWorkRequest,
    TicketRejectRequest,
    TicketRemoteWorkRecommendationRequest,
    TicketResponse,
    TicketResumeWorkRequest,
    TicketScheduleRequest,
    TicketStartRemoteWorkRequest,
    TicketStartWorkRequest,
    TicketUrgencyRequest, TicketCommentBaseRequest,
)


router = APIRouter(
    prefix="/admin/tickets",
    tags=["admin tickets"],
    dependencies=[
        Depends(get_current_admin),
    ],
)


# =====================================================================
# Response mapping
# =====================================================================


def to_ticket_response(
    response_dto,
) -> TicketResponse:
    return TicketResponse.model_validate(
        response_dto
    )


def to_ticket_responses(
    response_dtos,
) -> list[TicketResponse]:
    return [
        to_ticket_response(response_dto)
        for response_dto in response_dtos
    ]


# =====================================================================
# Request -> DTO
# =====================================================================


def ticket_id_to_dto(
    *,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )


def ticket_create_request_to_dto(
    *,
    request: TicketCreateRequest,
    actor_admin_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=0,

        client_id=request.client_id,

        user_id=request.user_id,
        contact_user_id=request.contact_user_id,
        user_ticket_id=0,

        department_id=request.department_id,

        text_of_ticket=request.text_of_ticket,
        description=request.description,

        remote_work_recommended=(
            request.remote_work_recommended
        ),

        urgency=request.urgency,
        planned_at=request.planned_at,

        comment=request.comment,
    )


def ticket_create_for_user_request_to_dto(
    *,
    request: TicketCreateForUserRequest,
    actor_admin_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=0,

        client_id=request.client_id,

        user_id=request.user_id,
        contact_user_id=request.contact_user_id,
        user_ticket_id=0,

        department_id=request.department_id,

        text_of_ticket=request.text_of_ticket,
        description=request.description,

        remote_work_recommended=(
            request.remote_work_recommended
        ),

        urgency=request.urgency,
        planned_at=request.planned_at,

        comment=request.comment,
    )


def ticket_comment_request_to_dto(
    *,
    request: TicketCommentBaseRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        ticket_id=ticket_id,
        actor_admin_id=actor_admin_id,
        comment=request.comment,
    )

def ticket_description_request_to_dto(
    *,
    request: TicketDescriptionRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
        description=request.description,
    )


def ticket_contact_user_request_to_dto(
    *,
    request: TicketContactUserRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
        contact_user_id=request.contact_user_id,
    )


def ticket_department_request_to_dto(
    *,
    request: TicketChangeDepartmentRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
        department_id=request.department_id,
    )


def ticket_remote_recommendation_request_to_dto(
    *,
    request: TicketRemoteWorkRecommendationRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
        remote_work_recommended=(
            request.remote_work_recommended
        ),
    )


def ticket_urgency_request_to_dto(
    *,
    request: TicketUrgencyRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
        urgency=request.urgency,
    )


def ticket_schedule_request_to_dto(
    *,
    request: TicketScheduleRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
        planned_at=request.planned_at,
    )


def ticket_assign_request_to_dto(
    *,
    request: TicketAssignRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
        executor_id=request.executor_id,
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
        ticket_id=ticket_id,
        work_is_remote=request.work_is_remote,
        comment=request.comment,
    )


def ticket_start_remote_work_request_to_dto(
    *,
    request: TicketStartRemoteWorkRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
        comment=request.comment,
    )


def ticket_resume_work_request_to_dto(
    *,
    request: TicketResumeWorkRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
        work_is_remote=request.work_is_remote,
        comment=request.comment,
    )


def ticket_complete_work_retroactively_request_to_dto(
    *,
    request: TicketCompleteWorkRetroactivelyRequest,
    actor_admin_id: int,
    ticket_id: int,
) -> TicketDTO:
    return TicketDTO(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,

        work_is_remote=request.work_is_remote,

        actual_started_at=request.actual_started_at,
        actual_finished_at=request.actual_finished_at,
        duration=timedelta(seconds=request.duration),
        comment=request.comment,
    )


# =====================================================================
# Creation
# =====================================================================


@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create internal ticket",
)
def create_ticket(
    ticket_request: TicketCreateRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_create_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
    )

    response_dto = (
        asf.ticket_service()
        .create_ticket(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )




# =====================================================================
# Queries
#
# Static paths intentionally come before /{ticket_id}.
# =====================================================================


@router.get(
    "/",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all tickets",
)
def get_all_tickets(
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = TicketDTO(
        actor_admin_id=actor_admin_id,
    )

    response_dtos = (
        asf.ticket_service()
        .get_all(
            ticket_dto=dto,
        )
    )

    return to_ticket_responses(
        response_dtos
    )


@router.get(
    "/open",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get open tickets",
)
def get_open_tickets(
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = TicketDTO(
        actor_admin_id=actor_admin_id,
    )

    response_dtos = (
        asf.ticket_service()
        .get_open(
            ticket_dto=dto,
        )
    )

    return to_ticket_responses(
        response_dtos
    )


@router.get(
    "/closed",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get closed tickets",
)
def get_closed_tickets(
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = TicketDTO(
        actor_admin_id=actor_admin_id,
    )

    response_dtos = (
        asf.ticket_service()
        .get_closed(
            ticket_dto=dto,
        )
    )

    return to_ticket_responses(
        response_dtos
    )


@router.get(
    "/by-client/{client_id}",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get tickets by client",
)
def get_tickets_by_client(
    client_id: int,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = TicketDTO(
        actor_admin_id=actor_admin_id,
        client_id=client_id,
    )

    response_dtos = (
        asf.ticket_service()
        .get_by_client_id(
            ticket_dto=dto,
        )
    )

    return to_ticket_responses(
        response_dtos
    )


@router.get(
    "/by-user/{user_id}",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get tickets by user",
)
def get_tickets_by_user(
    user_id: int,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = TicketDTO(
        actor_admin_id=actor_admin_id,
        user_id=user_id,
    )

    response_dtos = (
        asf.ticket_service()
        .get_by_user_id(
            ticket_dto=dto,
        )
    )

    return to_ticket_responses(
        response_dtos
    )


@router.get(
    "/by-contact-user/{contact_user_id}",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get tickets by contact user",
)
def get_tickets_by_contact_user(
    contact_user_id: int,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = TicketDTO(
        actor_admin_id=actor_admin_id,
        contact_user_id=contact_user_id,
    )

    response_dtos = (
        asf.ticket_service()
        .get_by_contact_user_id(
            ticket_dto=dto,
        )
    )

    return to_ticket_responses(
        response_dtos
    )


@router.get(
    "/by-department/{department_id}",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get tickets by department",
)
def get_tickets_by_department(
    department_id: int,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = TicketDTO(
        actor_admin_id=actor_admin_id,
        department_id=department_id,
    )

    response_dtos = (
        asf.ticket_service()
        .get_by_department_id(
            ticket_dto=dto,
        )
    )

    return to_ticket_responses(
        response_dtos
    )


@router.get(
    "/by-executor/{executor_id}",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Get tickets by current executor",
)
def get_tickets_by_current_executor(
    executor_id: int,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = TicketDTO(
        actor_admin_id=actor_admin_id,
        executor_id=executor_id,
    )

    response_dtos = (
        asf.ticket_service()
        .get_by_current_executor(
            ticket_dto=dto,
        )
    )

    return to_ticket_responses(
        response_dtos
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ticket by id",
)
def get_ticket(
    ticket_id: int,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_id_to_dto(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .get_by_id(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


# =====================================================================
# Ticket data
# =====================================================================


@router.post(
    "/{ticket_id}/comments",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Add ticket comment",
)
def add_comment(
    ticket_id: int,
    ticket_request: TicketCommentRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_comment_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .add_comment(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/description",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Update ticket description",
)
def update_description(
    ticket_id: int,
    ticket_request: TicketDescriptionRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_description_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .update_description(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/contact-user",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Change ticket contact user",
)
def change_contact_user(
    ticket_id: int,
    ticket_request: TicketContactUserRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_contact_user_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .change_contact_user(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/department",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Change ticket department",
)
def change_department(
    ticket_id: int,
    ticket_request: TicketChangeDepartmentRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_department_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .change_department(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/remote-work-recommended",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Change remote work recommendation",
)
def set_remote_work_recommended(
    ticket_id: int,
    ticket_request: TicketRemoteWorkRecommendationRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_remote_recommendation_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .set_remote_work_recommended(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/urgency",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Change ticket urgency",
)
def change_urgency(
    ticket_id: int,
    ticket_request: TicketUrgencyRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_urgency_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .change_urgency(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


# =====================================================================
# Planning
# =====================================================================


@router.patch(
    "/{ticket_id}/schedule",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Set ticket schedule",
)
def schedule_ticket(
    ticket_id: int,
    ticket_request: TicketScheduleRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_schedule_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .schedule(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.delete(
    "/{ticket_id}/schedule",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear ticket schedule",
)
def clear_ticket_schedule(
    ticket_id: int,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_id_to_dto(
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .clear_schedule(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


# =====================================================================
# Management workflow
# =====================================================================


@router.patch(
    "/{ticket_id}/accept",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept ticket",
)
def accept_ticket(
    ticket_id: int,
    ticket_request: TicketAcceptRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_comment_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .accept(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/reject",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject ticket",
)
def reject_ticket(
    ticket_id: int,
    ticket_request: TicketRejectRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_comment_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .reject(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/defer",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Defer ticket",
)
def defer_ticket(
    ticket_id: int,
    ticket_request: TicketDeferRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_comment_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .defer(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/executor",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign ticket executor",
)
def assign_ticket(
    ticket_id: int,
    ticket_request: TicketAssignRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_assign_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .assign(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


# =====================================================================
# Work
# =====================================================================


@router.patch(
    "/{ticket_id}/start-work",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Start ticket work",
)
def start_work(
    ticket_id: int,
    ticket_request: TicketStartWorkRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_start_work_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .start_work(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/start-remote-work",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Start recommended remote work",
)
def start_remote_work(
    ticket_id: int,
    ticket_request: TicketStartRemoteWorkRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_start_remote_work_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .start_remote_work(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/pause-work",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Pause ticket work",
)
def pause_work(
    ticket_id: int,
    ticket_request: TicketPauseWorkRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_comment_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .pause_work(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/resume-work",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Resume ticket work",
)
def resume_work(
    ticket_id: int,
    ticket_request: TicketResumeWorkRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_resume_work_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .resume_work(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/finish-work",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Finish ticket work",
)
def finish_work(
    ticket_id: int,
    ticket_request: TicketFinishWorkRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_comment_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .finish_work(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/complete-work-retroactively",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Register completed work retrospectively",
)
def complete_work_retroactively(
    ticket_id: int,
    ticket_request: TicketCompleteWorkRetroactivelyRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = (
        ticket_complete_work_retroactively_request_to_dto(
            request=ticket_request,
            actor_admin_id=actor_admin_id,
            ticket_id=ticket_id,
        )
    )

    response_dto = (
        asf.ticket_service()
        .complete_work_retroactively(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


# =====================================================================
# Finalization
# =====================================================================


@router.patch(
    "/{ticket_id}/execute",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute ticket",
)
def execute_ticket(
    ticket_id: int,
    ticket_request: TicketExecuteRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_comment_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .execute(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )


@router.patch(
    "/{ticket_id}/cancel",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel ticket",
)
def cancel_ticket(
    ticket_id: int,
    ticket_request: TicketCancelRequest,
    asf=Depends(
        get_application_service_factory
    ),
    actor_admin_id: int = Depends(
        get_employee_id_from_request
    ),
):
    dto = ticket_comment_request_to_dto(
        request=ticket_request,
        actor_admin_id=actor_admin_id,
        ticket_id=ticket_id,
    )

    response_dto = (
        asf.ticket_service()
        .cancel(
            ticket_dto=dto,
        )
    )

    return to_ticket_response(
        response_dto
    )