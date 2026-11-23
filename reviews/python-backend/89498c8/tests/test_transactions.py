import sqlite3

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.assemblers.assembler import TicketAssembler, TicketUserAssembler
from utils.db.connect import Connection
from utils.db.exceptions import DBOperationError


def test_automatic_commit_failure_rolls_back_before_reuse(sample):
    reader = sqlite3.connect(sample.path)
    connection = Connection.create_connection(str(sample.path), engine=sqlite3)
    connection.connect.execute("PRAGMA busy_timeout=0")
    uow = SQLiteUnitOfWork(connection)
    try:
        reader.execute("BEGIN")
        original_name, = reader.execute(
            "SELECT name FROM clients WHERE client_id=?", (sample.client_id,),
        ).fetchone()
        with pytest.raises(DBOperationError, match="commit"):
            with uow:
                connection.connect.execute(
                    "UPDATE clients SET name=? WHERE client_id=?",
                    ("Uncommitted synthetic name", sample.client_id),
                )
        reader.rollback()
        active_after_failure = connection.in_transaction()
        with uow:
            pass
        persisted_name, = reader.execute(
            "SELECT name FROM clients WHERE client_id=?", (sample.client_id,),
        ).fetchone()
        assert (active_after_failure, persisted_name) == (False, original_name)
    finally:
        reader.close()
        connection.close()


def test_internal_ticket_assembly_failure_rolls_back(web, sample, uow, monkeypatch):
    def fail_assembly(_):
        raise RuntimeError("Synthetic assembler failure")

    monkeypatch.setattr(TicketAssembler, "to_dto", fail_assembly)
    response = web.post("/admin/tickets/", json={
        "client_id": sample.client_id, "text_of_ticket": "Synthetic failed operation",
    })
    assert response.status_code == 500
    with uow:
        assert uow.tickets.get_all() == []


def test_linked_ticket_assembly_failure_rolls_back_both(web, sample, uow, monkeypatch):
    created = web.post("/user/tickets/", json={"text_of_ticket": "Synthetic request"}).json()
    ticket_user_id = created["ticket_user_id"]

    def fail_assembly(_):
        raise RuntimeError("Synthetic assembler failure")

    monkeypatch.setattr(TicketUserAssembler, "to_dto", fail_assembly)
    response = web.patch(f"/user/tickets/{ticket_user_id}/cancel", json={})
    assert response.status_code == 500
    with uow:
        assert uow.user_tickets.get(ticket_user_id).current_status() == "created"
        assert uow.tickets.get_by_user_ticket_id(ticket_user_id).current_status() == "created_from_ticket_user"


def test_legacy_null_versions_advance_and_preserve_optimistic_lock(web, sample, uow):
    from src.adapters.repositories.exceptions import OptimisticLockError

    created = web.post("/user/tickets/", json={"text_of_ticket": "Synthetic version test"}).json()
    linked_id = created["ticket_user_id"]
    with sqlite3.connect(sample.path) as db:
        db.execute("UPDATE user_tickets SET version=NULL WHERE user_ticket_id=?", (linked_id,))
        db.execute("UPDATE tickets SET version=NULL WHERE user_ticket_id=?", (linked_id,))

    with uow:
        stale_internal = uow.tickets.get_by_user_ticket_id(linked_id)
        stale_external = uow.user_tickets.get(linked_id)
        uow.tickets.save(uow.tickets.get_by_user_ticket_id(linked_id))
        uow.user_tickets.save(uow.user_tickets.get(linked_id))

    with uow:
        assert uow.tickets.get_by_user_ticket_id(linked_id).version == 1
        assert uow.user_tickets.get(linked_id).version == 1

    for repository, stale in ((uow.tickets, stale_internal), (uow.user_tickets, stale_external)):
        with pytest.raises(OptimisticLockError):
            with uow:
                repository.save(stale)


def test_uow_cannot_take_over_another_open_sqlite_transaction(sample):
    connection = Connection.create_connection(str(sample.path), engine=sqlite3)
    outer = SQLiteUnitOfWork(connection)
    inner = SQLiteUnitOfWork(connection)
    try:
        with outer:
            with pytest.raises(RuntimeError, match="active transaction"):
                with inner:
                    pass
            assert connection.in_transaction()
    finally:
        connection.close()
