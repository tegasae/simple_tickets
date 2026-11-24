import pytest

from conftest import database_uow


@pytest.mark.parametrize("target", ["clients", "users"])
def test_review_pair_is_closed_when_owner_or_client_disabled(world, target):
    internal_id, external_id = world.work_pair(finish=True)
    entity_id = world.client_id if target == "clients" else world.user_id
    for _ in range(2):
        response = world.client.patch(
            f"/admin/{target}/{entity_id}/disable", headers=world.admin_headers,
        )
        assert response.status_code == 200, response.text
    with database_uow(world.path) as uow:
        internal, external = uow.tickets.get(internal_id), uow.user_tickets.get(external_id)
        assert internal.current_status() == external.current_status() == "suspended"
        assert internal.is_closed and external.is_closed
        assert sum(record.status == "suspended" for record in external.statuses) == 1


def test_active_pair_survives_client_disable_and_can_finish(world):
    internal_id, external_id = world.work_pair()
    response = world.client.patch(
        f"/admin/clients/{world.client_id}/disable", headers=world.admin_headers,
    )
    assert response.status_code == 200
    with database_uow(world.path) as uow:
        assert uow.tickets.get(internal_id).current_status() == "at_work"
        assert uow.user_tickets.get(external_id).current_status() == "in_work"
    world.admin_action(internal_id, "finish-work")
    with database_uow(world.path) as uow:
        assert uow.tickets.get(internal_id).current_status() == "ready_for_review"
        assert uow.user_tickets.get(external_id).current_status() == "waiting_for_confirmation"


def test_selected_contact_and_ordinary_comment_roundtrip(world):
    created = world.create_user_ticket(contact_user_id=world.contact_id, comment="Synthetic note")
    external_id = created["ticket_user_id"]
    response = world.client.get(f"/user/tickets/{external_id}", headers=world.user_headers)
    assert response.status_code == 200
    assert response.json()["contact_user_id"] == world.contact_id
    assert response.json()["comments"][0]["comment"] == "Synthetic note"
    with database_uow(world.path) as uow:
        assert uow.tickets.get_by_user_ticket_id(external_id).contact_user_id == world.contact_id


def test_comment_created_by_staff_preserves_actual_author(world):
    response = world.client.post("/admin/tickets/", headers=world.admin_headers, json={
        "client_id": world.client_id, "user_id": world.user_id,
        "text_of_ticket": "Synthetic staff request", "comment": "Synthetic staff note",
    })
    assert response.status_code == 201
    with database_uow(world.path) as uow:
        external = uow.user_tickets.get(response.json()["user_ticket_id"])
        assert external.comments[0].employee_id == world.admin_id


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_refresh_is_bound_to_same_subject_after_login_is_reassigned(world, tmp_path, backend):
    if backend == "sqlite":
        from src.web.auth.storage_sqlite import TokenStorageSQLite
        world.client.app.state.refresh_token_storage = TokenStorageSQLite(tmp_path / "synthetic-refresh.sqlite3")
        login = world.client.post("/auth/user/login", data={
            "username": world.user_login, "password": world.password,
        })
        assert login.status_code == 200
        refresh = login.json()["refresh_token"]
    else:
        refresh = world.refresh
    removed = world.client.delete(
        f"/admin/users/{world.user_id}/account", headers=world.admin_headers,
    )
    assert removed.status_code == 200
    attached = world.client.post(
        f"/admin/users/{world.contact_id}/account", headers=world.admin_headers,
        json={"login": world.user_login, "password": world.password},
    )
    assert attached.status_code == 200, attached.text
    response = world.client.post("/auth/user/refresh", json={"refresh_token": refresh})
    assert response.status_code == 401
