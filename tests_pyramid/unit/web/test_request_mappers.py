from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.web.models.admins import (
    AdminAttachAccountRequest, AdminChangePasswordRequest, AdminCreateRequest, AdminRolesRequest, AdminUpdateRequest,
)
from src.web.models.clients import ClientCreateRequest, ClientUpdateContactRequest
from src.web.models.department import DepartmentCreateRequest, DepartmentUpdateRequest
from src.web.models.roles import AdminRoleCreateRequest, UserRoleCreateRequest
from src.web.models.tickets import (
    TicketAcceptRequest, TicketAssignExecutorRequest, TicketCancelRequest, TicketChangeDepartmentRequest,
    TicketConfirmExecutionRequest, TicketCreateRequest, TicketDeferRequest, TicketPauseWorkRequest,
    TicketReadyToWorkRequest, TicketRecordCompletedWorkForReviewRequest, TicketRejectRequest,
    TicketResumeWorkRequest, TicketReturnToAssignedRequest, TicketReturnToDeferredRequest,
    TicketReturnToReadyToWorkRequest, TicketReturnToScheduledRequest, TicketReturnToWorkRequest,
    TicketScheduleRequest, TicketStartWorkRequest, TicketSubmitForReviewRequest, TicketUpdateDetailsRequest,
)
from src.web.models.users import (
    UserAttachAccountRequest, UserChangePasswordRequest, UserCreateRequest, UserRolesRequest, UserUpdateRequest,
)
from src.web.routers.admin import admins as ar
from src.web.routers.admin import clients as cr
from src.web.routers.admin import departments as dr
from src.web.routers.admin import roles as rr
from src.web.routers.admin import tickets as tr
from src.web.routers.admin import users as ur
from src.web.routers.user import tickets as utr

pytestmark = pytest.mark.unit
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def test_admin_request_mappers_take_actor_from_context() -> None:
    dto = ar.admin_create_request_to_dto(
        request=AdminCreateRequest(first_name="New Admin", login="admin", password="Strong1!", department_id=5, roles={1, 2}),
        actor_admin_id=99,
    )
    assert dto.actor_admin_id == 99 and dto.employee_id == 0 and dto.department_id == 5 and dto.roles == {1, 2}
    update = ar.admin_update_request_to_dto(request=AdminUpdateRequest(first_name="Changed", job_title="Dev"), actor_admin_id=99, employee_id=10)
    assert update.employee_id == 10 and update.first_name == "Changed" and update.job_title == "Dev"
    account = ar.admin_attach_account_request_to_dto(request=AdminAttachAccountRequest(login="x", password="Strong1!"), actor_admin_id=99, employee_id=10)
    assert account.login == "x" and account.actor_admin_id == 99
    password = ar.admin_change_password_request_to_dto(request=AdminChangePasswordRequest(password="New2!"), actor_admin_id=99, employee_id=10)
    assert password.password == "New2!"
    roles = ar.admin_roles_request_to_dto(request=AdminRolesRequest(roles={4}), actor_admin_id=99, employee_id=10)
    assert roles.roles == {4}
    assert ar.admin_id_to_dto(actor_admin_id=99, employee_id=10).employee_id == 10


def test_user_request_mappers() -> None:
    dto = ur.user_create_request_to_dto(
        request=UserCreateRequest(client_id=5, first_name="New User", login="u", password="Strong1!", roles={1}), actor_admin_id=99
    )
    assert dto.actor_admin_id == 99 and dto.client_id == 5 and dto.employee_id == 0
    update = ur.user_update_request_to_dto(request=UserUpdateRequest(first_name="Changed"), actor_admin_id=99, employee_id=20)
    assert update.employee_id == 20 and update.first_name == "Changed"
    account = ur.user_attach_account_request_to_dto(request=UserAttachAccountRequest(login="u2", password="Strong1!"), actor_admin_id=99, employee_id=20)
    assert account.login == "u2"
    pw = ur.user_change_password_request_to_dto(request=UserChangePasswordRequest(password="New2!"), actor_admin_id=99, employee_id=20)
    assert pw.password == "New2!"
    roles = ur.user_roles_request_to_dto(request=UserRolesRequest(roles={2}), actor_admin_id=99, employee_id=20)
    assert roles.roles == {2}
    assert ur.user_id_to_dto(actor_admin_id=99, employee_id=20).employee_id == 20


def test_client_department_role_mappers() -> None:
    client = cr.client_create_request_to_dto(request=ClientCreateRequest(name="Acme", email="a@b.com"), actor_admin_id=99)
    assert client.actor_admin_id == 99 and client.name == "Acme"
    updated = cr.client_update_contact_request_to_dto(request=ClientUpdateContactRequest(name="New"), actor_admin_id=99, client_id=5)
    assert updated.client_id == 5 and updated.name == "New"

    dep = dr.create_request_to_dto(request=DepartmentCreateRequest(name="Support"), actor_admin_id=99)
    assert dep.actor_admin_id == 99 and dep.department_id == 0
    dep_up = dr.update_request_to_dto(department_id=5, request=DepartmentUpdateRequest(name="Infra"), actor_admin_id=99)
    assert dep_up.department_id == 5 and dep_up.name == "Infra"
    assert dr.id_to_dto(department_id=5, actor_admin_id=99).department_id == 5

    ar_dto = rr.admin_role_create_request_to_dto(
        request=AdminRoleCreateRequest(name="ticket", permissions=[AdminPermission.TICKET_VIEW]), actor_admin_id=99
    )
    assert ar_dto.permissions == frozenset({AdminPermission.TICKET_VIEW})
    ur_dto = rr.user_role_create_request_to_dto(
        request=UserRoleCreateRequest(name="ticket", permissions=[UserPermission.TICKET_VIEW]), actor_admin_id=99
    )
    assert ur_dto.permissions == frozenset({UserPermission.TICKET_VIEW})
    assert rr.admin_role_id_to_dto(role_id=3, actor_admin_id=99).role_id == 3
    assert rr.user_role_id_to_dto(role_id=4, actor_admin_id=99).role_id == 4


def test_ticket_create_mapper_has_no_command_admin_id() -> None:
    dto = tr.ticket_create_request_to_dto(
        request=TicketCreateRequest(client_id=1, text_of_ticket="Need help", user_id=2, contact_user_id=3, department_id=4, is_remote=True, urgency_level=2),
        actor_admin_id=99,
    )
    assert dto.actor_admin_id == 99 and dto.ticket_id == 0 and dto.user_ticket_id == 0
    assert not hasattr(dto, "admin_id")
    assert dto.client_id == 1 and dto.user_id == 2 and dto.contact_user_id == 3 and dto.department_id == 4


def test_ticket_id_details_department_comment_mappers() -> None:
    assert tr.ticket_id_to_dto(actor_admin_id=99, ticket_id=10).ticket_id == 10
    details = tr.ticket_update_details_request_to_dto(
        request=TicketUpdateDetailsRequest(description="d", contact_user_id=3, is_remote=True), actor_admin_id=99, ticket_id=10
    )
    assert details.description == "d" and details.contact_user_id == 3 and details.is_remote
    dep = tr.ticket_change_department_request_to_dto(request=TicketChangeDepartmentRequest(department_id=5), actor_admin_id=99, ticket_id=10)
    assert dep.department_id == 5
    assert tr.ticket_comment_request_to_dto(request=tr.TicketCommentRequest(comment="x"), actor_admin_id=99, ticket_id=10).comment == "x"


@pytest.mark.parametrize(
    "factory,mapper,fields",
    [
        (lambda: TicketAcceptRequest(comment="a"), tr.ticket_accept_request_to_dto, {"comment": "a"}),
        (lambda: TicketRejectRequest(comment="r"), tr.ticket_reject_request_to_dto, {"comment": "r"}),
        (lambda: TicketDeferRequest(comment="d"), tr.ticket_defer_request_to_dto, {"comment": "d"}),
        (lambda: TicketAssignExecutorRequest(executor_id=7, comment="x"), tr.ticket_assign_executor_request_to_dto, {"executor_id": 7}),
        (lambda: TicketStartWorkRequest(comment="x"), tr.ticket_start_work_request_to_dto, {"comment": "x"}),
        (lambda: TicketPauseWorkRequest(comment="x"), tr.ticket_pause_work_request_to_dto, {"comment": "x"}),
        (lambda: TicketResumeWorkRequest(comment="x"), tr.ticket_resume_work_request_to_dto, {"comment": "x"}),
        (lambda: TicketSubmitForReviewRequest(comment="x"), tr.ticket_submit_for_review_request_to_dto, {"comment": "x"}),
        (lambda: TicketConfirmExecutionRequest(comment="x"), tr.ticket_confirm_execution_request_to_dto, {"comment": "x"}),
        (lambda: TicketReturnToWorkRequest(comment="x"), tr.ticket_return_to_work_request_to_dto, {"comment": "x"}),
        (lambda: TicketReturnToAssignedRequest(executor_id=8), tr.ticket_return_to_assigned_request_to_dto, {"executor_id": 8}),
        (lambda: TicketReturnToDeferredRequest(comment="x"), tr.ticket_return_to_deferred_request_to_dto, {"comment": "x"}),
        (lambda: TicketCancelRequest(comment="x"), tr.ticket_cancel_request_to_dto, {"comment": "x"}),
    ],
)
def test_ticket_simple_workflow_mappers(factory, mapper, fields) -> None:
    dto = mapper(request=factory(), actor_admin_id=99, ticket_id=10)
    assert dto.actor_admin_id == 99 and dto.ticket_id == 10
    for name, expected in fields.items():
        assert getattr(dto, name) == expected


def test_ticket_time_payload_mappers() -> None:
    scheduled = tr.ticket_schedule_request_to_dto(request=TicketScheduleRequest(planned_start_at=NOW, planned_finish_at=NOW), actor_admin_id=99, ticket_id=10)
    assert scheduled.planned_start_at == NOW and scheduled.planned_finish_at == NOW
    ready = tr.ticket_ready_to_work_request_to_dto(request=TicketReadyToWorkRequest(executor_id=7, planned_start_at=NOW), actor_admin_id=99, ticket_id=10)
    assert ready.executor_id == 7 and ready.planned_start_at == NOW
    completed = tr.ticket_record_completed_work_for_review_request_to_dto(
        request=TicketRecordCompletedWorkForReviewRequest(executor_id=7, actual_started_at=NOW, actual_finished_at=NOW), actor_admin_id=99, ticket_id=10
    )
    assert completed.actual_started_at == NOW and completed.actual_finished_at == NOW
    ret_sched = tr.ticket_return_to_scheduled_request_to_dto(request=TicketReturnToScheduledRequest(planned_start_at=NOW), actor_admin_id=99, ticket_id=10)
    assert ret_sched.planned_start_at == NOW
    ret_ready = tr.ticket_return_to_ready_to_work_request_to_dto(request=TicketReturnToReadyToWorkRequest(executor_id=7, planned_start_at=NOW), actor_admin_id=99, ticket_id=10)
    assert ret_ready.executor_id == 7


def test_user_ticket_mappers() -> None:
    create = utr.create_request_to_dto(
        request=utr.UserTicketCreateRequest(client_id=1, text_of_ticket="Need help", contact_user_id=2, department_id=3, is_remote=True), actor_user_id=20
    )
    assert create.actor_user_id == 20 and create.ticket_user_id == 0 and create.client_id == 1
    filtered = utr.user_filter_to_dto(actor_user_id=20, client_id=1)
    assert filtered.actor_user_id == 20 and filtered.client_id == 1
    by_id = utr.ticket_user_id_to_dto(actor_user_id=20, ticket_user_id=5)
    assert by_id.ticket_user_id == 5
    action = utr.action_request_to_dto(request=utr.UserTicketActionRequest(comment="done"), actor_user_id=20, ticket_user_id=5)
    assert action.ticket_user_id == 5 and action.comment == "done"
