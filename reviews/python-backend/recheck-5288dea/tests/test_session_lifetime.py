"""Lifetime contract through the real refresh endpoint and persistent metadata."""
import secrets
from datetime import UTC, timedelta

import jwt
import pytest

from conftest import transaction
from src.web.auth.exceptions import TokenNotFoundError
from src.web.auth.storage_sqlite import TokenStorageSQLite
from src.web.auth.tokens import AccessToken, RefreshToken, hash_token
from src.web.config import Settings


def as_utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def refresh(world, current):
    return world.api.post('/auth/user/refresh', json={'refresh_token': current})


def issued_exp(world, response):
    settings = world.api.app.state.settings
    # Verify signature/realm; only temporal checks are disabled while measuring
    # tokens issued by the real endpoint under the controlled future clock.
    claims = jwt.decode(response.json()['access_token'], settings.SECRET_KEY,
                        algorithms=[settings.ALGORITHM], audience=settings.JWT_AUDIENCE,
                        issuer=settings.JWT_ISSUER,
                        options={'verify_iat': False, 'verify_exp': False})
    return claims['exp']


def test_central_default_lifetimes(monkeypatch):
    monkeypatch.delenv('ACCESS_TOKEN_EXPIRE_MINUTES', raising=False)
    monkeypatch.delenv('REFRESH_TOKEN_EXPIRE_DAYS', raising=False)
    settings = Settings(_env_file=None, SECRET_KEY=secrets.token_hex(32))
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 5
    assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7


@pytest.mark.parametrize('world', ['memory', 'sqlite'], indirect=True)
def test_several_rotations_preserve_initial_dates(world, monkeypatch):
    store = world.api.app.state.refresh_token_storage
    original = store.get(world.refresh)
    current = world.refresh
    initial_start, initial_end = original.created_at, original.expires_at
    assert initial_end - initial_start == timedelta(days=7)
    with transaction(world.path) as uow:
        assert uow.users.get(world.user_id).enabled
    for remaining in (timedelta(days=2), timedelta(hours=1), timedelta(seconds=45)):
        moment = as_utc(initial_end) - remaining
        monkeypatch.setattr('src.web.auth.tokens.utcnow', lambda: moment)
        response = refresh(world, current)
        assert response.status_code == 200
        previous = current
        current = response.json()['refresh_token']
        with pytest.raises(TokenNotFoundError):
            store.get(previous)
        # Reopen the persistent adapter to prove dates survive serialization.
        reader = TokenStorageSQLite(store.path) if isinstance(store, TokenStorageSQLite) else store
        successor = reader.get(current)
        assert successor.created_at == initial_start
        assert successor.expires_at == initial_end
        assert issued_exp(world, response) <= as_utc(initial_end).timestamp()
        assert response.json()['expires_in'] <= min(300, int(remaining.total_seconds()))


@pytest.mark.parametrize('world', ['memory', 'sqlite'], indirect=True)
def test_refresh_at_absolute_expiry_is_rejected_without_replacement(world, monkeypatch):
    store = world.api.app.state.refresh_token_storage
    original = store.get(world.refresh)
    moment = as_utc(original.expires_at)
    count = store.count()
    monkeypatch.setattr('src.web.auth.tokens.utcnow', lambda: moment)
    response = refresh(world, world.refresh)
    assert response.status_code == 401
    assert store.count() == count
    assert store.get(world.refresh).expires_at == original.expires_at


@pytest.mark.parametrize('world', ['memory', 'sqlite'], indirect=True)
def test_legacy_naive_dates_remain_supported_and_bound_access(world, monkeypatch):
    store = world.api.app.state.refresh_token_storage
    original = store.get(world.refresh)
    legacy = original.model_copy(update={
        'created_at': as_utc(original.created_at).replace(tzinfo=None),
        'expires_at': as_utc(original.expires_at).replace(tzinfo=None),
    })
    store.delete(world.refresh)
    store.put(legacy)
    moment = as_utc(legacy.expires_at) - timedelta(seconds=45)
    monkeypatch.setattr('src.web.auth.tokens.utcnow', lambda: moment)
    response = refresh(world, world.refresh)
    assert response.status_code == 200
    successor = store.get(response.json()['refresh_token'])
    assert successor.created_at == as_utc(legacy.created_at)
    assert successor.expires_at == as_utc(legacy.expires_at)
    assert successor.created_at.tzinfo is not None
    assert successor.expires_at.tzinfo is not None
    assert issued_exp(world, response) <= as_utc(legacy.expires_at).timestamp()
    store.cleanup_expired_tokens()
    assert store.get(response.json()['refresh_token']).is_valid()


@pytest.mark.parametrize('world', ['memory', 'sqlite'], indirect=True)
def test_encode_failure_preserves_old_refresh_for_retry(world, monkeypatch):
    store = world.api.app.state.refresh_token_storage
    count = store.count()
    original = store.get(world.refresh)
    def fail_encode(*args, **kwargs):
        raise RuntimeError('Injected encoding failure')
    with monkeypatch.context() as patch:
        patch.setattr(AccessToken, 'encode', fail_encode)
        response = refresh(world, world.refresh)
    assert response.status_code == 500
    assert store.count() == count
    assert store.get(world.refresh).is_valid()
    assert store.get(world.refresh).expires_at == original.expires_at
    assert refresh(world, world.refresh).status_code == 200


@pytest.mark.parametrize('world', ['memory', 'sqlite'], indirect=True)
def test_storage_failure_preserves_old_refresh_for_retry(world, monkeypatch):
    store = world.api.app.state.refresh_token_storage
    count = store.count()
    original_hash = hash_token(world.refresh)
    with monkeypatch.context() as patch:
        if isinstance(store, TokenStorageSQLite):
            insert = store._insert
            def insert_then_fail(db, successor):
                insert(db, successor)
                raise RuntimeError('Injected failure after successor INSERT')
            patch.setattr(store, '_insert', insert_then_fail)
        else:
            copy_model = RefreshToken.model_copy
            def copy_successor_or_fail(self, *args, **kwargs):
                if self.token_hash != original_hash:
                    raise RuntimeError('Injected successor copy failure')
                return copy_model(self, *args, **kwargs)
            patch.setattr(RefreshToken, 'model_copy', copy_successor_or_fail)
        response = refresh(world, world.refresh)
    assert response.status_code == 500
    assert store.count() == count
    assert store.get(world.refresh).is_valid()
    assert refresh(world, world.refresh).status_code == 200
