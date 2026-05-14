import pytest

from src.adapters.repositories.client_repository import ClientRepositorySQLite
from src.adapters.repositories.exceptions import OptimisticLockError
from src.domain.client import Client


def test_client_repository_save_get_update_delete(sqlite_schema):
    repo = ClientRepositorySQLite(sqlite_schema)
    client = Client.create(client_id=0, name="Acme", email="info@acme.com", created_by_admin_id=1)

    saved = repo.save(client)
    loaded = repo.get(saved.client_id)

    assert saved.client_id > 0
    assert str(loaded.name) == "Acme"
    assert str(loaded.email) == "info@acme.com"

    loaded.update_contact_info(email="support@acme.com")
    updated = repo.save(loaded)
    assert updated.version == 1
    assert str(repo.get(updated.client_id).email) == "support@acme.com"

    repo.delete(updated.client_id)
    assert repo.exists(updated.client_id) is False


def test_client_repository_optimistic_lock(sqlite_schema):
    repo = ClientRepositorySQLite(sqlite_schema)
    client = repo.save(Client.create(client_id=0, name="Acme"))

    first_copy = repo.get(client.client_id)
    second_copy = repo.get(client.client_id)

    first_copy.update_contact_info(email="first@acme.com")
    repo.save(first_copy)

    second_copy.update_contact_info(email="second@acme.com")
    with pytest.raises(OptimisticLockError):
        repo.save(second_copy)
