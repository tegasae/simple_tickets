import os
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role
from utils.db.connect import Connection


os.environ["SECRET_KEY"] = secrets.token_hex(32)


@contextmanager
def database_uow(path):
    connection = Connection.create_connection(str(path), engine=sqlite3)
    try:
        with SQLiteUnitOfWork(connection) as uow:
            yield uow
    finally:
        connection.close()


@dataclass
class World:
    path: Path
    client: object
    admin_id: int
    user_id: int
    contact_id: int
    client_id: int
    department_id: int
    admin_headers: dict = field(repr=False)
    user_headers: dict = field(repr=False)
    user_login: str = field(repr=False)
    password: str = field(repr=False)
    refresh: str = field(repr=False)

    def create_user_ticket(self, **fields):
        response = self.client.post("/user/tickets/", headers=self.user_headers, json={
            "text_of_ticket": "Synthetic request", **fields,
        })
        assert response.status_code == 201, response.text
        return response.json()

    def admin_action(self, ticket_id, action, body=None):
        response = self.client.patch(
            f"/admin/tickets/{ticket_id}/{action}",
            headers=self.admin_headers, json=body or {},
        )
        assert response.status_code == 200, response.text
        return response.json()

    def work_pair(self, finish=False):
        external = self.create_user_ticket()
        with database_uow(self.path) as uow:
            internal_id = uow.tickets.get_by_user_ticket_id(external["ticket_user_id"]).ticket_id
        self.admin_action(internal_id, "accept")
        self.admin_action(internal_id, "department", {"department_id": self.department_id})
        self.admin_action(internal_id, "executor", {"executor_id": self.admin_id})
        self.admin_action(internal_id, "start-work")
        if finish:
            self.admin_action(internal_id, "finish-work")
        return internal_id, external["ticket_user_id"]


@pytest.fixture
def world(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from src.web.main import create_app

    path = tmp_path / "synthetic.sqlite3"
    with sqlite3.connect(path) as db:
        db.executescript(Path("db/schema.sql").read_text())
    password = "Aa1!" + secrets.token_hex(12)
    admin_login, user_login = "operator" + secrets.token_hex(6), "owner" + secrets.token_hex(6)
    with database_uow(path) as uow:
        department = uow.departments.save(Department.create(name="Synthetic support"))
        admin = uow.admins.save(Admin.create(
            first_name="Operator", login=admin_login, password=password,
            department_id=department.department_id,
        ))
        client = uow.clients.save(Client.create(
            name="Synthetic organization", created_by_admin_id=admin.employee_id,
        ))
        user = uow.users.save(User.create(
            first_name="Owner", client_id=client.client_id, login=user_login, password=password,
        ))
        contact = uow.users.save(User.create(first_name="Contact", client_id=client.client_id))
        admin_role = uow.roles_admin.save(Role.create(name="Synthetic operators", permissions=set(AdminPermission)))
        user_role = uow.roles_user.save(Role.create(name="Synthetic requesters", permissions=set(UserPermission)))
        uow.connection.connect.execute(
            "INSERT INTO admins_roles VALUES (?, ?)", (admin.employee_id, admin_role.role_id),
        )
        uow.connection.connect.execute(
            "INSERT INTO users_roles VALUES (?, ?)", (user.employee_id, user_role.role_id),
        )
    monkeypatch.setenv("DATABASE_URL", str(path))
    monkeypatch.setenv("REFRESH_TOKEN_BACKEND", "memory")
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client_api:
        admin_auth = client_api.post("/auth/admin/login", data={
            "username": admin_login, "password": password,
        })
        user_auth = client_api.post("/auth/user/login", data={
            "username": user_login, "password": password,
        })
        assert admin_auth.status_code == user_auth.status_code == 200
        yield World(
            path, client_api, admin.employee_id, user.employee_id, contact.employee_id,
            client.client_id, department.department_id,
            {"Authorization": "Bearer " + admin_auth.json()["access_token"]},
            {"Authorization": "Bearer " + user_auth.json()["access_token"]},
            user_login, password, user_auth.json()["refresh_token"],
        )
