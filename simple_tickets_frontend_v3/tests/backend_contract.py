"""I1 through I3 checks against FastAPI and a disposable SQLite database.

From frontend v3, run `python -B tests/backend_contract.py`.
Use `--serve` for the I1/I2 fixture or `--serve-i3` for extra workflow cases.
The loopback fixture writes temporary login details to its private fixture directory.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest
from unittest.mock import patch


FRONTEND = Path(__file__).resolve().parents[1]
REPO = FRONTEND.parent
SCHEMA = REPO / "db" / "schema.sql"


@dataclass(frozen=True)
class References:
    client: int
    other_client: int
    requester: int
    contact: int
    other_contact: int
    department: int
    archived_department: int


@dataclass(frozen=True)
class Fixture:
    app: object
    directory: Path
    accounts: dict = field(repr=False)
    ticket_ids: tuple[int, ...]
    references: References
    workflow: dict | None


def seed_profiles(uow, profiles, accounts, actor_ids):
    from src.domain.employee import Admin
    from src.domain.rbac.role_new import Role

    for profile, (name, permissions, department_id) in profiles.items():
        role = uow.roles_admin.save(Role.create(name=name, permissions=permissions))
        login = {"username": "qa" + secrets.token_hex(6), "password": "Aa1!" + secrets.token_hex(12)}
        actor = Admin.create(
            first_name=name, login=login["username"], password=login["password"], department_id=department_id,
        )
        actor.grant_role(role.role_id)
        actor_ids[profile] = uow.admins.save(actor).employee_id
        accounts[profile] = login


def seed_workflow(uow, references, accounts, actor_ids):
    from src.domain.department import Department
    from src.domain.employee import Admin
    from src.domain.rbac.permissions import AdminPermission as Permission
    from src.domain.ticket import Ticket

    department = references.department
    other_department = uow.departments.save(Department.create(name="Внешний тестовый отдел")).department_id
    view = Permission.TICKET_VIEW
    work = Permission.TICKET_AT_WORK
    remote = Permission.TICKET_AT_WORK_REMOTE
    seed_profiles(uow, {
        "dispatcher": ("Диспетчер И3", {
            view, Permission.TICKET_ACCEPTED, Permission.TICKET_CANCELLED, Permission.TICKET_OPERATION,
            Permission.TICKET_ASSIGN_EXECUTOR, Permission.ADMIN_VIEW,
        }, department),
        "worker": ("Исполнитель И3", {view, work}, department),
        "peer_worker": ("Сменщик И3", {view, work}, department),
        "hotline": ("Оператор Линии", {view, remote}, department),
        "peer_hotline": ("Сменщик Линии", {view, remote}, department),
        "outside_hotline": ("Внешний Оператор", {view, remote}, other_department),
        "reviewer": ("Проверяющий И3", {view, Permission.TICKET_EXECUTED}, department),
        "recorder": ("Регистратор Работ", {view, Permission.TICKET_AT_WORK_RETROSPECTIVE}, department),
    }, accounts, actor_ids)
    disabled = Admin.create(first_name="Отключённый Исполнитель", enabled=False, enable_account=False,
                            department_id=department)
    actor_ids["disabled_worker"] = uow.admins.save(disabled).employee_id

    scenarios = {
        "lifecycle": ("И3 Жизненный цикл", False, False, None),
        "reject": ("И3 Отклонение", False, False, None),
        "defer": ("И3 Отложенная заявка", True, False, None),
        "hotline": ("И3 Горячая линия", True, True, None),
        "hotline_race": ("И3 Два оператора", True, True, None),
        "hotline_assigned": ("И3 Назначенная заявка линии", True, True, "hotline"),
        "not_recommended": ("И3 Без рекомендации", True, False, None),
        "retrospective": ("И3 Учёт длительности", True, False, "worker"),
        "retrospective_interval": ("И3 Учёт интервала", True, False, "worker"),
        "unknown_unchanged": ("И3 Неопределённый перенос", True, False, None),
    }
    tickets = {}
    dispatcher = actor_ids["dispatcher"]
    for scenario, (title, accepted, recommended, executor) in scenarios.items():
        ticket = Ticket.create(
            client_id=references.client,
            admin_id=dispatcher,
            text_of_ticket=title,
            department_id=department,
            remote_work_recommended=recommended,
        )
        if accepted:
            ticket.accept(actor_employee_id=dispatcher)
        if executor:
            ticket.assign(actor_employee_id=dispatcher, executor_id=actor_ids[executor])
        tickets[scenario] = {"id": uow.tickets.save(ticket).ticket_id, "title": title}
    return {"actors": actor_ids, "tickets": tickets}


def seed_database(database, *, workflow=False):
    from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
    from src.domain.client import Client
    from src.domain.department import Department
    from src.domain.employee import User
    from src.domain.rbac.permissions import AdminPermission
    from src.domain.ticket import Ticket
    from src.domain.ticket_user import TicketUser
    from utils.db.connect import Connection

    with closing(sqlite3.connect(database)) as connection:
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))

    accounts = {}
    with closing(Connection.create_connection(str(database), engine=sqlite3)) as connection:
        with SQLiteUnitOfWork(connection) as uow:
            profiles = {
                "reader": ("Тестовый Оператор", {AdminPermission.TICKET_VIEW}, 0),
                "restricted": ("Тестовый Автор", {AdminPermission.TICKET_CREATED}, 0),
                "creator": ("Тестовый Регистратор", {AdminPermission.TICKET_CREATED, AdminPermission.CLIENT_VIEW}, 0),
                "writer": ("Тестовый Диспетчер", {
                    AdminPermission.TICKET_VIEW,
                    AdminPermission.TICKET_OPERATION,
                    AdminPermission.CLIENT_VIEW,
                    AdminPermission.USER_VIEW,
                    AdminPermission.DEPARTMENT_VIEW,
                }, 0),
                "recommender": ("Тестовый Рекомендатель", {
                    AdminPermission.TICKET_VIEW,
                    AdminPermission.TICKET_SET_REMOTE_RECOMMENDATION,
                }, 0),
            }
            actor_ids = {}
            seed_profiles(uow, profiles, accounts, actor_ids)

            reader_id = actor_ids["reader"]
            client = uow.clients.save(Client.create(name="Тестовый клиент", created_by_admin_id=reader_id))
            other_client = uow.clients.save(Client.create(name="Резервный клиент", created_by_admin_id=reader_id))
            requester = uow.users.save(User.create(first_name="Анна", last_name="Заявитель", client_id=client.client_id))
            contact = uow.users.save(User.create(first_name="Борис", last_name="Контакт", client_id=client.client_id))
            other_contact = uow.users.save(User.create(first_name="Галина", last_name="Контакт", client_id=other_client.client_id))
            department = uow.departments.save(Department.create(name="Тестовый отдел"))
            archived = uow.departments.save(Department.create(name="Архивный отдел", enabled=False))
            references = References(
                client.client_id, other_client.client_id, requester.employee_id, contact.employee_id,
                other_contact.employee_id, department.department_id, archived.department_id,
            )
            ticket_ids = []
            samples = (
                ("Проверка печати", "accepted"),
                ("Очередь поддержки", "created"),
                ("Проверка архива", "rejected"),
            )
            for subject, status in samples:
                ticket_fields = {
                    "client_id": references.client,
                    "admin_id": reader_id,
                    "text_of_ticket": subject,
                    "description": "Синтетическая заявка для тестового стенда",
                    "comment": "Синтетический комментарий",
                }
                if status == "created":
                    request = uow.user_tickets.save(TicketUser.create(
                        client_id=references.client,
                        user_id=references.requester,
                        contact_user_id=references.contact,
                        text_of_ticket=subject,
                    ))
                    ticket = Ticket.create_from_request_user(
                        **ticket_fields,
                        user_id=references.requester,
                        user_ticket_id=request.ticket_user_id,
                        contact_user_id=references.contact,
                        department_id=references.department,
                    )
                else:
                    ticket = Ticket.create(**ticket_fields)
                if status == "accepted":
                    ticket.accept(actor_employee_id=reader_id)
                if status == "rejected":
                    ticket.reject(actor_employee_id=reader_id, comment="Синтетическая причина")
                ticket_ids.append(uow.tickets.save(ticket).ticket_id)
            workflow_data = seed_workflow(uow, references, accounts, actor_ids) if workflow else None

    return accounts, tuple(ticket_ids), references, workflow_data


@contextmanager
def isolated_application(*, workflow=False):
    # Change cwd before importing Settings so the checkout's .env is never read.
    with TemporaryDirectory(prefix=".qa-contract-", dir=FRONTEND) as temporary:
        directory = Path(temporary)
        database = directory / "test.sqlite3"
        accounts, ticket_ids, references, workflow_data = seed_database(database, workflow=workflow)
        previous_directory = Path.cwd()
        with patch.dict(os.environ, {"DATABASE_URL": str(database), "SECRET_KEY": secrets.token_hex(32)}):
            try:
                os.chdir(directory)
                from src.web.main import create_app

                application = create_app()
                if application.state.settings.DATABASE_URL != str(database):
                    raise RuntimeError("FastAPI did not select the disposable database")
                yield Fixture(application, directory, accounts, ticket_ids, references, workflow_data)
            finally:
                os.chdir(previous_directory)


class ContractCase(unittest.TestCase):
    def login(self, profile):
        response = self.api.post("/auth/admin/login", data=self.fixture.accounts[profile])
        self.assertEqual(response.status_code, 200, "Admin form login failed")
        tokens = response.json()
        self.assertEqual(tokens["token_type"], "bearer")
        self.assertGreater(tokens["expires_in"], 0)
        self.assertTrue(all(isinstance(tokens.get(key), str) and tokens[key] for key in ("access_token", "refresh_token")))
        return tokens

    @staticmethod
    def bearer(tokens):
        return {"Authorization": "Bearer " + tokens["access_token"]}


class BackendContract(ContractCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        cls.fixture = cls.enterClassContext(isolated_application())
        cls.api = cls.enterClassContext(TestClient(cls.fixture.app, raise_server_exceptions=False))
    def test_health_and_form_login_contract(self):
        self.assertEqual(self.api.get("/health").json(), {"status": "ok"})
        wrong_content_type = self.api.post("/auth/admin/login", json=self.fixture.accounts["reader"])
        self.assertEqual(wrong_content_type.status_code, 422)
        self.login("reader")

    def test_refresh_rotation_and_logout_revocation(self):
        tokens = self.login("reader")
        old_refresh = {"refresh_token": tokens["refresh_token"]}
        refreshed = self.api.post("/auth/admin/refresh", json=old_refresh)
        self.assertEqual(refreshed.status_code, 200)
        new_tokens = refreshed.json()
        new_refresh = {"refresh_token": new_tokens["refresh_token"]}
        self.assertTrue(new_refresh != old_refresh, "Refresh did not rotate")
        self.assertEqual(self.api.post("/auth/admin/refresh", json=old_refresh).status_code, 401)
        self.assertEqual(self.api.get("/admin/admins/permissions", headers=self.bearer(new_tokens)).status_code, 200)
        self.assertEqual(self.api.post("/auth/admin/logout", json=new_refresh).status_code, 200)
        self.assertEqual(self.api.post("/auth/admin/refresh", json=new_refresh).status_code, 401)

    def test_permissions_and_read_denial(self):
        ticket_id = self.fixture.ticket_ids[0]
        reader = self.bearer(self.login("reader"))
        restricted = self.bearer(self.login("restricted"))
        for headers, expected in ((reader, "ticket.view"), (restricted, "ticket.created")):
            response = self.api.get("/admin/admins/permissions", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"permissions": [expected]})
        for path in ("/admin/tickets/", "/admin/tickets/open", "/admin/tickets/closed", f"/admin/tickets/{ticket_id}"):
            self.assertEqual(self.api.get(path).status_code, 401, path)
            self.assertEqual(self.api.get(path, headers=restricted).status_code, 403, path)

    def test_ticket_read_history_order_and_missing_detail(self):
        headers = self.bearer(self.login("reader"))
        ticket_ids = self.fixture.ticket_ids
        self.assertEqual(ticket_ids, tuple(sorted(ticket_ids)))
        for path, expected in (
            ("/admin/tickets/", ticket_ids),
            ("/admin/tickets/open", ticket_ids[:2]),
            ("/admin/tickets/closed", ticket_ids[2:]),
        ):
            response = self.api.get(path, headers=headers)
            self.assertEqual(response.status_code, 200, path)
            self.assertEqual(tuple(ticket["ticket_id"] for ticket in response.json()), expected)

        detail = self.api.get(f"/admin/tickets/{ticket_ids[0]}", headers=headers)
        self.assertEqual(detail.status_code, 200)
        ticket = detail.json()
        self.assertEqual(ticket["ticket_id"], ticket_ids[0])
        self.assertNotIn("current_status", ticket)
        self.assertNotIn("version", ticket)
        self.assertEqual([record["status"] for record in ticket["statuses"]], ["created", "accepted"])
        timestamps = [datetime.fromisoformat(record["date_created"]) for record in ticket["statuses"]]
        self.assertTrue(all(value.utcoffset() is not None for value in timestamps))
        self.assertEqual(timestamps, sorted(timestamps))
        self.assertEqual([record["comment"] for record in ticket["comments"]], ["Синтетический комментарий"])
        self.assertEqual(self.api.get(f"/admin/tickets/{max(ticket_ids) + 1}", headers=headers).status_code, 404)


class BackendWriteContract(ContractCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        self.fixture = self.enterContext(isolated_application())
        self.api = self.enterContext(TestClient(self.fixture.app, raise_server_exceptions=False))

    def test_reader_cannot_create_edit_or_add_comments(self):
        headers = self.bearer(self.login("reader"))
        ticket = f"/admin/tickets/{self.fixture.ticket_ids[0]}"
        create = self.api.post("/admin/tickets/", headers=headers, json={
            "client_id": self.fixture.references.client, "text_of_ticket": "Недоступная новая заявка",
        })
        self.assertEqual(create.status_code, 403)
        edit = self.api.patch(f"{ticket}/description", headers=headers, json={"description": "Недоступное изменение"})
        self.assertEqual(edit.status_code, 403)
        comment = self.api.post(f"{ticket}/comments", headers=headers, json={"comment": "Недоступный комментарий"})
        self.assertEqual(comment.status_code, 403)

    def test_author_without_view_can_create_and_safely_repeat_creation(self):
        creator = self.bearer(self.login("creator"))
        reader = self.bearer(self.login("reader"))
        permissions = self.api.get("/admin/admins/permissions", headers=creator)
        self.assertEqual(permissions.status_code, 200)
        self.assertEqual(set(permissions.json()["permissions"]), {"ticket.created", "client.view"})
        self.assertEqual(self.api.get("/admin/clients/", headers=creator).status_code, 200)
        self.assertEqual(self.api.get("/admin/tickets/", headers=creator).status_code, 403)

        body = {"client_id": self.fixture.references.client, "text_of_ticket": "Синтетическая новая заявка"}
        headers = {**creator, "Idempotency-Key": secrets.token_hex(16)}
        created = self.api.post("/admin/tickets/", json=body, headers=headers)
        self.assertEqual(created.status_code, 201)
        ticket = created.json()
        self.assertEqual(ticket["statuses"][-1]["status"], "created")
        repeated = self.api.post("/admin/tickets/", json=body, headers=headers)
        self.assertEqual(repeated.status_code, 201)
        self.assertEqual(repeated.json(), ticket)
        conflict = self.api.post("/admin/tickets/", json={**body, "text_of_ticket": "Другая заявка"}, headers=headers)
        self.assertEqual(conflict.status_code, 409)
        path = f"/admin/tickets/{ticket['ticket_id']}"
        self.assertEqual(self.api.get(path, headers=creator).status_code, 403)
        all_tickets = self.api.get("/admin/tickets/", headers=reader)
        self.assertEqual(all_tickets.status_code, 200)
        self.assertEqual([item["ticket_id"] for item in all_tickets.json()], [*self.fixture.ticket_ids, ticket["ticket_id"]])

    def test_scoped_catalogs_and_linked_ticket(self):
        headers = self.bearer(self.login("writer"))
        refs = self.fixture.references
        ticket = self.api.get(f"/admin/tickets/{self.fixture.ticket_ids[1]}", headers=headers)
        self.assertEqual(ticket.status_code, 200)
        self.assertEqual((ticket.json()["client_id"], ticket.json()["user_id"], ticket.json()["contact_user_id"]),
                         (refs.client, refs.requester, refs.contact))
        client = self.api.get(f"/admin/clients/{refs.client}", headers=headers)
        self.assertEqual(client.status_code, 200)
        self.assertEqual(client.json()["name"], "Тестовый клиент")
        contact = self.api.get(f"/admin/users/{refs.contact}", headers=headers)
        self.assertEqual(contact.status_code, 200)
        self.assertEqual(contact.json()["client_id"], refs.client)
        for client_id, expected in ((refs.client, {refs.requester, refs.contact}), (refs.other_client, {refs.other_contact})):
            response = self.api.get(f"/admin/users/client/{client_id}", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual({user["employee_id"] for user in response.json()}, expected)
        departments = self.api.get("/admin/departments/", headers=headers)
        self.assertEqual(departments.status_code, 200)
        self.assertEqual({row["department_id"]: row["enabled"] for row in departments.json()},
                         {refs.department: True, refs.archived_department: False})

    def test_edits_and_schedule_follow_field_contracts(self):
        headers = self.bearer(self.login("writer"))
        refs = self.fixture.references
        ticket = f"/admin/tickets/{self.fixture.ticket_ids[0]}"
        for endpoint, field, value in (
            ("description", "description", "Изменённое синтетическое описание"),
            ("contact-user", "contact_user_id", refs.contact),
            ("department", "department_id", refs.department),
            ("urgency", "urgency", "urgent"),
        ):
            response = self.api.patch(f"{ticket}/{endpoint}", headers=headers, json={field: value})
            self.assertEqual(response.status_code, 200, endpoint)
            self.assertEqual(response.json()[field], value)
        wrong_client = self.api.patch(f"{ticket}/contact-user", headers=headers, json={"contact_user_id": refs.other_contact})
        self.assertEqual(wrong_client.status_code, 400)
        archived = self.api.patch(f"{ticket}/department", headers=headers, json={"department_id": refs.archived_department})
        self.assertEqual(archived.status_code, 400)
        for endpoint, field in (("contact-user", "contact_user_id"), ("department", "department_id")):
            cleared = self.api.patch(f"{ticket}/{endpoint}", headers=headers, json={field: 0})
            self.assertEqual(cleared.status_code, 200)
            self.assertEqual(cleared.json()[field], 0)

        planned = (datetime.now(timezone(timedelta(hours=3))) + timedelta(days=2)).replace(microsecond=0)
        invalid = self.api.patch(f"{ticket}/schedule", headers=headers, json={"planned_at": planned.replace(tzinfo=None).isoformat()})
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(invalid.json()["detail"][0]["loc"], ["body", "planned_at"])
        scheduled = self.api.patch(f"{ticket}/schedule", headers=headers, json={"planned_at": planned.isoformat()})
        self.assertEqual(scheduled.status_code, 200)
        self.assertEqual(datetime.fromisoformat(scheduled.json()["planned_at"]), planned)
        unscheduled = self.api.delete(f"{ticket}/schedule", headers=headers)
        self.assertEqual(unscheduled.status_code, 200)
        self.assertIsNone(unscheduled.json()["planned_at"])
        saved = self.api.get(ticket, headers=headers)
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["urgency"], "urgent")
        self.assertIsNone(saved.json()["planned_at"])

    def test_remote_recommendation_requires_its_own_permission(self):
        ordinary = self.bearer(self.login("writer"))
        allowed = self.bearer(self.login("recommender"))
        ticket = f"/admin/tickets/{self.fixture.ticket_ids[0]}"
        body = {"remote_work_recommended": True}
        create = self.api.post("/admin/tickets/", headers=ordinary, json={
            **body, "client_id": self.fixture.references.client, "text_of_ticket": "Новая заявка с рекомендацией",
        })
        self.assertEqual(create.status_code, 403)
        self.assertEqual(self.api.patch(f"{ticket}/remote-work-recommended", headers=ordinary, json=body).status_code, 403)
        changed = self.api.patch(f"{ticket}/remote-work-recommended", headers=allowed, json=body)
        self.assertEqual(changed.status_code, 200)
        self.assertIs(changed.json()["remote_work_recommended"], True)
        self.assertEqual(self.api.patch(f"{ticket}/description", headers=allowed, json={"description": "Текст"}).status_code, 403)

    def test_comment_replay_is_one_write_and_does_not_replace_fresh_data(self):
        writer = self.bearer(self.login("writer"))
        ticket = f"/admin/tickets/{self.fixture.ticket_ids[0]}"
        comments = f"{ticket}/comments"
        invalid = self.api.post(comments, headers=writer, json={"comment": " "})
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(invalid.json()["detail"][0]["loc"], ["body", "comment"])
        closed = f"/admin/tickets/{self.fixture.ticket_ids[-1]}/comments"
        self.assertEqual(self.api.post(closed, headers=writer, json={"comment": "Закрытая заявка"}).status_code, 400)

        headers = {**writer, "Idempotency-Key": secrets.token_hex(16)}
        body = {"comment": "Опубликованный синтетический комментарий"}
        created = self.api.post(comments, headers=headers, json=body)
        self.assertEqual(created.status_code, 200)
        description = "Описание изменено после комментария"
        updated = self.api.patch(f"{ticket}/description", headers=writer, json={"description": description})
        self.assertEqual(updated.status_code, 200)
        replay = self.api.post(comments, headers=headers, json=body)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json(), created.json())
        current = self.api.get(ticket, headers=writer)
        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.json()["description"], description)
        self.assertEqual([row["comment"] for row in current.json()["comments"]].count(body["comment"]), 1)
        self.assertEqual(self.api.post(comments, headers=headers, json={"comment": "Другое намерение"}).status_code, 409)


class BackendWorkflowContract(ContractCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        cls.fixture = cls.enterClassContext(isolated_application(workflow=True))
        cls.api = cls.enterClassContext(TestClient(cls.fixture.app, raise_server_exceptions=False))
        cls.actors = cls.fixture.workflow["actors"]
        cls.tickets = cls.fixture.workflow["tickets"]

    def headers(self, profile):
        return self.bearer(self.login(profile))

    def ticket_path(self, scenario):
        return f"/admin/tickets/{self.tickets[scenario]['id']}"

    def transition(self, path, action, headers, data, status=200):
        result = self.api.patch(f"{path}/{action}", headers=headers, json=data)
        self.assertEqual(result.status_code, status, f"{action}: {result.text}")
        return result.json()

    def read_ticket(self, path, headers):
        result = self.api.get(path, headers=headers)
        self.assertEqual(result.status_code, 200)
        return result.json()

    def assert_timeline(self, ticket, statuses):
        records = ticket["statuses"]
        self.assertEqual([item["status"] for item in records], statuses)
        ids = [item["id"] for item in records]
        self.assertEqual(ids, sorted(set(ids)))

    def assert_persisted(self, path, headers, transition_response):
        # SQLite exposes a default false for new non-work records returned as null by PATCH.
        records = [
            {**record, "work_is_remote": False}
            if record["status"] != "at_work" and record["work_is_remote"] is None
            else record
            for record in transition_response["statuses"]
        ]
        self.assertEqual(self.read_ticket(path, headers), {**transition_response, "statuses": records})

    def test_accept_assign_work_and_administrative_review(self):
        path = self.ticket_path("lifecycle")
        dispatcher = self.headers("dispatcher")
        worker = self.headers("worker")
        peer = self.headers("peer_worker")
        reviewer = self.headers("reviewer")
        self.transition(path, "accept", worker, {}, status=403)
        self.transition(path, "execute", reviewer, {}, status=400)
        accepted = self.transition(path, "accept", dispatcher, {})
        self.assert_timeline(accepted, ["created", "accepted"])
        for profile, expected in (("dispatcher", 403), ("outside_hotline", 400), ("disabled_worker", 400)):
            with self.subTest(executor=profile):
                self.transition(path, "executor", dispatcher, {"executor_id": self.actors[profile]}, status=expected)
        worker_id = self.actors["worker"]
        assigned = self.transition(path, "executor", dispatcher, {"executor_id": worker_id})
        self.assertEqual(assigned["current_executor_id"], worker_id)
        self.assertEqual(assigned["statuses"][-1]["actor_id"], self.actors["dispatcher"])
        self.transition(path, "start-work", peer, {}, status=400)
        working = self.transition(path, "start-work", worker, {"work_is_remote": False})
        self.assertIs(working["statuses"][-1]["work_is_remote"], False)
        self.transition(path, "pause-work", worker, {"comment": "Ожидание проверки"})
        self.transition(path, "resume-work", worker, {"work_is_remote": False})
        submitted = self.transition(path, "finish-work", worker, {"comment": "Работа выполнена"})
        timeline = ["created", "accepted", "assigned", "at_work", "paused", "at_work", "ready_for_review"]
        self.assert_timeline(submitted, timeline)
        self.assertFalse(submitted["is_closed"])
        self.transition(path, "execute", worker, {}, status=403)
        self.assert_persisted(path, reviewer, submitted)
        complete = self.transition(path, "execute", reviewer, {})
        self.assert_timeline(complete, [*timeline, "executed"])
        self.assertTrue(complete["is_closed"])
        self.assertEqual(complete["statuses"][-1]["actor_id"], self.actors["reviewer"])
        self.assert_persisted(path, reviewer, complete)

    def test_rejection_and_deferral_require_reasons(self):
        path = self.ticket_path("reject")
        dispatcher = self.headers("dispatcher")
        reader = self.headers("reader")
        self.transition(path, "reject", dispatcher, {}, status=422)
        self.transition(path, "reject", reader, {"comment": "Нет прав"}, status=403)
        self.assert_timeline(self.read_ticket(path, reader), ["created"])
        rejected = self.transition(path, "reject", dispatcher, {"comment": "Синтетическая причина отклонения"})
        self.assert_timeline(rejected, ["created", "rejected"])
        self.assertEqual(rejected["statuses"][-1]["comment"], "Синтетическая причина отклонения")
        path = self.ticket_path("defer")
        self.transition(path, "defer", dispatcher, {"comment": ""}, status=422)
        deferred = self.transition(path, "defer", dispatcher, {"comment": "Синтетическая причина переноса"})
        self.assert_timeline(deferred, ["created", "accepted", "deferred"])
        self.assertEqual(deferred["statuses"][-1]["comment"], "Синтетическая причина переноса")

    def test_hotline_required_body_permissions_and_atomic_start(self):
        path = self.ticket_path("hotline")
        hotline = self.headers("hotline")
        outside = self.headers("outside_hotline")
        reader = self.headers("reader")
        initial = self.read_ticket(path, reader)
        self.assertEqual(self.api.patch(f"{path}/start-remote-work", headers=hotline).status_code, 422)
        self.transition(path, "start-remote-work", hotline, {"work_is_remote": True}, status=422)
        self.transition(path, "start-remote-work", reader, {}, status=403)
        self.transition(path, "start-remote-work", outside, {}, status=400)
        self.transition(path, "executor", hotline, {"executor_id": self.actors["worker"]}, status=403)
        self.assertEqual(self.read_ticket(path, reader), initial)
        unapproved = self.ticket_path("not_recommended")
        self.transition(unapproved, "start-remote-work", hotline, {}, status=400)
        self.assert_timeline(self.read_ticket(unapproved, hotline), ["created", "accepted"])

        started = self.transition(path, "start-remote-work", hotline, {})
        self.assert_hotline_start(started, self.actors["hotline"])
        self.assert_persisted(path, reader, started)
        self.transition(path, "pause-work", self.headers("peer_hotline"), {}, status=400)
        self.transition(path, "pause-work", hotline, {})
        self.transition(path, "resume-work", hotline, {"work_is_remote": False}, status=403)
        self.transition(path, "resume-work", hotline, {"work_is_remote": True})
        submitted = self.transition(path, "finish-work", hotline, {})
        self.assert_timeline(submitted, ["created", "accepted", "assigned", "at_work", "paused", "at_work",
                                         "ready_for_review"])

    def assert_hotline_start(self, ticket, actor):
        self.assert_timeline(ticket, ["created", "accepted", "assigned", "at_work"])
        assigned, working = ticket["statuses"][-2:]
        self.assertEqual(assigned["executor_id"], actor)
        self.assertEqual(assigned["actor_id"], actor)
        self.assertEqual(working["actor_id"], actor)
        self.assertEqual(working["date_created"], assigned["date_created"])
        self.assertIs(working["work_is_remote"], True)
        self.assertEqual(ticket["current_executor_id"], actor)

    def test_hotline_assigned_only_current_actor_and_no_duplicate_assignment(self):
        path = self.ticket_path("hotline_assigned")
        hotline = self.headers("hotline")
        initial = self.read_ticket(path, hotline)
        self.transition(path, "start-remote-work", self.headers("peer_hotline"), {}, status=400)
        started = self.transition(path, "start-remote-work", hotline, {"comment": "Наблюдение И3"})
        self.assert_timeline(started, ["created", "accepted", "assigned", "at_work"])
        self.assertEqual(started["statuses"][:-1], initial["statuses"])
        self.assertEqual(started["statuses"][-1]["comment"], "Наблюдение И3")
        self.assertIs(started["statuses"][-1]["work_is_remote"], True)

    def test_two_hotline_operators_have_one_persisted_winner(self):
        path = self.ticket_path("hotline_race")
        profiles = ("hotline", "peer_hotline")
        headers = {profile: self.headers(profile) for profile in profiles}
        barrier = Barrier(2)

        def start(profile):
            barrier.wait(timeout=10)
            return self.api.patch(f"{path}/start-remote-work", headers=headers[profile], json={})

        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = dict(zip(profiles, pool.map(start, profiles), strict=True))
        winners = [profile for profile, result in responses.items() if result.status_code == 200]
        self.assertEqual(len(winners), 1, {profile: result.status_code for profile, result in responses.items()})
        winner = winners[0]
        loser = next(profile for profile in profiles if profile != winner)
        self.assertIn(responses[loser].status_code, (400, 409, 503))
        actual = self.read_ticket(path, headers[loser])
        self.assert_hotline_start(actual, self.actors[winner])
        self.assert_persisted(path, headers[loser], responses[winner].json())

    def test_retroactive_duration_and_interval_with_separate_permission(self):
        recorder = self.headers("recorder")
        worker = self.headers("worker")
        interval = {"actual_started_at": "2020-01-01T10:00:00Z", "actual_finished_at": "2020-01-01T10:40:00Z"}
        action = "complete-work-retroactively"
        path = self.ticket_path("retrospective")
        self.transition(path, action, worker, {"duration": "PT40M"}, status=403)
        for body in ({}, {**interval, "duration": "PT40M"}, {"actual_started_at": interval["actual_started_at"]}):
            with self.subTest(body=body):
                self.transition(path, action, recorder, body, status=400)
        self.assert_timeline(self.read_ticket(path, recorder), ["created", "accepted", "assigned"])
        for case, body in (("retrospective", {"duration": "PT40M"}), ("retrospective_interval", interval)):
            with self.subTest(case=case):
                result = self.transition(self.ticket_path(case), action, recorder, {**body, "work_is_remote": True})
                self.assert_timeline(result, ["created", "accepted", "assigned", "at_work", "ready_for_review"])
                recorded, submitted = result["statuses"][-2:]
                self.assertEqual(recorded["actor_id"], self.actors["recorder"])
                self.assertEqual(recorded["date_created"], submitted["date_created"])
                self.assertIs(recorded["work_is_remote"], True)
                for key, value in body.items():
                    self.assertEqual(recorded[key], value)


def serve_fixture(*, workflow=False, port=18080):
    import uvicorn

    with isolated_application(workflow=workflow) as fixture:
        credentials = fixture.directory / "credentials.json"
        fd = os.open(credentials, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            data = {**fixture.accounts, "workflow": fixture.workflow} if workflow else fixture.accounts
            json.dump(data, output, ensure_ascii=False)
        print(f"Loopback fixture on 127.0.0.1:{port}; private credentials file: {credentials}", flush=True)
        uvicorn.run(fixture.app, host="127.0.0.1", port=port, access_log=False, log_level="warning")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--serve", action="store_true", help="Run the I1/I2 loopback API fixture")
    mode.add_argument("--serve-i3", action="store_true", help="Run the loopback API fixture with workflow cases")
    parser.add_argument("--port", type=int, default=18080, choices=(18080, 18081),
                        help="Loopback API fixture port")
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(REPO))
    if args.serve or args.serve_i3:
        serve_fixture(workflow=args.serve_i3, port=args.port)
        return 0
    cases = (BackendContract, BackendWriteContract, BackendWorkflowContract)
    tests = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in cases)
    return 0 if unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
