from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.adapters.repositories.exceptions import OptimisticLockError
from src.adapters.repositories.ticket_repository import TicketRepositorySQLite
from src.domain.exceptions import ItemNotFoundError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment
from utils.db.connect import Connection


NOW = datetime.now(timezone.utc)

PLANNED_START = NOW + timedelta(hours=1)
PLANNED_FINISH = NOW + timedelta(hours=2)


SCHEMA_SQL = """
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 0,
    date_created TEXT
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
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
    admin_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (admin_id)
        REFERENCES employees(employee_id)
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
    text_of_ticket TEXT NOT NULL,
    date_created TEXT NOT NULL,
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
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (user_id)
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (contact_user_id)
        REFERENCES employees(employee_id)
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


@pytest.fixture
def ticket_sqlite_connection(tmp_path: Path) -> Connection:
    db_path = tmp_path / "tickets.sqlite3"

    connection = Connection.create_connection(
        str(db_path),
        engine=sqlite3,
    )

    connection.connect.executescript(SCHEMA_SQL)

    connection.connect.executescript(
        """
        INSERT INTO departments (department_id, name)
        VALUES
            (1, 'Support'),
            (2, 'Infrastructure');

        INSERT INTO employees (
            employee_id,
            first_name,
            last_name,
            email,
            is_admin
        )
        VALUES
            (10, 'Alice', 'Manager', 'alice@example.com', 1),
            (20, 'Bob', 'Engineer', 'bob@example.com', 1),
            (30, 'Carol', 'Reviewer', 'carol@example.com', 1),
            (40, 'David', 'ClientUser', 'david@example.com', 0),
            (99, 'Eve', 'Other', 'eve@example.com', 1);

        INSERT INTO admins (
            employee_id,
            job_title,
            department_id
        )
        VALUES
            (10, 'Manager', 1),
            (20, 'Engineer', 1),
            (30, 'Reviewer', 1),
            (99, 'Other admin', 2);

        INSERT INTO clients (
            client_id,
            admin_id,
            name
        )
        VALUES (
            100,
            10,
            'Acme'
        );

        INSERT INTO users (
            employee_id,
            client_id
        )
        VALUES (
            40,
            100
        );

        INSERT INTO user_tickets (
            user_ticket_id,
            client_id,
            user_id,
            text_of_ticket,
            date_created
        )
        VALUES (
            500,
            100,
            40,
            'The network is unavailable',
            '2026-01-01T00:00:00+00:00'
        );
        """
    )

    connection.connect.commit()

    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def repo(
    ticket_sqlite_connection: Connection,
) -> TicketRepositorySQLite:
    return TicketRepositorySQLite(ticket_sqlite_connection)


def make_ticket(
    *,
    user_id: int = 0,
    contact_user_id: int = 0,
    user_ticket_id: int = 0,
    department_id: int = 1,
    comment: str = "",
) -> Ticket:
    return Ticket.create(
        ticket_id=0,
        client_id=100,
        admin_id=10,
        user_id=user_id,
        contact_user_id=contact_user_id,
        user_ticket_id=user_ticket_id,
        department_id=department_id,
        text_of_ticket="Fix the office network",
        description="Third-floor office",
        is_remote=False,
        urgency_level=2,
        comment=comment,
    )


def accept(ticket: Ticket) -> None:
    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=10,
            status=TicketStatus.ACCEPTED,
        )
    )


def assign(
    ticket: Ticket,
    *,
    executor_id: int = 20,
) -> None:
    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=10,
            status=TicketStatus.ASSIGNED,
            executor_id=executor_id,
            comment="Assigned to engineer",
        )
    )


def test_connection_enables_foreign_keys(
    ticket_sqlite_connection: Connection,
) -> None:
    row = ticket_sqlite_connection.connect.execute(
        "PRAGMA foreign_keys"
    ).fetchone()

    assert row == (1,)


def test_save_and_get_restores_ticket_aggregate(
    repo: TicketRepositorySQLite,
) -> None:
    ticket = make_ticket(
        user_id=40,
        contact_user_id=40,
        user_ticket_id=500,
        comment="Created by phone",
    )
    accept(ticket)
    assign(ticket)

    ticket.add_comment(
        Comment(
            employee_id=30,
            comment="Please visit after noon",
        )
    )

    saved = repo.save(ticket)
    loaded = repo.get(saved.ticket_id)

    assert saved.ticket_id > 0
    assert [record.status_id for record in saved.statuses] == [
        1,
        2,
        3,
    ]
    assert [comment.comment_id for comment in saved.comments] == [
        1,
        2,
    ]

    assert loaded.ticket_id == saved.ticket_id
    assert loaded.client_id == 100
    assert loaded.admin_id == 10
    assert loaded.user_id == 40
    assert loaded.contact_user_id == 40
    assert loaded.user_ticket_id == 500
    assert loaded.department_id == 1

    assert loaded.text_of_ticket == "Fix the office network"
    assert loaded.description == "Third-floor office"
    assert loaded.urgency_level == 2
    assert not loaded.is_remote

    assert [record.status for record in loaded.statuses] == [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
        TicketStatus.ASSIGNED,
    ]
    assert loaded.current_status() == TicketStatus.ASSIGNED
    assert loaded.current_executor_id() == 20
    assert loaded.statuses[-1].comment == "Assigned to engineer"

    assert [comment.comment for comment in loaded.comments] == [
        "Created by phone",
        "Please visit after noon",
    ]
    assert all(comment.comment_id > 0 for comment in loaded.comments)


def test_save_and_get_maps_sql_null_executor_to_domain_zero(
    repo: TicketRepositorySQLite,
) -> None:
    ticket = make_ticket()
    accept(ticket)

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=10,
            status=TicketStatus.SCHEDULED,
            planned_start_at=PLANNED_START,
            planned_finish_at=PLANNED_FINISH,
            comment="Scheduled for tomorrow",
        )
    )

    saved = repo.save(ticket)
    loaded = repo.get(saved.ticket_id)

    assert loaded.current_status() == TicketStatus.SCHEDULED
    assert loaded.current_executor_id() == 0
    assert not loaded.has_executor()

    assert (
        loaded.current_status_record().planned_start_at
        == PLANNED_START
    )
    assert (
        loaded.current_status_record().planned_finish_at
        == PLANNED_FINISH
    )


def test_save_existing_ticket_appends_history_and_increments_version(
    repo: TicketRepositorySQLite,
) -> None:
    saved = repo.save(make_ticket())
    original_status_id = saved.statuses[0].status_id

    ticket = repo.get(saved.ticket_id)

    accept(ticket)

    ticket.add_comment(
        Comment(
            employee_id=30,
            comment="Accepted for processing",
        )
    )

    ticket.description = "Updated description"
    ticket.is_remote = True

    updated = repo.save(ticket)
    loaded = repo.get(updated.ticket_id)

    assert updated.version == 1
    assert loaded.version == 1

    assert loaded.description == "Updated description"
    assert loaded.is_remote

    assert len(loaded.statuses) == 2
    assert loaded.statuses[0].status_id == original_status_id
    assert loaded.statuses[1].status_id > original_status_id
    assert loaded.current_status() == TicketStatus.ACCEPTED

    assert len(loaded.comments) == 1
    assert loaded.comments[0].comment == "Accepted for processing"
    assert loaded.comments[0].comment_id > 0


def test_loading_terminal_ticket_recomputes_derived_state(
    repo: TicketRepositorySQLite,
) -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=10,
            status=TicketStatus.REJECTED,
            comment="Incomplete request",
        )
    )

    saved = repo.save(ticket)
    loaded = repo.get(saved.ticket_id)

    assert loaded.current_status() == TicketStatus.REJECTED
    assert loaded.is_closed
    assert (
        loaded.date_finished
        == loaded.current_status_record().date_created
    )


def test_save_rejects_stale_ticket_version(
    repo: TicketRepositorySQLite,
) -> None:
    saved = repo.save(make_ticket())

    first_copy = repo.get(saved.ticket_id)
    second_copy = repo.get(saved.ticket_id)

    accept(first_copy)
    repo.save(first_copy)

    accept(second_copy)

    with pytest.raises(OptimisticLockError):
        repo.save(second_copy)

    loaded = repo.get(saved.ticket_id)

    assert loaded.version == 1
    assert loaded.current_status() == TicketStatus.ACCEPTED


def test_iter_active_by_client_id_excludes_terminal_tickets(
    repo: TicketRepositorySQLite,
) -> None:
    active_ticket = repo.save(make_ticket())

    rejected_ticket = make_ticket()
    rejected_ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=10,
            status=TicketStatus.REJECTED,
            comment="Rejected by manager",
        )
    )
    repo.save(rejected_ticket)

    batches = list(
        repo.iter_active_by_client_id(
            client_id=100,
            batch_size=1,
        )
    )

    loaded_ids = [
        ticket.ticket_id
        for batch in batches
        for ticket in batch
    ]

    assert loaded_ids == [active_ticket.ticket_id]


def test_delete_removes_ticket_children_via_foreign_key_cascade(
    repo: TicketRepositorySQLite,
    ticket_sqlite_connection: Connection,
) -> None:
    ticket = make_ticket(comment="Initial comment")
    accept(ticket)
    assign(ticket)

    saved = repo.save(ticket)

    repo.delete(saved.ticket_id)

    with pytest.raises(ItemNotFoundError):
        repo.get(saved.ticket_id)

    status_count = ticket_sqlite_connection.connect.execute(
        """
        SELECT COUNT(*)
        FROM ticket_status_records
        WHERE ticket_id = ?
        """,
        (saved.ticket_id,),
    ).fetchone()[0]

    comment_count = ticket_sqlite_connection.connect.execute(
        """
        SELECT COUNT(*)
        FROM ticket_comments
        WHERE ticket_id = ?
        """,
        (saved.ticket_id,),
    ).fetchone()[0]

    assert status_count == 0
    assert comment_count == 0


def test_reference_checks_and_user_ticket_lookup(
    repo: TicketRepositorySQLite,
) -> None:
    ticket = make_ticket(
        user_id=40,
        contact_user_id=40,
        user_ticket_id=500,
    )

    accept(ticket)
    assign(ticket, executor_id=20)

    ticket.add_comment(
        Comment(
            employee_id=30,
            comment="Review required",
        )
    )

    saved = repo.save(ticket)

    assert repo.does_client_exist(100)
    assert not repo.does_client_exist(999)

    assert repo.does_user_tickets_exist(500)
    assert not repo.does_user_tickets_exist(999)

    loaded_by_user_ticket = repo.get_by_user_ticket_id(500)
    assert loaded_by_user_ticket.ticket_id == saved.ticket_id

    assert repo.has_admin_reference(10)
    assert repo.has_admin_reference(20)
    assert repo.has_admin_reference(30)
    assert not repo.has_admin_reference(99)

    assert repo.has_department_reference(1)
    assert not repo.has_department_reference(999)


def test_get_all_returns_loaded_aggregates(
    repo: TicketRepositorySQLite,
) -> None:
    first = repo.save(make_ticket())
    second = repo.save(
        make_ticket(
            department_id=2,
        )
    )

    tickets = repo.get_all()

    assert [ticket.ticket_id for ticket in tickets] == [
        first.ticket_id,
        second.ticket_id,
    ]

    assert all(
        ticket.current_status() == TicketStatus.CREATED
        for ticket in tickets
    )