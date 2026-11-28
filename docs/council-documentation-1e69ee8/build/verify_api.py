from contextlib import closing
import json
import logging
from pathlib import Path
import secrets
import sqlite3
import sys
from tempfile import TemporaryDirectory

import pytest

SOURCE = Path.cwd()
RUN = SOURCE.parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE / "tests"))

from src.domain.rbac.permissions import AdminPermission as P
from test_creation_and_refresh import application
from test_ticket_deletion_permission import persisted_ticket_records

logging.disable(logging.CRITICAL)
MISSING = object()

def show(group, **evidence):
    print(json.dumps({"group": group, **evidence}, ensure_ascii=False), flush=True)


def verify(app):
    api = app.api
    supervisor = app.admin_headers

    def http(method, path, *, actor=supervisor, body=MISSING, form=MISSING, expected=200):
        request_args = {"headers": actor}
        if body is not MISSING:
            request_args["json"] = body
        if form is not MISSING:
            request_args["data"] = form
        response = api.request(method, path, **request_args)
        assert response.status_code == expected, (method, path.split("/")[-1], expected, response.status_code)
        return response

    def catalog(method, path, body, *, actor=supervisor):
        return http(method, path, actor=actor, body=body, expected=201).json()

    def add_role(area, name, permissions):
        role = catalog("POST", f"/admin/roles/{area}", {"name": name, "permissions": permissions})
        assert set(role["permissions"]) == set(permissions)
        return role["role_id"]

    def create_account(area, path, body):
        login = "sample" + secrets.token_hex(6)
        password = "Aa1!" + secrets.token_hex(16)
        record = catalog("POST", path, dict(body, login=login, password=password))
        login_form = {"username": login, "password": password}
        response = http("POST", f"/auth/{area}/login", actor={}, form=login_form)
        return record, response.json()

    def bearer(tokens):
        return {"Authorization": "Bearer " + tokens["access_token"]}

    dept = catalog("POST", "/admin/departments/", {"name": "Поддержка"})["department_id"]
    alternate_dept = catalog("POST", "/admin/departments/", {"name": "Второй отдел"})["department_id"]
    disabled = catalog("POST", "/admin/departments/", {"name": "Архивный отдел", "enabled": False})
    assert not disabled["enabled"]
    assert http("GET", f"/admin/departments/{dept}").json()["enabled"]
    client = catalog("POST", "/admin/clients/", {"name": "Учебная организация"})["client_id"]
    requester_role = add_role("user", "Автор обращений", ["ticket.operation", "ticket.view"])
    requester, requester_login = create_account("user", "/admin/users/", {
        "client_id": client, "first_name": "Автор", "roles": [requester_role]
    })
    main_user = requester["employee_id"]
    user = bearer(requester_login)
    contact = catalog("POST", "/admin/users/", {"client_id": client, "first_name": "Контакт"})
    contact_id = contact["employee_id"]
    engineer_role = add_role("admin", "Учебный инженер", [P.TICKET_AT_WORK])
    engineer, engineer_login = create_account("admin", "/admin/admins/", {
        "department_id": dept, "first_name": "Инженер", "roles": [engineer_role]
    })
    worker = bearer(engineer_login)
    engineer_id = engineer["employee_id"]
    foreign = catalog("POST", "/admin/admins/", {"first_name": "Другой инженер", "department_id": alternate_dept})
    creator_role = add_role("admin", "Регистрация обращений", [P.TICKET_CREATED])
    creator, creator_login = create_account("admin", "/admin/admins/", {
        "department_id": dept, "first_name": "Регистратор", "roles": [creator_role]
    })
    registrar = bearer(creator_login)
    dispatcher_role = add_role("admin", "Учебный диспетчер", [P.TICKET_ASSIGN_EXECUTOR, P.TICKET_SET_REMOTE_RECOMMENDATION])
    _, dispatcher_login = create_account("admin", "/admin/admins/", {
        "department_id": dept, "first_name": "Диспетчер", "roles": [dispatcher_role]
    })
    dispatcher = bearer(dispatcher_login)
    hotline_role = add_role("admin", "Учебная горячая линия", [P.TICKET_AT_WORK_REMOTE])
    hotline, hotline_login = create_account("admin", "/admin/admins/", {
        "department_id": dept, "first_name": "Инженер линии", "roles": [hotline_role]
    })
    remote = bearer(hotline_login)

    assert requester["enabled"] and requester["enabled_login"]
    assert engineer["department_id"] == dept and engineer["enabled_login"]
    show("catalog", role_fields=["name", "permissions"], client=True, user=True,
         admin=True, department_default=True, department_explicit_false=True)

    old_refresh = engineer_login["refresh_token"]
    def session_interval():
        with closing(sqlite3.connect(app.database)) as db:
            return db.execute(
                "SELECT created_at, expires_at FROM auth_refresh_sessions WHERE subject_id=? AND subject_type=?",
                (engineer_id, "admin"),
            ).fetchall()
    interval = session_interval()
    assert len(interval) == 1 and round(interval[0][1] - interval[0][0]) == 604800
    rotated = http("POST", "/auth/admin/refresh", actor={}, body={"refresh_token": old_refresh}).json()
    assert rotated["refresh_token"] != old_refresh
    assert session_interval() == interval
    revoked = http("POST", "/auth/admin/refresh", actor={}, body={"refresh_token": old_refresh}, expected=401)
    assert revoked.headers["WWW-Authenticate"] == "Bearer"
    assert revoked.json() == {"detail": "Invalid credentials or session"}
    http("POST", "/auth/admin/logout", actor={}, body={"refresh_token": rotated["refresh_token"]})
    http("POST", "/auth/admin/refresh", actor={}, body={"refresh_token": rotated["refresh_token"]}, expected=401)
    http("GET", "/admin/admins/permissions", actor=worker)
    assert engineer_login["token_type"] == "bearer" and 0 < engineer_login["expires_in"] <= 300
    assert requester_login["token_type"] == "bearer" and 0 < requester_login["expires_in"] <= 300
    show("auth", token_response_fields=sorted(engineer_login),
         default_access_reported_seconds=engineer_login["expires_in"], absolute_refresh_seconds=604800,
         previous_refresh_401=revoked.json(), valid_access_after_logout=200)

    retained = catalog("POST", "/admin/admins/", {"department_id": dept, "first_name": "Перевод"})
    profile = f"/admin/admins/{retained['employee_id']}"
    omitted = http("PUT", profile, body={"first_name": "Новое имя"}).json()
    assert omitted["department_id"] == 0
    http("PATCH", profile + "/department", body={"department_id": dept})
    explicit = http("PUT", profile, body={"first_name": "Перевод", "department_id": 0}).json()
    assert explicit["department_id"] == 0
    guard_department = catalog("POST", "/admin/departments/", {"name": "Отдел проверки включения"})
    guard_id = guard_department["department_id"]
    guard_admin = catalog("POST", "/admin/admins/", {"first_name": "Сотрудник отдела", "department_id": guard_id})
    guard_profile = f"/admin/admins/{guard_admin['employee_id']}"
    assert not http("PATCH", guard_profile + "/disable").json()["enabled"]
    assert not http("PATCH", f"/admin/departments/{guard_id}/disable").json()["enabled"]
    enable_denied = http("PATCH", guard_profile + "/enable", expected=400).json()
    assert http("DELETE", guard_profile + "/department").json()["department_id"] == 0
    assert http("PATCH", guard_profile + "/enable").json()["enabled"]
    show("profile_department", omitted_department_id=omitted["department_id"],
         explicit_zero_department_id=explicit["department_id"], disabled_department_enable_denied=enable_denied["error_type"],
         enable_after_unassign=200)

    def internal(tid):
        return http("GET", f"/admin/tickets/{tid}").json()

    def external(tuid, *, actor=user):
        return http("GET", f"/user/tickets/{tuid}", actor=actor).json()

    def status(ticket):
        return ticket["statuses"][-1]["status"]

    def action(tid, route, *, actor=supervisor, body=None, expected=200):
        return http("PATCH", f"/admin/tickets/{tid}/{route}", actor=actor,
                    body={} if body is None else body, expected=expected)

    def user_pair(title, *, actor=user, contact=0, ticket_department=dept):
        request = {"text_of_ticket": title}
        if contact:
            request["contact_user_id"] = contact
        created = catalog("POST", "/user/tickets/", request, actor=actor)
        linked = [ticket for ticket in http("GET", "/admin/tickets/").json()
                  if ticket["user_ticket_id"] == created["ticket_user_id"]]
        assert len(linked) == 1 and created["current_status"] == "created"
        assert status(linked[0]) == "created_from_ticket_user"
        tid = linked[0]["ticket_id"]
        action(tid, "department", body={"department_id": ticket_department})
        action(tid, "accept")
        return tid, created

    root_created = catalog("POST", "/admin/tickets/", {
        "client_id": client, "text_of_ticket": "Внутренняя запись",
    })
    assert [r["status"] for r in root_created["statuses"]] == ["created", "accepted"]
    assert root_created["user_ticket_id"] == 0
    registered = catalog("POST", "/admin/tickets/", {
        "client_id": client, "user_id": main_user, "text_of_ticket": "Записано со слов пользователя",
        "comment": "Зафиксировано при обращении",
    }, actor=registrar)
    registered_ext = external(registered["user_ticket_id"])
    assert status(registered) == "created_from_request_user"
    assert registered["statuses"][0]["actor_id"] == creator["employee_id"]
    assert registered_ext["statuses"][0]["actor_id"] == main_user
    for record in (registered["comments"][-1], registered_ext["comments"][-1]):
        assert record["actor_id"] == creator["employee_id"]
        assert record["comment"] == "Зафиксировано при обращении"
    external_contact = f"/user/tickets/{registered['user_ticket_id']}/contact-user"
    updated_external = http("PATCH", external_contact, actor=user, body={"contact_user_id": contact_id}).json()
    assert updated_external["contact_user_id"] == internal(registered["ticket_id"])["contact_user_id"] == contact_id
    reset_external = http("PATCH", external_contact, actor=user, body={"contact_user_id": 0}).json()
    assert reset_external["contact_user_id"] == internal(registered["ticket_id"])["contact_user_id"] == main_user
    action(registered["ticket_id"], "contact-user", body={"contact_user_id": 0}, expected=400)

    tid, original_ext = user_pair("Восстановить доступ")
    tuid = original_ext["ticket_user_id"]
    assert original_ext["contact_user_id"] == main_user
    assert original_ext["statuses"][0]["actor_id"] == main_user
    assert external(tuid)["current_status"] == "in_work"
    changed_contact = action(tid, "contact-user", body={"contact_user_id": contact_id}).json()
    assert changed_contact["contact_user_id"] == external(tuid)["contact_user_id"] == contact_id
    show("pair", standalone_admin=["created", "accepted"], standalone_no_user_ticket=True,
         admin_for_user_internal=status(registered), admin_for_user_external=registered_ext["current_status"],
         admin_for_user_history_authors=["Admin-регистратор", "User"],
         shared_comment_author="Admin-регистратор", shared_comment_is_string=True,
         user_contact_zero_resets_to_owner=True, admin_contact_zero_linked_400=True,
         user_created_external=original_ext["current_status"], user_created_internal="created_from_ticket_user",
         pair_after_accept=[status(changed_contact), external(tuid)["current_status"]],
         default_contact="User-владелец", updated_both_contacts=True)

    before = persisted_ticket_records(app, tid, tuid)
    wrong_department = action(tid, "executor", actor=dispatcher, body={"executor_id": foreign["employee_id"]}, expected=400)
    assert persisted_ticket_records(app, tid, tuid) == before
    action(tid, "remote-work-recommended", actor=dispatcher, body={"remote_work_recommended": True})
    assigned = action(tid, "executor", actor=dispatcher, body={"executor_id": engineer_id}).json()
    assert status(assigned) == "assigned" and assigned["current_executor_id"] == engineer_id
    action(tid, "remote-work-recommended", actor=dispatcher, body={"remote_work_recommended": False}, expected=400)
    dedicated_denied = action(tid, "start-remote-work", actor=worker, expected=403)
    started = action(tid, "start-work", actor=worker).json()
    assert status(started) == "at_work" and started["statuses"][-1]["work_is_remote"] is False
    disable_assigned = http("PATCH", f"/admin/admins/{engineer_id}/disable", expected=400)
    update_assigned = http("PUT", f"/admin/admins/{engineer_id}", body={"first_name": "Профиль"}, expected=400)
    show("assignment", wrong_department_400=wrong_department.json()["error_type"],
         assigned_status=status(assigned), assigned_executor="Инженер",
         dedicated_remote_without_right_403=dedicated_denied.json(),
         start_status=status(started), actual_work_is_remote=False,
         disable_current_executor_400=disable_assigned.json()["error_type"],
         omit_department_current_executor_400=update_assigned.json()["error_type"])

    ready = action(tid, "finish-work", actor=worker, body={"comment": "Работа выполнена"}).json()
    assert status(ready) == "ready_for_review" and external(tuid)["current_status"] == "waiting_for_confirmation"
    before = persisted_ticket_records(app, tid, tuid)
    denied = action(tid, "execute", actor=worker, expected=403)
    assert persisted_ticket_records(app, tid, tuid) == before
    final = action(tid, "execute", body={"comment": "Результат принят"}).json()
    final_ext = external(tuid)
    assert status(final) == "executed" and final_ext["current_status"] == "confirmed_by_admin"
    assert final["is_closed"] and final_ext["is_closed"]
    for record in (final["statuses"][-1], final_ext["statuses"][-1]):
        assert record["actor_id"] == app.admin_id and record["comment"] == "Результат принят"
    after = persisted_ticket_records(app, tid, tuid)
    repeated = action(tid, "execute", expected=400)
    assert persisted_ticket_records(app, tid, tuid) == after
    show("execute", before=["ready_for_review", "waiting_for_confirmation"], denied_403=denied.json(),
         after=[status(final), final_ext["current_status"]], closing_actor="Проверяющий Admin",
         closing_comment=final["statuses"][-1]["comment"], is_closed=True,
         repeated_400=repeated.json(), rejection_preserves_pair=True)

    second_requester, second_login = create_account("user", "/admin/users/", {
        "client_id": client, "first_name": "Другой автор", "roles": [requester_role]
    })
    second_user = bearer(second_login)
    remote_tid, remote_external = user_pair("Удалённая диагностика", actor=second_user)
    before = persisted_ticket_records(app, remote_tid, remote_external["ticket_user_id"])
    no_rec = action(remote_tid, "start-remote-work", actor=remote, expected=400)
    action(remote_tid, "executor", actor=remote, body={"executor_id": hotline["employee_id"]}, expected=400)
    assert persisted_ticket_records(app, remote_tid, remote_external["ticket_user_id"]) == before
    action(remote_tid, "remote-work-recommended", actor=dispatcher, body={"remote_work_recommended": True})
    remote_started = action(remote_tid, "start-remote-work", actor=remote).json()
    assert remote_started["current_executor_id"] == hotline["employee_id"]
    assert [record["status"] for record in remote_started["statuses"]][-2:] == ["assigned", "at_work"]
    assert remote_started["statuses"][-1]["work_is_remote"] is True
    show("hotline", no_recommendation_400=no_rec.json(), tail=["assigned", "at_work"],
         current_executor="Инженер горячей линии", work_is_remote=True)

    def database_statuses(pair):
        ticket, ticket_user = pair
        records = persisted_ticket_records(app, ticket, ticket_user)
        with closing(sqlite3.connect(app.database)) as db:
            internal_sql = "SELECT status FROM ticket_status_records WHERE ticket_id=? ORDER BY status_id DESC LIMIT 1"
            external_sql = "SELECT status FROM user_tickets_status_record WHERE user_ticket_id=? ORDER BY user_ticket_status_record_id DESC LIMIT 1"
            return [db.execute(internal_sql, (ticket,)).fetchone()[0],
                    db.execute(external_sql, (ticket_user,)).fetchone()[0]], records

    contact_case, contact_external = user_pair("Проверка отдельного контакта", contact=contact_id)
    action(contact_case, "executor", actor=dispatcher, body={"executor_id": engineer_id})
    action(contact_case, "start-work", actor=worker)
    action(contact_case, "finish-work", actor=worker)
    contact_disabled = http("PATCH", f"/admin/users/{contact_id}/disable").json()
    contact_after = external(contact_external["ticket_user_id"])
    assert not contact_disabled["enabled"] and status(internal(contact_case)) == contact_after["current_status"] == "suspended"
    assert contact_after["is_closed"] and http("GET", f"/admin/users/{main_user}").json()["enabled"]
    show("disable_contact", before=["ready_for_review", "waiting_for_confirmation"],
         after=["suspended", "suspended"], contact_enabled=False, owner_enabled=True)

    account_case, account_external = user_pair("Аккаунт и сотрудник")
    account_pair = (account_case, account_external["ticket_user_id"])
    action(account_case, "executor", actor=dispatcher, body={"executor_id": engineer_id})
    action(account_case, "start-work", actor=worker)
    action(account_case, "finish-work", actor=worker)
    before_account = persisted_ticket_records(app, *account_pair)
    account_disabled = http("PATCH", f"/admin/users/{main_user}/account/disable").json()
    assert account_disabled["enabled"] and not account_disabled["enabled_login"]
    assert persisted_ticket_records(app, *account_pair) == before_account
    http("GET", f"/user/tickets/{account_pair[1]}", actor=user, expected=401)
    stale_refresh = requester_login["refresh_token"]
    http("POST", "/auth/user/refresh", actor={}, body={"refresh_token": stale_refresh}, expected=401)
    http("PATCH", f"/admin/users/{main_user}/account/enable")
    http("POST", "/auth/user/refresh", actor={}, body={"refresh_token": stale_refresh}, expected=401)
    show("disable_account", employee_enabled=True, enabled_login=False, ticket_history_preserved=True,
         previous_refresh_after_enable=401)

    main_disabled = http("PATCH", f"/admin/users/{main_user}/disable").json()
    assert not main_disabled["enabled"]
    owner_states, _ = database_statuses(account_pair)
    assert owner_states == ["suspended", "suspended"]
    show("disable_owner", before=["ready_for_review", "waiting_for_confirmation"],
         after=owner_states, owner_enabled=False)

    # The remote ticket was already AT_WORK under the same client. It remains
    # operational while the supervisor disables the client and then closes it.
    ready_tid, ready_external = user_pair("Проверка перед отключением клиента", actor=second_user)
    action(ready_tid, "executor", actor=dispatcher, body={"executor_id": engineer_id})
    action(ready_tid, "start-work", actor=worker)
    action(ready_tid, "finish-work", actor=worker)
    client_disabled = http("PATCH", f"/admin/clients/{client}/disable").json()
    assert not client_disabled["enabled"]
    assert not http("GET", f"/admin/users/{second_requester['employee_id']}").json()["enabled"]
    http("POST", "/auth/user/refresh", actor={}, body={"refresh_token": second_login["refresh_token"]}, expected=401)
    ready_suspended, _ = database_statuses((ready_tid, ready_external["ticket_user_id"]))
    assert ready_suspended == ["suspended", "suspended"]
    action(ready_tid, "execute", expected=400)
    remote_pair = (remote_tid, remote_external["ticket_user_id"])
    at_work, _ = database_statuses(remote_pair)
    assert at_work == ["at_work", "in_work"]
    action(remote_tid, "finish-work", actor=remote)
    ready_again, _ = database_statuses(remote_pair)
    assert ready_again == ["ready_for_review", "waiting_for_confirmation"]
    action(remote_tid, "execute")
    closed, _ = database_statuses(remote_pair)
    assert closed == ["executed", "confirmed_by_admin"]
    show("disable_client", client_enabled=False, through_disable=at_work, after_finish=ready_again,
         after_admin_execute=closed, already_ready_suspended=ready_suspended, client_user_enabled=False)

    key = secrets.token_hex(16)
    idempotent_actor = dict(supervisor, **{"Idempotency-Key": key})
    payload = {"name": "Повторяемое создание", "enabled": False}
    first = http("POST", "/admin/departments/", actor=idempotent_actor, body=payload, expected=201)
    replay = http("POST", "/admin/departments/", actor=idempotent_actor, body=payload, expected=201)
    assert first.content == replay.content
    conflict = http("POST", "/admin/departments/", actor=idempotent_actor,
                    body=dict(payload, enabled=True), expected=409)
    listing = http("GET", "/admin/departments/").json()
    assert sum(department["name"] == payload["name"] for department in listing) == 1
    show("idempotency", status_first=201, status_repeat=201, same_response=True,
         status_changed_payload=409, conflict=conflict.json(), distinct_department_count=1)


with TemporaryDirectory(dir=RUN, prefix="example-db-") as temp, pytest.MonkeyPatch.context() as patch:
    fixture = application.__wrapped__(Path(temp), patch)
    try:
        verify(next(fixture))
    finally:
        fixture.close()
