import pytest

from src.adapters.repositories.ticket_user_repository import TicketUserRepositorySQLite
from src.domain.ticket_user import TicketUser


@pytest.mark.xfail(reason="Current TicketUserRepositorySQLite may need schema/query cleanup. This test documents expected behavior.")
def test_ticket_user_repository_save_get_with_status_history(sqlite_schema):
    repo = TicketUserRepositorySQLite(sqlite_schema)
    ticket = TicketUser.create(ticket_id=0, client_id=1, user_id=1, description="Need help")

    saved = repo.save(ticket)
    loaded = repo.get(saved.ticket_id)

    assert loaded.ticket_id > 0
    assert loaded.description == "Need help"
    assert loaded.current_status().value == "created"
