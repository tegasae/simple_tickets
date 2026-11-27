"""Verify documented operations with minimal ordinary permissions."""
from contextlib import closing
import secrets
import sqlite3

from conftest import transaction
from test_shared_sessions import auth_data


def scoped_admin(world, permissions):
    role = world.api.post(
        "/admin/roles/admin", headers=world.admin_headers,
        json={"name": "Synthetic scoped role " + secrets.token_hex(4), "permissions": permissions},
    )
    assert role.status_code == 201
    login, password = "scoped" + secrets.token_hex(5), "Aa1!" + secrets.token_hex(12)
    operator = world.api.post(
        "/admin/admins/", headers=world.admin_headers,
        json={"first_name": "Synthetic scoped operator", "department_id": world.department_id,
              "roles": [role.json()["role_id"]], "login": login, "password": password},
    )
    assert operator.status_code == 201
    response = auth_data(world, "admin", login, password)
    return {"Authorization": "Bearer " + response["access_token"]}, operator.json()["employee_id"]


def linked_ticket_id(world, **payload):
    external_id = world.user_ticket(**payload)["ticket_user_id"]
    with transaction(world.path) as uow:
        return uow.tickets.get_by_user_ticket_id(external_id).ticket_id


def test_accept_has_body_and_separate_permission(world):
    """Пустой JSON для accept обязателен, право на обычную операцию даёт только смену отдела."""
    headers, _ = scoped_admin(world, ["ticket.operation"])
    ticket_id = linked_ticket_id(world)
    route = f"/admin/tickets/{ticket_id}/accept"
    assert world.api.patch(route, headers=world.admin_headers).status_code == 422
    assert world.api.patch(route, headers=headers, json={}).status_code == 403
    assert world.api.patch(route, headers=world.admin_headers, json={}).status_code == 200
    assert world.api.patch(f"/admin/tickets/{ticket_id}/department",
                           headers=headers, json={"department_id": world.department_id}).status_code == 200


def test_remote_work_requires_more_rights_for_preparation(world):
    """Один remote scope даёт старт подготовленной заявки, подготовка требует отдельных прав."""
    headers, executor_id = scoped_admin(world, ["ticket.at_work_remote"])
    ticket_id = linked_ticket_id(world, remote_work_recommended=True)
    root = f"/admin/tickets/{ticket_id}"
    assert world.api.patch(root + "/accept", headers=headers, json={}).status_code == 403
    assert world.api.patch(root + "/department", headers=headers,
                           json={"department_id": world.department_id}).status_code == 403
    world.action(ticket_id, "accept")
    world.action(ticket_id, "department", {"department_id": world.department_id})
    started = world.api.patch(root + "/start-remote-work", headers=headers, json={})
    assert started.status_code == 200
    result = started.json()
    assert result["current_executor_id"] == executor_id
    assert [s["status"] for s in result["statuses"][-2:]] == ["assigned", "at_work"]
    assert result["statuses"][-1]["work_is_remote"] is True


def test_department_create_and_followup_get_have_distinct_permissions(world):
    """Создание даёт 201 при DEPARTMENT_OPERATION, GET требует DEPARTMENT_VIEW."""
    writer_headers, _ = scoped_admin(world, ["department.operation"])
    created = world.api.post("/admin/departments/", headers=writer_headers,
                             json={"name": "Synthetic department created by an operator", "enabled": True})
    assert created.status_code == 201
    assert created.json()["enabled"] is True
    department_id = created.json()["department_id"]
    url = f"/admin/departments/{department_id}"
    assert world.api.get(url, headers=writer_headers).status_code == 403
    authorized = world.api.get(url, headers=world.admin_headers)
    assert authorized.status_code == 200 and authorized.json()["enabled"] is True


def test_user_ticket_create_does_not_accept_department_field(world):
    """User POST с внутренним department_id получает 422, пара не создаётся."""
    denied = world.api.post("/user/tickets/", headers=world.user_headers, json={
        "text_of_ticket": "Synthetic field validation", "department_id": world.department_id,
    })
    assert denied.status_code == 422
    with closing(sqlite3.connect(world.path)) as database:
        assert database.execute("SELECT count(*) FROM tickets").fetchone() == (0,)
        assert database.execute("SELECT count(*) FROM user_tickets").fetchone() == (0,)
