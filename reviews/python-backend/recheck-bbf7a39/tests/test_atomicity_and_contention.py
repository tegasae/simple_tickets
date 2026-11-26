"""HTTP regressions for transaction rollback and temporary SQLite contention.

The contention contract is one successful PATCH and one typed temporary 503,
without automatic command retry. The unchanged bbf7a39 snapshot fails that
contract; a generic 500 is not an acceptable contention result.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock

import pytest

from conftest import database_uow
from src.adapters.repositories.exceptions import PersistenceError
from src.adapters.repositories.ticket_repository import TicketRepositorySQLite
from src.application.services.ticket_service import TicketApplicationService


PAIR_TABLES = (
    "clients",
    "employees",
    "tickets",
    "user_tickets",
    "ticket_status_records",
    "user_tickets_status_record",
    "ticket_comments",
    "user_tickets_comment",
)


def persisted_pair_state(path):
    """Read committed roots, histories, comments and related guard versions."""
    with database_uow(path) as uow:
        return {
            table: uow.connection.connect.execute(
                f"SELECT * FROM {table} ORDER BY rowid"
            ).fetchall()
            for table in PAIR_TABLES
        }


@pytest.mark.parametrize("command", ["create", "cancel"])
def test_pair_command_rolls_back_when_second_aggregate_write_fails(
    world, monkeypatch, command,
):
    if command == "cancel":
        external = world.create_user_ticket()
        path = f"/user/tickets/{external['ticket_user_id']}/cancel"
        method, payload = "PATCH", {"comment": "Synthetic cancellation"}
    else:
        path = "/user/tickets/"
        method, payload = "POST", {
            "text_of_ticket": "Synthetic rollback request",
            "comment": "Synthetic initial comment",
        }

    before = persisted_pair_state(world.path)
    original_save = TicketRepositorySQLite.save
    second_write = []

    def save_then_fail(repository, ticket):
        saved = original_save(repository, ticket)
        # The first aggregate and the second aggregate's real SQL are already
        # visible inside this transaction. The failure must undo both.
        connection = repository.conn.connect
        second_write.append({
            "ticket_id": saved.ticket_id,
            "user_ticket_id": saved.user_ticket_id,
            "ticket_rows": connection.execute(
                "SELECT COUNT(*) FROM tickets"
            ).fetchone()[0],
            "user_ticket_rows": connection.execute(
                "SELECT COUNT(*) FROM user_tickets"
            ).fetchone()[0],
            "user_status": connection.execute(
                "SELECT status FROM user_tickets_status_record "
                "WHERE user_ticket_id=? "
                "ORDER BY user_ticket_status_record_id DESC LIMIT 1",
                (saved.user_ticket_id,),
            ).fetchone()[0],
        })
        raise PersistenceError("Synthetic failure after the second aggregate write")

    monkeypatch.setattr(TicketRepositorySQLite, "save", save_then_fail)
    response = world.client.request(
        method, path, headers=world.user_headers, json=payload,
    )

    # This injected unknown persistence failure is correctly a server error;
    # it is deliberately distinct from the temporary contention test below.
    assert response.status_code == 500, response.text
    assert response.json() == {"detail": "Internal server error"}
    assert len(second_write) == 1
    observed = second_write[0]
    assert observed["ticket_id"] > 0 and observed["user_ticket_id"] > 0
    assert observed["ticket_rows"] == observed["user_ticket_rows"] == 1
    assert observed["user_status"] == (
        "cancelled_by_user" if command == "cancel" else "created"
    )
    # A fresh connection must see no partial roots/statuses/comments or guard
    # version changes after the failed HTTP command.
    assert persisted_pair_state(world.path) == before


def test_concurrent_description_patches_return_success_and_temporary_503(
    world, monkeypatch,
):
    created = world.client.post(
        "/admin/tickets/", headers=world.admin_headers, json={
            "client_id": world.client_id,
            "department_id": world.department_id,
            "text_of_ticket": "Synthetic concurrent request",
        },
    )
    assert created.status_code == 201, created.text
    ticket_id = created.json()["ticket_id"]
    before = persisted_pair_state(world.path)
    with database_uow(world.path) as uow:
        initial_version = uow.tickets.get(ticket_id).version

    after_read = Barrier(2, timeout=10)
    record_lock = Lock()
    reads = []
    original_get = TicketApplicationService._get_ticket

    def read_then_synchronize(service, requested_id):
        ticket = original_get(service, requested_id)
        if requested_id == ticket_id:
            with record_lock:
                reads.append(id(service.uow.connection))
            after_read.wait()
        return ticket

    monkeypatch.setattr(TicketApplicationService, "_get_ticket", read_then_synchronize)
    descriptions = ("Synthetic writer one", "Synthetic writer two")

    def patch_description(description):
        response = world.client.patch(
            f"/admin/tickets/{ticket_id}/description",
            headers=world.admin_headers, json={"description": description},
        )
        return description, response

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(patch_description, descriptions))

    statuses = [response.status_code for _, response in results]
    successful = [description for description, response in results if response.status_code == 200]
    # Two independent real request-scoped connections read before either
    # writes. A retry would add reads and must not silently rerun the command.
    assert len(reads) == 2 and len(set(reads)) == 2
    assert len(successful) == 1, statuses
    with database_uow(world.path) as uow:
        stored = uow.tickets.get(ticket_id)
        assert stored.description.value == successful[0]
        assert stored.version == initial_version + 1

    after = persisted_pair_state(world.path)
    for table in PAIR_TABLES:
        if table != "tickets":
            assert after[table] == before[table], table
    assert len(after["tickets"]) == len(before["tickets"]) == 1

    # Keep this last so the unchanged snapshot also proves committed-state
    # invariants before reporting its current generic error as a regression.
    assert sorted(statuses) == [200, 503], (
        "Temporary SQLite contention must produce 503 without automatic retry",
        statuses,
    )
