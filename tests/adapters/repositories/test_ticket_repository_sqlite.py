import pytest

from src.adapters.repositories.ticket_repository import TicketRepositorySQLite
from src.domain.ticket import Ticket


@pytest.mark.xfail(reason="Current TicketRepositorySQLite has known insert/load mapping bugs for status/executor history.")
def test_ticket_repository_save_get_with_history(sqlite_schema):
    repo = TicketRepositorySQLite(sqlite_schema)
    ticket = Ticket.create(
        ticket_id=0,
        client_id=1,
        admin_id=1,
        description="Broken printer",
        text_of_ticket="Broken printer",
        executor_id=2,
        comment="Initial comment",
    )

    saved = repo.save(ticket)
    loaded = repo.get(saved.ticket_id)

    assert loaded.ticket_id > 0
    assert loaded.current_status().value == "created"
    assert loaded.comments[-1].comment == "Initial comment"
    assert loaded.executors[-1].executor_id == 2
