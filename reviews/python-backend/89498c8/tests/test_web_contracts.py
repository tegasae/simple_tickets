import importlib.util
import runpy
from secrets import token_hex

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError


def test_direct_web_launcher_uses_importable_asgi_target(monkeypatch):
    import uvicorn

    targets = []
    monkeypatch.setattr(uvicorn, "run", lambda target, **options: targets.append(target))
    runpy.run_path("src/web/main.py", run_name="__main__")
    module_name, attribute = targets[0].split(":")
    assert module_name != "main"  # The root module launches pytest and exits.
    assert importlib.util.find_spec(module_name) is not None
    assert callable(getattr(importlib.import_module(module_name), attribute))


def test_missing_internal_ticket_is_a_404(web):
    response = web.get("/admin/tickets/1000000")
    assert response.status_code == 404


def test_typical_signing_configuration_loads_explicit_key():
    from src.web.config import Settings

    key = token_hex(32)
    assert Settings(SECRET_KEY=key).SECRET_KEY == key


def test_signing_config_has_no_implicit_key(monkeypatch):
    from src.web.config import Settings

    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError, match="Configure SECRET_KEY"):
        Settings(_env_file=None)


def test_own_user_session_can_be_closed_by_refresh_token(sample):
    from src.web.main import create_app

    app = create_app()
    app.state.settings.DATABASE_URL = str(sample.path)
    with TestClient(app, raise_server_exceptions=False) as client:
        login = client.post("/auth/user/login", data={
            "username": sample.user_login, "password": sample.user_password,
        })
        assert login.status_code == 200
        session = {"refresh_token": login.json()["refresh_token"]}
        assert client.post("/auth/user/logout", json=session).status_code == 200
        assert client.post("/auth/user/refresh", json=session).status_code == 401


def test_root_test_runner_propagates_pytest_status(monkeypatch):
    import sys

    calls = []
    monkeypatch.setattr(pytest, "main", lambda args: calls.append(args) or 3)
    monkeypatch.setattr(sys, "argv", ["main.py", "synthetic_test_target"])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path("main.py", run_name="__main__")
    assert (exit_info.value.code, calls) == (3, [["synthetic_test_target"]])


def test_new_password_hashes_are_salted_and_legacy_hash_remains_readable():
    import hashlib

    from src.domain.value_objects import Password

    plain = "Aa1!" + token_hex(12)
    first = Password.from_plain(plain)
    second = Password.from_plain(plain)
    if first.value == second.value:
        pytest.fail("Two password hashes share the same value")
    assert first.verify(plain) and second.verify(plain)
    assert not second.verify(plain + "1")
    legacy = Password.from_hash(hashlib.sha256(plain.encode()).hexdigest())
    assert legacy.verify(plain)


def test_active_user_can_list_own_tickets_and_log_out_by_authenticated_username(sample):
    from src.web.main import create_app

    app = create_app()
    app.state.settings.DATABASE_URL = str(sample.path)
    with TestClient(app, raise_server_exceptions=False) as client:
        login = client.post("/auth/user/login", data={
            "username": sample.user_login, "password": sample.user_password,
        })
        assert login.status_code == 200
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        assert client.get("/user/tickets/open", headers=headers).status_code == 200
        logout = client.post("/auth/user/logout", headers=headers, json={
            "username": sample.user_login,
        })
        assert logout.status_code == 200
        session = {"refresh_token": login.json()["refresh_token"]}
        assert client.post("/auth/user/refresh", json=session).status_code == 401


def test_unexpected_error_has_generic_response(monkeypatch, web):
    from src.adapters.repositories.ticket_repository import TicketRepositorySQLite

    def fail_read(*args, **kwargs):
        raise RuntimeError("Synthetic underlying failure")

    monkeypatch.setattr(TicketRepositorySQLite, "get", fail_read)
    response = web.get("/admin/tickets/1")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


def test_negative_admin_ticket_id_is_a_client_error(web):
    assert web.get("/admin/tickets/-1").status_code == 400


def test_employee_write_conflict_keeps_its_http_status(monkeypatch, web, sample):
    from src.adapters.repositories.exceptions import OptimisticLockError
    from src.adapters.repositories.user_repository import UserRepositorySQLite

    def reject_stale_version(*args, **kwargs):
        raise OptimisticLockError("Synthetic write conflict")

    monkeypatch.setattr(UserRepositorySQLite, "save", reject_stale_version)
    response = web.patch(f"/admin/users/{sample.user_id}/account/disable")
    assert response.status_code == 409
