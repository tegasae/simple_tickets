import pytest

from conftest import database_uow
from src.domain.department import Department
from src.domain.employee import Admin


def create_pair(world, state):
    external = world.create_user_ticket()
    external_id = external["ticket_user_id"]
    with database_uow(world.path) as uow:
        internal_id = uow.tickets.get_by_user_ticket_id(external_id).ticket_id
    if state == "created":
        return internal_id, external_id
    world.admin_action(internal_id, "department", {"department_id": world.department_id})
    world.admin_action(internal_id, "accept")
    if state == "deferred":
        world.admin_action(internal_id, "defer", {"comment": "Waiting for contact"})
    elif state == "cancelled":
        world.admin_action(internal_id, "cancel", {"comment": "Synthetic cancellation"})
    elif state in {"assigned", "at_work", "paused", "ready_for_review", "executed"}:
        world.admin_action(internal_id, "executor", {"executor_id": world.admin_id})
        if state != "assigned":
            world.admin_action(internal_id, "start-work")
        if state == "paused":
            world.admin_action(internal_id, "pause-work")
        elif state in {"ready_for_review", "executed"}:
            world.admin_action(internal_id, "finish-work")
            if state == "executed":
                world.admin_action(internal_id, "execute")
    return internal_id, external_id


def change_contact(world, side, internal_id, external_id, contact_id):
    if side == "admin":
        path, headers = f"/admin/tickets/{internal_id}/contact-user", world.admin_headers
    else:
        path, headers = f"/user/tickets/{external_id}/contact-user", world.user_headers
    return world.client.patch(path, headers=headers, json={"contact_user_id": contact_id})


@pytest.mark.parametrize("state", ["created", "accepted", "deferred"])
@pytest.mark.parametrize("side", ["admin", "user"])
def test_both_sides_change_contact_in_editable_pair(world, side, state):
    internal_id, external_id = create_pair(world, state)
    with database_uow(world.path) as uow:
        expected_status = uow.tickets.get(internal_id).current_status()
        expected_external_status = uow.user_tickets.get(external_id).current_status()
    for contact_id in (world.contact_id, world.user_id):
        response = change_contact(world, side, internal_id, external_id, contact_id)
        assert response.status_code == 200, response.text
        assert response.json()["contact_user_id"] == contact_id
        with database_uow(world.path) as uow:
            internal = uow.tickets.get(internal_id)
            external = uow.user_tickets.get(external_id)
            assert internal.contact_user_id == external.contact_user_id == contact_id
            assert internal.current_status() == expected_status
            assert external.current_status() == expected_external_status


@pytest.mark.parametrize("state", [
    "assigned", "at_work", "paused", "ready_for_review", "executed", "cancelled",
])
@pytest.mark.parametrize("side", ["admin", "user"])
def test_contact_edit_does_not_open_other_internal_states(world, side, state):
    internal_id, external_id = create_pair(world, state)
    with database_uow(world.path) as uow:
        internal = uow.tickets.get(internal_id)
        external = uow.user_tickets.get(external_id)
        original = (
            internal.contact_user_id, external.contact_user_id,
            internal.current_status(), external.current_status(),
            len(internal.statuses), len(external.statuses),
        )
    response = change_contact(world, side, internal_id, external_id, world.contact_id)
    assert response.status_code == 400, response.text
    with database_uow(world.path) as uow:
        internal = uow.tickets.get(internal_id)
        external = uow.user_tickets.get(external_id)
        assert (
            internal.contact_user_id, external.contact_user_id,
            internal.current_status(), external.current_status(),
            len(internal.statuses), len(external.statuses),
        ) == original


def test_contact_permission_does_not_expand_user_description_edit(world):
    _, external_id = create_pair(world, "accepted")
    response = world.client.patch(
        f"/user/tickets/{external_id}/description", headers=world.user_headers,
        json={"description": "Not editable after acceptance"},
    )
    assert response.status_code == 400, response.text
    with database_uow(world.path) as uow:
        assert uow.user_tickets.get(external_id).description.value == ""


@pytest.mark.parametrize("remedy", ["enable_department", "remove_department"])
def test_admin_enable_requires_enabled_department_or_no_assignment(world, remedy):
    with database_uow(world.path) as uow:
        department = uow.departments.save(Department.create(name="Inactive support"))
        admin = uow.admins.save(Admin.create(
            first_name="Inactive operator", enabled=False,
            department_id=department.department_id,
        ))
        department_id, admin_id = department.department_id, admin.employee_id
    response = world.client.patch(
        f"/admin/departments/{department_id}/disable", headers=world.admin_headers,
    )
    assert response.status_code == 200, response.text
    with database_uow(world.path) as uow:
        version_before = uow.departments.get(department_id).version
    response = world.client.patch(
        f"/admin/admins/{admin_id}/enable", headers=world.admin_headers,
    )
    assert response.status_code == 400, response.text
    with database_uow(world.path) as uow:
        assert not uow.admins.get(admin_id).enabled
        assert not uow.departments.get(department_id).enabled
        assert uow.departments.get(department_id).version == version_before
    if remedy == "enable_department":
        response = world.client.patch(
            f"/admin/departments/{department_id}/enable", headers=world.admin_headers,
        )
    else:
        response = world.client.delete(
            f"/admin/admins/{admin_id}/department", headers=world.admin_headers,
        )
    assert response.status_code == 200, response.text
    with database_uow(world.path) as uow:
        department_version_before_enable = uow.departments.get(department_id).version
    response = world.client.patch(
        f"/admin/admins/{admin_id}/enable", headers=world.admin_headers,
    )
    assert response.status_code == 200, response.text
    with database_uow(world.path) as uow:
        admin = uow.admins.get(admin_id)
        assert admin.enabled
        if remedy == "enable_department":
            assert admin.department_id == department_id
            assert uow.departments.get(department_id).enabled
            assert uow.departments.get(department_id).version == department_version_before_enable + 1
        else:
            assert admin.department_id == 0
            assert not uow.departments.get(department_id).enabled
            assert uow.departments.get(department_id).version == department_version_before_enable


def test_admin_without_department_can_be_enabled(world):
    with database_uow(world.path) as uow:
        admin = uow.admins.save(Admin.create(first_name="Unassigned operator", enabled=False))
        admin_id = admin.employee_id
    response = world.client.patch(
        f"/admin/admins/{admin_id}/enable", headers=world.admin_headers,
    )
    assert response.status_code == 200, response.text
    with database_uow(world.path) as uow:
        admin = uow.admins.get(admin_id)
        assert admin.enabled and admin.department_id == 0
