import pytest

from src.adapters.repositories.client_repository import ClientRepositorySQLite
from src.adapters.repositories.user_repository import UserRepositorySQLite
from src.domain.client import Client
from src.domain.employee import User


#@pytest.mark.xfail(reason="Current UserRepositorySQLite.save() does not sync account/roles on create. Remove xfail after repository is fixed.")
def test_user_repository_save_get_with_account(sqlite_schema):
    clients = ClientRepositorySQLite(sqlite_schema)
    client = clients.save(Client.create(client_id=0, name="Acme"))

    repo = UserRepositorySQLite(sqlite_schema)
    user = User.create(
        employee_id=0,
        first_name="Alice",
        client_id=client.client_id,
        login="alice",
        password="Secret123!",
        roles=frozenset({1}),
    )

    saved = repo.save(user)
    loaded = repo.get(saved.employee_id)

    assert loaded.employee_id > 0
    assert loaded.client_id == client.client_id
    assert str(loaded.account.login) == "alice"
    assert loaded.role_ids() == frozenset({1})


def test_user_repository_save_get_without_account(sqlite_schema):
    clients = ClientRepositorySQLite(sqlite_schema)
    client = clients.save(Client.create(client_id=0, name="Acme"))

    repo = UserRepositorySQLite(sqlite_schema)
    user = User.create(employee_id=0, first_name="Alice", client_id=client.client_id)

    saved = repo.save(user)
    loaded = repo.get(saved.employee_id)

    assert loaded.employee_id > 0
    assert loaded.client_id == client.client_id
    assert str(loaded.account) == "<no-account>"
