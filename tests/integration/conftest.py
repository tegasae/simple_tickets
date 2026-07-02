from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from utils.db.connect import Connection


TICKET_COMMAND_SCHEMA_SQL = """
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 0,
    date_created TEXT NOT NULL
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    date_created TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 0,
    is_admin INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE admins (
    employee_id INTEGER PRIMARY KEY,
    job_title TEXT,
    department_id INTEGER NULL,

    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON DELETE RESTRICT
);

CREATE TABLE clients (
    client_id INTEGER PRIMARY KEY,
    admin_id INTEGER NULL,
    name TEXT NOT NULL,
    address TEXT,
    email TEXT,
    phone TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 0,
    date_created TEXT NOT NULL,

    FOREIGN KEY (admin_id)
        REFERENCES admins(employee_id)
        ON DELETE RESTRICT
);

CREATE TABLE users (
    employee_id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,

    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (client_id)
        REFERENCES clients(client_id)
        ON DELETE RESTRICT
);

CREATE TABLE user_tickets (
    user_ticket_id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_ticket_contact_user_id INTEGER NULL,
    text_of_ticket TEXT NOT NULL,
    date_created TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 0,
    date_closed TEXT NULL,
    is_closed INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (client_id)
        REFERENCES clients(client_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (user_id)
        REFERENCES users(employee_id)
        ON DELETE RESTRICT
);

CREATE TABLE tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,

    client_id INTEGER NOT NULL,
    admin_id INTEGER NOT NULL,

    user_id INTEGER NULL,
    contact_user_id INTEGER NULL,
    user_ticket_id INTEGER NULL,

    department_id INTEGER NULL,

    text_of_ticket TEXT NOT NULL,
    description TEXT NULL,

    date_created TEXT NOT NULL,

    is_remote INTEGER NOT NULL DEFAULT 0,
    urgency_level INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (client_id)
        REFERENCES clients(client_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (admin_id)
        REFERENCES admins(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (user_id)
        REFERENCES users(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (contact_user_id)
        REFERENCES users(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (user_ticket_id)
        REFERENCES user_tickets(user_ticket_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON DELETE RESTRICT
);

CREATE TABLE ticket_status_records (
    status_id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticket_id INTEGER NOT NULL,

    actor_employee_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    date_created TEXT NOT NULL,

    executor_id INTEGER NULL,

    planned_start_at TEXT NULL,
    planned_finish_at TEXT NULL,

    actual_started_at TEXT NULL,
    actual_finished_at TEXT NULL,

    comment TEXT NOT NULL DEFAULT '',

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
        ON DELETE CASCADE,

    FOREIGN KEY (actor_employee_id)
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (executor_id)
        REFERENCES admins(employee_id)
        ON DELETE RESTRICT
);

CREATE TABLE ticket_comments (
    ticket_comment_id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticket_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,

    comment TEXT NOT NULL,
    date_created TEXT NOT NULL,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
        ON DELETE CASCADE,

    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_ticket_status_records_ticket_id
    ON ticket_status_records(ticket_id, status_id);

CREATE INDEX idx_ticket_comments_ticket_id
    ON ticket_comments(ticket_id, ticket_comment_id);
"""


TICKET_COMMAND_SEED_SQL = """
INSERT INTO departments (
    department_id,
    name,
    enabled,
    version,
    date_created
)
VALUES
    (1, 'Support', 1, 0, '2026-01-01T00:00:00+00:00'),
    (2, 'Infrastructure', 1, 0, '2026-01-01T00:00:00+00:00'),
    (3, 'Disabled department', 0, 0, '2026-01-01T00:00:00+00:00');

INSERT INTO employees (
    employee_id,
    first_name,
    last_name,
    email,
    phone,
    date_created,
    enabled,
    version,
    is_admin
)
VALUES (
    10,
    'Alice',
    'Manager',
    'alice@example.com',
    '+10000000000',
    '2026-01-01T00:00:00+00:00',
    1,
    0,
    1
);

INSERT INTO admins (
    employee_id,
    job_title,
    department_id
)
VALUES (
    10,
    'Manager',
    1
);

INSERT INTO clients (
    client_id,
    admin_id,
    name,
    address,
    email,
    phone,
    enabled,
    version,
    date_created
)
VALUES (
    100,
    10,
    'Acme',
    'Main street',
    'acme@example.com',
    '+10000000001',
    1,
    0,
    '2026-01-01T00:00:00+00:00'
);
"""


@pytest.fixture
def ticket_command_connection(
    tmp_path: Path,
) -> Connection:
    db_path = tmp_path / "ticket-command.sqlite3"

    connection = Connection.create_connection(
        str(db_path),
        engine=sqlite3,
    )

    connection.connect.executescript(
        TICKET_COMMAND_SCHEMA_SQL,
    )
    connection.connect.executescript(
        TICKET_COMMAND_SEED_SQL,
    )
    connection.connect.commit()

    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def ticket_command_uow(
    ticket_command_connection: Connection,
) -> SQLiteUnitOfWork:
    return SQLiteUnitOfWork(
        connection=ticket_command_connection,
    )