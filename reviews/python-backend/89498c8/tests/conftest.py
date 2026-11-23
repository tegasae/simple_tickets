import os
import secrets
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role
from utils.db.connect import Connection


# create_app() is evaluated when the ASGI module is imported.
os.environ["SECRET_KEY"] = secrets.token_hex(32)


@dataclass(frozen=True)
class Sample:
    path: Path
    client_id: int
    admin_id: int
    user_id: int
    contact_id: int
    department_id: int
    user_login: str = field(repr=False)
    user_password: str = field(repr=False)


@pytest.fixture
def sample(tmp_path):
    path = tmp_path / "synthetic.sqlite3"
    schema = Path("db/schema.sql").read_text()
    with sqlite3.connect(path) as db:
        db.executescript(schema.replace("CREATE TABLE sqlite_sequence(name,seq);", ""))

    conn = Connection.create_connection(str(path), engine=sqlite3)
    # Values are generated for this fixture and discarded along with the database.
    user_login = "fixture" + secrets.token_hex(8)
    user_password = "Aa1!" + secrets.token_hex(16)
    try:
        with SQLiteUnitOfWork(conn) as uow:
            department = uow.departments.save(Department.create(name="Support"))
            admin = uow.admins.save(
                Admin.create(first_name="Operator", department_id=department.department_id)
            )
            client = uow.clients.save(
                Client.create(name="Synthetic Client", created_by_admin_id=admin.employee_id)
            )
            user = uow.users.save(
                User.create(first_name="Owner", client_id=client.client_id,
                            login=user_login, password=user_password)
            )
            contact = uow.users.save(User.create(first_name="Contact", client_id=client.client_id))
            admin_role = uow.roles_admin.save(Role.create(
                name="Operators",
                permissions={
                    AdminPermission.TICKET_CREATED,
                    AdminPermission.TICKET_OPERATION,
                    AdminPermission.TICKET_CANCELLED,
                    AdminPermission.TICKET_VIEW,
                    AdminPermission.TICKET_ACCEPTED,
                    AdminPermission.TICKET_AT_WORK,
                    AdminPermission.TICKET_AT_WORK_REMOTE,
                    AdminPermission.TICKET_AT_WORK_RETROSPECTIVE,
                    AdminPermission.CLIENT_DECISION,
                    AdminPermission.USER_OPERATION,
                },
            ))
            user_role = uow.roles_user.save(Role.create(
                name="Requesters",
                permissions={UserPermission.TICKET_OPERATION, UserPermission.TICKET_VIEW},
            ))
            conn.connect.execute(
                "INSERT INTO admins_roles VALUES (?, ?)", (admin.employee_id, admin_role.role_id)
            )
            conn.connect.execute(
                "INSERT INTO users_roles VALUES (?, ?)", (user.employee_id, user_role.role_id)
            )
    finally:
        conn.close()
    return Sample(path, client.client_id, admin.employee_id, user.employee_id,
                  contact.employee_id, department.department_id, user_login, user_password)


@pytest.fixture
def uow(sample):
    conn = Connection.create_connection(str(sample.path), engine=sqlite3)
    try:
        yield SQLiteUnitOfWork(conn)
    finally:
        conn.close()


@pytest.fixture
def web(sample):
    from src.web.dependencies.auth import get_current_admin, get_current_user
    from src.web.main import create_app

    app = create_app()
    app.state.settings.DATABASE_URL = str(sample.path)
    app.dependency_overrides[get_current_admin] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: None
    from src.web.dependencies.auth import get_employee_id_from_request
    from fastapi import Request

    def actor_id(request: Request):
        return sample.admin_id if request.url.path.startswith("/admin/") else sample.user_id

    app.dependency_overrides[get_employee_id_from_request] = actor_id
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
