"""Observe issue and rotation through the active auth routes."""
from datetime import UTC, datetime, timedelta
import secrets

import jwt
import pytest

from conftest import transaction
from src.web.auth.tokens import AccessToken, hash_token
from src.web.config import Settings


def metadata(world, token):
    storage = getattr(world.api.app.state, "refresh_token_storage", None)
    if storage is not None:
        item = storage.get(token)
        return item.created_at, item.expires_at
    with transaction(world.path) as uow:
        item = uow.refresh_sessions.get(hash_token(token))
        assert item is not None
        return item.created_at, item.expires_at


def refresh(world, token, realm="user"):
    return world.api.post(f"/auth/{realm}/refresh", json={"refresh_token": token})


def expiration(world, response):
    config = world.api.app.state.settings
    return jwt.decode(
        response.json()["access_token"], config.SECRET_KEY, algorithms=[config.ALGORITHM],
        audience=config.JWT_AUDIENCE, issuer=config.JWT_ISSUER,
        options={"verify_exp": False, "verify_iat": False},
    )["exp"]


def test_central_default_lifetimes(monkeypatch):
    """Settings default to 5 minutes and 7 days."""
    monkeypatch.delenv('ACCESS_TOKEN_EXPIRE_MINUTES', raising=False)
    monkeypatch.delenv('REFRESH_TOKEN_EXPIRE_DAYS', raising=False)
    settings = Settings(_env_file=None, SECRET_KEY=secrets.token_hex(32))
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 5
    assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7



@pytest.mark.parametrize("world", ["sqlite", "memory"], indirect=True)
def test_issue_uses_five_minutes_and_seven_days(world, monkeypatch):
    """200 with 300 seconds and persisted 7 days; wrong password gives 401."""
    now = datetime.now(UTC).replace(microsecond=0)
    monkeypatch.setattr("src.web.auth.tokens.utcnow", lambda: now)
    response = world.api.post("/auth/user/login", data={"username": world.login, "password": world.password})
    assert response.status_code == 200
    assert response.json()["expires_in"] == 300
    assert response.json()["token_type"] == "bearer"
    assert expiration(world, response) == int(now.timestamp()) + 300
    assert metadata(world, response.json()["refresh_token"]) == (now, now + timedelta(days=7))
    invalid = world.api.post("/auth/user/login", data={"username": world.login, "password": secrets.token_hex(24)})
    assert invalid.status_code == 401


@pytest.mark.parametrize("world", ["sqlite", "memory"], indirect=True)
def test_rotation_has_one_deadline_and_single_use(world, monkeypatch):
    """Rotations keep t0, cap access, consume the old credential and reject at expiry."""
    current = world.refresh
    start, end = metadata(world, current)
    assert end - start == timedelta(days=7)
    for remaining in (timedelta(days=2), timedelta(hours=1), timedelta(seconds=45)):
        now = end - remaining
        monkeypatch.setattr("src.web.auth.tokens.utcnow", lambda: now)
        response = refresh(world, current)
        assert response.status_code == 200
        previous, current = current, response.json()["refresh_token"]
        assert current != previous
        assert metadata(world, current) == (start, end)
        assert expiration(world, response) <= end.timestamp()
        assert response.json()["expires_in"] <= min(300, remaining.total_seconds())
        assert refresh(world, previous).status_code == 401
    monkeypatch.setattr("src.web.auth.tokens.utcnow", lambda: end)
    assert refresh(world, current).status_code == 401
    assert metadata(world, current) == (start, end)


@pytest.mark.parametrize("world", ["sqlite", "memory"], indirect=True)
def test_rotation_encoding_error_preserves_old_session(world, monkeypatch):
    """Encoding failure gives 500 and preserves the valid old credential."""
    previous = metadata(world, world.refresh)

    def fail_encoding(*args, **kwargs):
        raise RuntimeError("Synthetic encoding error")

    with monkeypatch.context() as patch:
        patch.setattr(AccessToken, "encode", fail_encoding)
        assert refresh(world, world.refresh).status_code == 500
    assert metadata(world, world.refresh) == previous
    assert refresh(world, world.refresh).status_code == 200


def test_two_refreshes_consume_credential_only_once(world):
    """Concurrent rotations yield one usable successor and at most one success."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    gate = Barrier(2)

    def request():
        gate.wait(timeout=10)
        return refresh(world, world.refresh)

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = [future.result(timeout=15) for future in (pool.submit(request), pool.submit(request))]
    success = [response for response in responses if response.status_code == 200]
    refused = [response.status_code for response in responses if response.status_code != 200]
    assert len(success) == 1 and len(refused) == 1
    assert refused[0] in (401, 503)
    assert refresh(world, world.refresh).status_code == 401
    assert metadata(world, success[0].json()["refresh_token"])


@pytest.mark.parametrize("world", ["sqlite", "memory"], indirect=True)
def test_legacy_naive_session_timestamps_are_interpreted_in_utc(world, monkeypatch):
    """The current legacy storage rotates UTC-normalized dates without extending TTL."""
    storage = getattr(world.api.app.state, "refresh_token_storage", None)
    if storage is None:
        pytest.skip("Legacy sessions require login after 05; tested by test_upgrade_requires_login_and_never_uses_old_refresh")
    prior = storage.get(world.refresh)
    simple_dates = prior.model_copy(update={
        "created_at": prior.created_at.replace(tzinfo=None),
        "expires_at": prior.expires_at.replace(tzinfo=None),
    })
    storage.delete(world.refresh)
    storage.put(simple_dates)
    now = prior.expires_at - timedelta(seconds=45)
    monkeypatch.setattr("src.web.auth.tokens.utcnow", lambda: now)
    answer = refresh(world, world.refresh)
    assert answer.status_code == 200
    assert answer.json()["expires_in"] == 45
    assert metadata(world, answer.json()["refresh_token"]) == (prior.created_at, prior.expires_at)
