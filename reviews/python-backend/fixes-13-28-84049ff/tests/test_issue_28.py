"""Exercise the remote first-line role through FastAPI and inspect persisted state."""

import secrets
import sqlite3

import pytest

from conftest import transaction


REMOTE = "ticket.at_work_remote"
GENERAL = "ticket.at_work"
OPERATION = "ticket.operation"
ASSIGN = "ticket.assign_executor"
RECOMMEND = "ticket.set_remote_recommendation"


def create_role(world, *permissions):
    response = world.api.post(
        "/admin/roles/admin",
        headers=world.admin_headers,
        json={"name": "Synthetic role " + secrets.token_hex(5), "permissions": list(permissions)},
    )
    assert response.status_code == 201, response.text
    assert set(response.json()["permissions"]) == set(permissions)
    return response.json()["role_id"]


def add_operator(world, *permissions):
    role_id = create_role(world, *permissions)
    login = "operator" + secrets.token_hex(5)
    password = "Aa1!" + secrets.token_hex(12)
    created = world.api.post(
        "/admin/admins/",
        headers=world.admin_headers,
        json={
            "first_name": "Synthetic operator",
            "department_id": world.department_id,
            "roles": [role_id],
            "login": login,
            "password": password,
        },
    )
    assert created.status_code == 201, created.text
    authenticated = world.api.post("/auth/admin/login", data={"username": login, "password": password})
    assert authenticated.is_success
    return created.json()["employee_id"], {"Authorization": "Bearer " + authenticated.json()["access_token"]}


def change_roles(world, employee_id, role_id, method):
    response = world.api.request(
        method, f"/admin/admins/{employee_id}/roles", headers=world.admin_headers,
        json={"roles": [role_id]},
    )
    assert response.status_code == 200, response.text


def accepted_pair(world, *, recommended):
    ticket_user_id = world.user_ticket(remote_work_recommended=recommended)["ticket_user_id"]
    with transaction(world.path) as uow:
        ticket_id = uow.tickets.get_by_user_ticket_id(ticket_user_id).ticket_id
    world.action(ticket_id, "department", {"department_id": world.department_id})
    world.action(ticket_id, "accept")
    return ticket_id, ticket_user_id


def ticket_state(world, pair):
    with transaction(world.path) as uow:
        ticket = uow.tickets.get(pair[0])
        ticket_user = uow.user_tickets.get(pair[1])
        return (
            ticket.remote_work_recommended,
            ticket.current_executor_id(),
            tuple((r.status.value, r.actor_employee_id, r.work_is_remote) for r in ticket.statuses),
            tuple(r.status.value for r in ticket_user.statuses),
            ticket.version,
            ticket_user.version,
        )


def command(world, pair, headers, action, body=None, *, expected=200):
    response = world.api.patch(f"/admin/tickets/{pair[0]}/{action}", headers=headers, json=body or {})
    assert response.status_code == expected, response.text
    return response.json()


def test_generic_operation_grants_no_recommendation_or_unrecommended_self_assignment(world):
    actor, headers = add_operator(world, REMOTE, OPERATION)
    pair = accepted_pair(world, recommended=False)
    before = ticket_state(world, pair)
    command(world, pair, headers, "executor", {"executor_id": actor}, expected=400)
    command(world, pair, headers, "remote-work-recommended", {"remote_work_recommended": True}, expected=403)
    command(world, pair, headers, "start-remote-work", expected=400)
    assert ticket_state(world, pair) == before

    world.action(pair[0], "executor", {"executor_id": actor})
    assigned = ticket_state(world, pair)
    command(world, pair, headers, "start-work", {"work_is_remote": True}, expected=403)
    command(world, pair, headers, "start-work", expected=403)
    command(world, pair, headers, "start-remote-work", expected=400)
    assert ticket_state(world, pair) == assigned


def test_scoped_role_completes_recommended_work_with_one_executor(world):
    actor, headers = add_operator(world, REMOTE)
    other, other_headers = add_operator(world, REMOTE)
    pair = accepted_pair(world, recommended=True)
    command(world, pair, headers, "executor", {"executor_id": other}, expected=403)
    command(world, pair, headers, "executor", {"executor_id": actor})
    assigned = ticket_state(world, pair)
    assert assigned[1] == actor
    assert assigned[2][-1] == ("assigned", actor, False)
    command(world, pair, headers, "start-work", expected=403)
    command(world, pair, headers, "start-work", {"work_is_remote": True}, expected=403)
    assert ticket_state(world, pair) == assigned
    command(world, pair, headers, "start-remote-work")

    started = ticket_state(world, pair)
    command(world, pair, other_headers, "pause-work", expected=400)
    command(world, pair, other_headers, "finish-work", expected=400)
    assert ticket_state(world, pair) == started
    command(world, pair, headers, "pause-work")
    paused = ticket_state(world, pair)
    command(world, pair, headers, "resume-work", expected=403)
    assert ticket_state(world, pair) == paused
    command(world, pair, headers, "resume-work", {"work_is_remote": True})
    command(world, pair, headers, "finish-work")
    resolved = ticket_state(world, pair)
    assert resolved[2][-5:] == (
        ("assigned", actor, False), ("at_work", actor, True), ("paused", actor, False),
        ("at_work", actor, True), ("ready_for_review", actor, False),
    )
    assert resolved[3][-1] == "waiting_for_confirmation"


def test_scoped_assignment_does_not_take_over_another_executor_or_pick_deferred_ticket(world):
    actor, headers = add_operator(world, REMOTE, OPERATION)
    pair = accepted_pair(world, recommended=True)
    world.action(pair[0], "executor", {"executor_id": world.admin_id})
    assigned = ticket_state(world, pair)
    command(world, pair, headers, "executor", {"executor_id": actor}, expected=400)
    command(world, pair, headers, "start-remote-work", expected=400)
    assert ticket_state(world, pair) == assigned

    world.action(pair[0], "defer", {"comment": "Synthetic reason"})
    deferred = ticket_state(world, pair)
    assert deferred[2][-1][0] == "deferred"
    command(world, pair, headers, "executor", {"executor_id": actor}, expected=400)
    assert ticket_state(world, pair) == deferred


def test_specialized_start_keeps_assignment_and_start_atomic(world):
    actor, headers = add_operator(world, REMOTE)
    pair = accepted_pair(world, recommended=True)
    before = ticket_state(world, pair)
    command(world, pair, headers, "start-remote-work")
    after = ticket_state(world, pair)
    assert after[1] == actor
    assert after[2] == before[2] + (("assigned", actor, False), ("at_work", actor, True))
    assert after[3] == before[3]


def test_dispatch_and_general_work_remain_possible_without_recommendation(world):
    catalog = world.api.get("/admin/roles/admin/permissions", headers=world.admin_headers)
    assert catalog.status_code == 200
    assert {ASSIGN, RECOMMEND} <= set(catalog.json())
    worker, worker_headers = add_operator(world, GENERAL)
    dispatcher, dispatcher_headers = add_operator(world, ASSIGN)
    pair = accepted_pair(world, recommended=False)
    command(world, pair, dispatcher_headers, "executor", {"executor_id": worker})
    command(world, pair, dispatcher_headers, "remote-work-recommended", {"remote_work_recommended": True}, expected=403)
    command(world, pair, worker_headers, "start-work", {"work_is_remote": True})
    after = ticket_state(world, pair)
    assert after[0:2] == (False, worker)
    assert after[2][-2:] == (("assigned", dispatcher, False), ("at_work", worker, True))

    command(world, pair, worker_headers, "finish-work")
    assert ticket_state(world, pair)[3][-1] == "waiting_for_confirmation"
    command(world, pair, dispatcher_headers, "executor", {"executor_id": worker})
    assert ticket_state(world, pair)[3][-1] == "in_work"
    command(world, pair, worker_headers, "start-work")
    assert ticket_state(world, pair)[2][-1] == ("at_work", worker, False)


@pytest.mark.parametrize("work_is_remote", [False, True], ids=["on-site", "remote"])
def test_changing_role_keeps_scope_for_existing_work(world, work_is_remote):
    actor, headers = add_operator(world, REMOTE)
    general_role_id = create_role(world, GENERAL)
    change_roles(world, actor, general_role_id, "POST")
    pair = accepted_pair(world, recommended=False)
    world.action(pair[0], "executor", {"executor_id": actor})
    command(world, pair, headers, "start-work", {"work_is_remote": work_is_remote})
    change_roles(world, actor, general_role_id, "DELETE")

    if not work_is_remote:
        before = ticket_state(world, pair)
        command(world, pair, headers, "pause-work", expected=400)
        command(world, pair, headers, "finish-work", expected=400)
        assert ticket_state(world, pair) == before
        return

    command(world, pair, headers, "pause-work")
    before = ticket_state(world, pair)
    command(world, pair, headers, "resume-work", {"work_is_remote": True}, expected=400)
    assert ticket_state(world, pair) == before


def test_admin_creation_and_replay_require_the_recommendation_grant(world):
    actor, headers = add_operator(world, OPERATION, REMOTE)
    keyed_headers = {**headers, "Idempotency-Key": secrets.token_hex(16)}
    body = {
        "client_id": world.client_id,
        "text_of_ticket": "Synthetic recommendation test",
        "remote_work_recommended": True,
    }

    def create_request(request_body, request_headers=keyed_headers):
        return world.api.post("/admin/tickets/", headers=request_headers, json=request_body)

    def counts():
        with sqlite3.connect(world.path) as db:
            return tuple(db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                         for table in ("tickets", "creation_results"))

    before = counts()
    assert create_request(body).status_code == 403
    assert counts() == before

    without_recommendation = create_request({**body, "remote_work_recommended": False}, headers)
    assert without_recommendation.status_code == 201
    assert without_recommendation.json()["remote_work_recommended"] is False

    role_id = create_role(world, RECOMMEND)
    change_roles(world, actor, role_id, "POST")
    first = create_request(body)
    assert first.status_code == 201, first.text
    assert first.json()["remote_work_recommended"] is True
    replay = create_request(body)
    assert replay.status_code == 201
    assert replay.json() == first.json()
    after = counts()
    assert after == (before[0] + 2, before[1] + 1)

    change_roles(world, actor, role_id, "DELETE")
    assert create_request(body).status_code == 403
    assert counts() == after


def test_recommendation_editor_does_not_gain_assignment_right(world):
    actor, headers = add_operator(world, RECOMMEND)
    pair = accepted_pair(world, recommended=False)
    command(world, pair, headers, "remote-work-recommended", {"remote_work_recommended": True})
    before = ticket_state(world, pair)
    assert before[:2] == (True, 0)
    command(world, pair, headers, "executor", {"executor_id": actor}, expected=403)
    assert ticket_state(world, pair) == before


def test_dispatcher_can_recommend_and_assign_another_employee_but_not_self(world):
    actor, headers = add_operator(world, ASSIGN, RECOMMEND)
    worker, _ = add_operator(world, GENERAL)
    pair = accepted_pair(world, recommended=False)
    command(world, pair, headers, "remote-work-recommended", {"remote_work_recommended": True})
    recommended = ticket_state(world, pair)
    assert recommended[:2] == (True, 0)

    command(world, pair, headers, "executor", {"executor_id": actor}, expected=403)
    assert ticket_state(world, pair) == recommended

    command(world, pair, headers, "executor", {"executor_id": worker})
    assigned = ticket_state(world, pair)
    assert assigned[:2] == (True, worker)
    assert assigned[2][-1] == ("assigned", actor, False)


def test_dispatch_right_does_not_override_hotline_self_assignment_conditions(world):
    actor, headers = add_operator(world, ASSIGN, REMOTE)
    unadvised = accepted_pair(world, recommended=False)
    before = ticket_state(world, unadvised)
    command(world, unadvised, headers, "executor", {"executor_id": actor}, expected=400)
    assert ticket_state(world, unadvised) == before

    advised = accepted_pair(world, recommended=True)
    other, _ = add_operator(world, GENERAL)
    world.action(advised[0], "executor", {"executor_id": other})
    before = ticket_state(world, advised)
    command(world, advised, headers, "executor", {"executor_id": actor}, expected=400)
    assert ticket_state(world, advised) == before

    unassigned = accepted_pair(world, recommended=True)
    command(world, unassigned, headers, "executor", {"executor_id": actor})
    assert ticket_state(world, unassigned)[:2] == (True, actor)


def test_preassigned_executor_needs_hotline_grant_to_start_hotline_work(world):
    dispatcher, dispatcher_headers = add_operator(world, ASSIGN)
    worker, worker_headers = add_operator(world, GENERAL)
    pair = accepted_pair(world, recommended=True)
    command(world, pair, dispatcher_headers, "executor", {"executor_id": worker})
    assigned = ticket_state(world, pair)
    assert assigned[1] == worker
    assert assigned[2][-1] == ("assigned", dispatcher, False)

    command(world, pair, worker_headers, "start-remote-work", expected=403)
    assert ticket_state(world, pair) == assigned

    hotline_role = create_role(world, REMOTE)
    change_roles(world, worker, hotline_role, "POST")
    command(world, pair, worker_headers, "start-remote-work")
    started = ticket_state(world, pair)
    assert started[1] == worker
    assert started[2] == assigned[2] + (("at_work", worker, True),)
    assert started[3] == assigned[3]
