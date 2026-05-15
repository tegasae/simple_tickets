from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.domain.account import Account
from src.domain.ticket_user import TicketUser
from tests.fakes.fake_uow import FakeUnitOfWork
from utils.db.connect import Connection
from src.domain.employee import Admin, User
from src.domain.client import Client
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role


@pytest.fixture
def admin_role():
    return Role(
        role_id=1,
        name="Admin role",
        permissions=frozenset(AdminPermission),
    )


@pytest.fixture
def user_role():
    return Role(
        role_id=1,
        name="User role",
        permissions=frozenset(UserPermission),
    )


@pytest.fixture
def admin_with_all_permissions():
    admin = Admin.create(
        employee_id=1,
        first_name="Root",
        last_name="Admin",
        login="root",
        password="Secret123!",
        job_title="Root admin",
    )
    admin.grant_role(1)
    return admin


@pytest.fixture
def other_admin():
    admin = Admin.create(
        employee_id=2,
        first_name="Other",
        last_name="Admin",
        email="other-admin@test.com",
    )
    admin.grant_role(1)
    return admin


@pytest.fixture
def client():
    return Client.create(
        client_id=1,
        name="Test Client",
    )


@pytest.fixture
def user():
    user = User.create(
        employee_id=1,
        client_id=1,
        first_name="John",
        last_name="Smith",
        email="user@test.com",
        login="user-login",
        password="Secret123!",
    )
    user.grant_role(1)
    return user


@pytest.fixture
def other_user():
    user = User.create(
        employee_id=2,
        client_id=1,
        first_name="Other",
        last_name="User",
        email="other@test.com",
        login="other-user-login",
        password="Secret123!",
    )
    user.grant_role(1)
    return user


@pytest.fixture
def uow(
    admin_with_all_permissions,
    other_admin,
    admin_role,
    user_role,
    client,
    user,
    other_user,
):
    uow = FakeUnitOfWork()

    uow.roles_admin.save(admin_role)
    uow.roles_user.save(user_role)

    uow.admins.save(admin_with_all_permissions)
    uow.admins.save(other_admin)

    uow.clients.save(client)

    uow.users.save(user)
    uow.users.save(other_user)

    return uow

####

@pytest.fixture
def user_ticket(user):
    return TicketUser.create(
        ticket_id=1,
        client_id=user.client_id,
        user_id=user.employee_id,
        contact_user_id=user.employee_id,
        description="User ticket description",
    )

@pytest.fixture
def operation_client_role() -> Role[AdminPermission]:
    return Role(
        role_id=1,
        name="operator",
        permissions=frozenset(AdminPermission),
    )


@pytest.fixture
def role():
    return Role.create(
        role_id=1,
        name="Test Role",
        permissions={
            AdminPermission.CREATE_TICKET,
            AdminPermission.UPDATE_TICKET,
        },
    )





@pytest.fixture
def sqlite_connection(tmp_path: Path):
    db_path = tmp_path / "test.sqlite3"
    conn = Connection.create_connection(str(db_path), engine=sqlite3)
    yield conn
    conn.close()


@pytest.fixture
def sqlite_schema(sqlite_connection):
    # Minimal schema matching the repository gateways used in tests.
    sql = """
    CREATE TABLE employees (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        phone TEXT,
        date_created TEXT,
        enabled INTEGER DEFAULT 1,
        version INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0
    );

    CREATE TABLE admins (
        employee_id INTEGER PRIMARY KEY,
        job_title TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
    );

    CREATE TABLE users (
        employee_id INTEGER PRIMARY KEY,
        client_id INTEGER NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
        FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE RESTRICT
    );

    CREATE TABLE clients (
        client_id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        name TEXT,
        address TEXT,
        email TEXT,
        phone TEXT,
        enabled INTEGER DEFAULT 1,
        version INTEGER DEFAULT 0,
        date_created TEXT
    );

    CREATE TABLE accounts (
        account_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER UNIQUE,
        login TEXT UNIQUE,
        password TEXT,
        enabled INTEGER DEFAULT 1,
        date_created TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
    );

    CREATE TABLE roles (
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        permissions TEXT,
        description TEXT,
        is_system_role INTEGER DEFAULT 0,
        date_created TEXT,
        is_admin INTEGER DEFAULT 1,
        version INTEGER DEFAULT 0
    );

    CREATE TABLE admins_roles (
        employee_id INTEGER,
        role_id INTEGER,
        PRIMARY KEY (employee_id, role_id)
    );

    CREATE TABLE users_roles (
        employee_id INTEGER,
        role_id INTEGER,
        PRIMARY KEY (employee_id, role_id)
    );

    CREATE TABLE user_tickets (
	user_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER, -- заявки от какого клиента
	user_id INTEGER, -- кто создал заявку
	user_ticket_contact_user_id INTEGER DEFAULT NULL, -- контактное лицо по заявке, может не быть
	text_of_ticket TEXT, -- текст заявки 
	date_created TEXT,
	version INTEGER, 
	date_closed TEXT, -- дата завершения или снятия заявки 
	is_closed INTEGER
);

    CREATE TABLE user_tickets_status_record (
	user_ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	user_ticket_id INTEGER,
	status TEXT,
	date_created TEXT
	
);

    CREATE TABLE user_tickets_comment (
	user_comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_ticket_id INTEGER,
	employee_id INTEGER,
	comment TEXT,
	date_created TEXT,
	CONSTRAINT comment_tickets_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);

    CREATE TABLE tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        admin_id INTEGER NOT NULL,
        user_id INTEGER,
        user_ticket_contact_user_id INTEGER,
        user_ticket_id INTEGER,
        text_of_ticket TEXT,
        date_created TEXT,
        is_remote INTEGER DEFAULT 0,
        is_closed INTEGER DEFAULT 0,
        date_closed TEXT,
        urgency_level INTEGER DEFAULT 0,
        version INTEGER DEFAULT 0
    );

    CREATE TABLE tickets_comment (
        comment_ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        admin_id INTEGER NOT NULL,
        comment TEXT,
        date_created TEXT
    );

    CREATE TABLE tickets_executor_assignment (
	executor_assignment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER, 
	ticket_id INTEGER,
	date_assignment TEXT  
    );

    CREATE TABLE tickets_status_record (
	ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	ticket_id INTEGER,
	admin_id INTEGER, -- кто установил статус
	status TEXT,
	date_created TEXT
	
);
    """
    sqlite_connection.connect.executescript(sql)
    sqlite_connection.connect.commit()
    return sqlite_connection
