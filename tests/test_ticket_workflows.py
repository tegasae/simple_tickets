"""HTTP regressions for scoped work permissions and linked ticket histories."""

from dataclasses import dataclass
import secrets

import pytest

from src.domain.rbac.permissions import AdminPermission, UserPermission
from test_creation_and_refresh import application


@dataclass(frozen=True)
class TicketPair:
    internal: str
    external: str


@pytest.fixture
def support_department(application):
    response = application.api.post(
        "/admin/departments/", headers=application.admin_headers, json={"name": "Test support"},
    )
    assert response.status_code == 201, response.text
    return response.json()["department_id"]


@pytest.fixture
def ticket_requester(application):
    role = application.api.post(
        "/admin/roles/user",
        headers=application.admin_headers,
        json={
            "name": "Test requester role",
            "permissions": [UserPermission.TICKET_OPERATION, UserPermission.TICKET_VIEW],
        },
    )
    assert role.status_code == 201, role.text
    granted = application.api.post(
        f"/admin/users/{application.user_id}/roles",
        headers=application.admin_headers,
        json={"roles": [role.json()["role_id"]]},
    )
    assert granted.status_code == 200, granted.text
    return application.user_headers


def add_operator(application, department_id, permission):
    role = application.api.post(
        "/admin/roles/admin",
        headers=application.admin_headers,
        json={"name": f"Test {permission}", "permissions": [permission]},
    )
    assert role.status_code == 201, role.text
    assert role.json()["permissions"] == [permission]

    login = "operator" + secrets.token_hex(5)
    password = "Aa1!" + secrets.token_hex(12)
    employee = application.api.post(
        "/admin/admins/",
        headers=application.admin_headers,
        json={
            "first_name": "Test operator",
            "department_id": department_id,
            "roles": [role.json()["role_id"]],
            "login": login,
            "password": password,
        },
    )
    assert employee.status_code == 201
    auth = application.api.post("/auth/admin/login", data={"username": login, "password": password})
    assert auth.status_code == 200
    return employee.json()["employee_id"], {"Authorization": "Bearer " + auth.json()["access_token"]}


def transition(application, path, action, headers, *, body=None, expected=200):
    response = application.api.patch(f"{path}/{action}", headers=headers, json={} if body is None else body)
    assert response.status_code == expected, response.text
    return response.json()


def accepted_pair(application, department_id, requester, *, recommended):
    created = application.api.post(
        "/user/tickets/",
        headers=requester,
        json={"text_of_ticket": "Test support request", "remote_work_recommended": recommended},
    )
    assert created.status_code == 201, created.text
    assert created.json()["current_status"] == "created"
    ticket_user_id = created.json()["ticket_user_id"]

    listing = application.api.get("/admin/tickets/", headers=application.admin_headers)
    assert listing.status_code == 200, listing.text
    linked = [ticket for ticket in listing.json() if ticket["user_ticket_id"] == ticket_user_id]
    assert len(linked) == 1
    ticket = linked[0]
    assert ticket["remote_work_recommended"] is recommended
    pair = TicketPair(f"/admin/tickets/{ticket['ticket_id']}", f"/user/tickets/{ticket_user_id}")
    transition(
        application, pair.internal, "department", application.admin_headers,
        body={"department_id": department_id},
    )
    transition(application, pair.internal, "accept", application.admin_headers)
    return pair


def read_pair(application, pair, requester):
    internal = application.api.get(pair.internal, headers=application.admin_headers)
    external = application.api.get(pair.external, headers=requester)
    assert internal.status_code == 200, internal.text
    assert external.status_code == 200, external.text
    return internal.json(), external.json()


def statuses(ticket):
    return [entry["status"] for entry in ticket["statuses"]]


def test_hotline_needs_recommendation_to_self_assign_or_start(
    application, support_department, ticket_requester,
):
    hotline, headers = add_operator(application, support_department, AdminPermission.TICKET_AT_WORK_REMOTE)
    pair = accepted_pair(application, support_department, ticket_requester, recommended=False)
    before = read_pair(application, pair, ticket_requester)

    transition(application, pair.internal, "executor", headers, body={"executor_id": hotline}, expected=400)
    transition(application, pair.internal, "start-remote-work", headers, expected=400)
    assert read_pair(application, pair, ticket_requester) == before


@pytest.mark.parametrize("assign_first", [True, False], ids=["self-assigned", "direct-start"])
def test_hotline_can_start_recommended_work_only_as_own_executor(
    application, support_department, ticket_requester, assign_first,
):
    hotline, headers = add_operator(application, support_department, AdminPermission.TICKET_AT_WORK_REMOTE)
    other, _ = add_operator(application, support_department, AdminPermission.TICKET_AT_WORK)
    pair = accepted_pair(application, support_department, ticket_requester, recommended=True)
    before = read_pair(application, pair, ticket_requester)

    transition(application, pair.internal, "executor", headers, body={"executor_id": other}, expected=403)
    assert read_pair(application, pair, ticket_requester) == before

    if assign_first:
        assigned = transition(
            application, pair.internal, "executor", headers, body={"executor_id": hotline},
        )
        assert assigned["current_executor_id"] == hotline
        assert statuses(assigned)[-1] == "assigned"

    started = transition(application, pair.internal, "start-remote-work", headers)
    assert started["current_executor_id"] == hotline
    assert statuses(started)[-2:] == ["assigned", "at_work"]
    assert started["statuses"][-1]["work_is_remote"] is True


def test_dispatcher_and_worker_complete_a_linked_ticket(application, support_department, ticket_requester):
    dispatcher, dispatcher_headers = add_operator(
        application, support_department, AdminPermission.TICKET_ASSIGN_EXECUTOR,
    )
    worker, worker_headers = add_operator(application, support_department, AdminPermission.TICKET_AT_WORK)
    pair = accepted_pair(application, support_department, ticket_requester, recommended=True)

    transition(
        application, pair.internal, "executor", dispatcher_headers,
        body={"executor_id": dispatcher}, expected=403,
    )
    assigned = transition(
        application, pair.internal, "executor", dispatcher_headers, body={"executor_id": worker},
    )
    assert assigned["current_executor_id"] == worker

    transition(application, pair.internal, "start-remote-work", worker_headers, expected=403)
    started = transition(application, pair.internal, "start-work", worker_headers)
    assert started["statuses"][-1]["work_is_remote"] is False
    transition(application, pair.internal, "pause-work", worker_headers)
    transition(application, pair.internal, "resume-work", worker_headers)
    transition(
        application, pair.internal, "finish-work", worker_headers, body={"comment": "Work completed"},
    )

    ready_internal, ready_external = read_pair(application, pair, ticket_requester)
    assert statuses(ready_internal)[-1] == "ready_for_review"
    assert ready_external["current_status"] == "waiting_for_confirmation"

    transition(
        application, pair.external, "confirm", ticket_requester, body={"comment": "Result confirmed"},
    )
    internal, external = read_pair(application, pair, ticket_requester)
    assert internal["is_closed"] and external["is_closed"]
    assert statuses(internal) == [
        "created_from_ticket_user", "accepted", "assigned", "at_work", "paused",
        "at_work", "ready_for_review", "confirmed_by_user",
    ]
    assert statuses(external) == ["created", "in_work", "waiting_for_confirmation", "confirmed_by_user"]
    assert internal["statuses"][-1]["comment"] == external["statuses"][-1]["comment"] == "Result confirmed"

    transition(
        application, pair.internal, "cancel", application.admin_headers,
        body={"comment": "Cancel a confirmed ticket"}, expected=400,
    )
    assert read_pair(application, pair, ticket_requester) == (internal, external)


def test_cancel_appends_the_reason_to_both_ticket_histories(
    application, support_department, ticket_requester,
):
    pair = accepted_pair(application, support_department, ticket_requester, recommended=False)
    reason = "Request no longer needed"
    transition(application, pair.internal, "cancel", application.admin_headers, body={"comment": reason})

    internal, external = read_pair(application, pair, ticket_requester)
    assert internal["is_closed"] and external["is_closed"]
    assert statuses(internal) == ["created_from_ticket_user", "accepted", "cancelled"]
    assert statuses(external) == ["created", "in_work", "cancelled_by_admin"]
    assert internal["statuses"][-1]["comment"] == external["statuses"][-1]["comment"] == reason
