from __future__ import annotations

from datetime import timedelta

import pytest

from src.domain.client import Client
from src.domain.employee import Admin, User
from src.web.auth.exceptions import InvalidCredentialsError, TokenError, TokenNotFoundError, UserNotValidError
from src.web.auth.models import LoginRequest, LogoutRequest, RefreshRequest, UserAuth
from src.web.auth.services.auth_service import AdminAuthService, UserAuthService
from src.web.auth.services.services import AuthManager, TokenService
from src.web.auth.storage import TokenStorageMemory
from src.web.auth.tokens import AccessToken, JWTToken, RefreshToken, hash_token, utcnow
from tests_pyramid.support.fakes import FakeUnitOfWork

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def clear_storage() -> None:
    TokenStorageMemory().clear()
    yield
    TokenStorageMemory().clear()


def test_access_token_encode_decode_scope_and_subject_helpers() -> None:
    token = AccessToken.create(subject_id=10, subject_type="admin", scope=["ticket.view", "ticket.edit"])
    encoded = token.encode()
    decoded = AccessToken.decode(encoded)
    assert decoded.sub == "10"
    assert decoded.subject_type == "admin"
    assert set(decoded.scope) == {"ticket.view", "ticket.edit"}
    assert decoded.get_admin_id() == 10
    with pytest.raises(TokenError):
        decoded.get_user_id()


def test_access_token_rejects_wrong_token_type_and_expired() -> None:
    expired = AccessToken.create(subject_id=10, subject_type="admin")
    expired.exp = utcnow() - timedelta(seconds=1)
    with pytest.raises(TokenError):
        AccessToken.decode(expired.encode())


def test_access_token_scope_conversion() -> None:
    assert AccessToken.scope_from_str("a  b c") == ["a", "b", "c"]
    assert AccessToken.scope_from_str("") == []
    assert AccessToken.create(subject_id=1, subject_type="user", scope=["a"]).scope_to_str() == "a"


def test_refresh_token_hash_use_revoke_and_validity() -> None:
    token = RefreshToken.create(subject_id=1, subject_type="user", username="user")
    assert token.token_hash == hash_token(token.token_id)
    assert token.is_valid()
    token.mark_used()
    assert token.used and token.use_count == 1 and not token.is_valid()
    token2 = RefreshToken.create(subject_id=1, subject_type="user", username="user")
    token2.revoke()
    assert not token2.is_valid()


def test_jwt_token_encode_contains_pair_metadata() -> None:
    pair = JWTToken.create(subject_id=1, subject_type="user", username="user", scope=["ticket.view"])
    data = pair.encode()
    assert data["token_type"] == "bearer"
    assert data["refresh_token"] == pair.refresh_token.token_id
    assert data["scope"] == "ticket.view"
    assert AccessToken.decode(data["access_token"]).get_user_id() == 1


def test_token_storage_put_get_delete_count_and_missing() -> None:
    storage = TokenStorageMemory()
    token = RefreshToken.create(subject_id=1, subject_type="user", username="user")
    storage.put(token)
    assert storage.count() == 1
    assert storage.get(token.token_id) is token
    storage.delete(token.token_id)
    assert storage.count() == 0
    with pytest.raises(TokenNotFoundError):
        storage.get(token.token_id)


def test_token_storage_user_tokens_revoke_and_cleanup() -> None:
    storage = TokenStorageMemory()
    one = RefreshToken.create(subject_id=1, subject_type="user", username="same")
    two = RefreshToken.create(subject_id=1, subject_type="user", username="same")
    other = RefreshToken.create(subject_id=2, subject_type="user", username="other")
    for token in (one, two, other):
        storage.put(token)
    assert len(storage.get_user_tokens("same")) == 2
    assert storage.revoke_user_tokens("same") == 2
    assert storage.cleanup_expired_tokens() == 2
    assert storage.count() == 1


def test_token_service_create_verify_rotate_and_revoke() -> None:
    storage = TokenStorageMemory()
    service = TokenService(storage)
    pair = service.create_token_pair(username="user", subject_id=1, subject_type="user", scope=["x"])
    assert storage.count() == 1
    assert service.verify_access_token(pair["access_token"]).get_user_id() == 1
    assert service.verify_refresh_token(pair["refresh_token"])
    rotated = service.renew_tokens(pair["refresh_token"])
    assert rotated["refresh_token"] != pair["refresh_token"]
    assert not service.verify_refresh_token(pair["refresh_token"])
    service.revoke_token(rotated["refresh_token"])
    assert storage.count() == 0


class StubAuthService:
    def __init__(self, *, scope=None, exists=True):
        self.scope = scope or []
        self.exists = exists

    def authenticate_user(self, login_request: LoginRequest) -> UserAuth:
        return UserAuth(id=7, username=login_request.username, scope=self.scope)

    def validate_user_exists(self, login_request: LoginRequest) -> bool:
        return self.exists


def test_auth_manager_login_scope_resolution() -> None:
    storage = TokenStorageMemory()
    manager = AuthManager(auth_service=StubAuthService(scope=["a", "b"]), token_storage=storage, subject_type="admin")
    result = manager.login(login_request=LoginRequest(username="admin", password="x", scope=["a"]))
    assert AccessToken.decode(result["access_token"]).scope == ["a"]
    with pytest.raises(TokenError, match="forbidden"):
        manager.login(login_request=LoginRequest(username="admin", password="x", scope=["c"]))


def test_auth_manager_refresh_rejects_wrong_realm_and_invalid_subject() -> None:
    storage = TokenStorageMemory()
    token = RefreshToken.create(subject_id=7, subject_type="user", username="user")
    storage.put(token)
    admin_manager = AuthManager(auth_service=StubAuthService(), token_storage=storage, subject_type="admin")
    with pytest.raises(TokenError, match="subject type"):
        admin_manager.refresh(refresh_request=RefreshRequest(refresh_token=token.token_id))

    storage.clear()
    token = RefreshToken.create(subject_id=7, subject_type="admin", username="admin")
    storage.put(token)
    manager = AuthManager(auth_service=StubAuthService(exists=False), token_storage=storage, subject_type="admin")
    with pytest.raises(UserNotValidError):
        manager.refresh(refresh_request=RefreshRequest(refresh_token=token.token_id))


def test_auth_manager_logout_one_or_all_and_rejects_empty_request() -> None:
    storage = TokenStorageMemory(); manager = AuthManager(auth_service=StubAuthService(), token_storage=storage, subject_type="user")
    one = RefreshToken.create(subject_id=1, subject_type="user", username="user")
    two = RefreshToken.create(subject_id=1, subject_type="user", username="user")
    storage.put(one); storage.put(two)
    manager.logout(logout_request=LogoutRequest(refresh_token=one.token_id))
    assert storage.count() == 1
    manager.logout(logout_request=LogoutRequest(username="user"))
    assert storage.get(two.token_id).revoked is True
    with pytest.raises(TokenError):
        manager.logout(logout_request=LogoutRequest())


def test_admin_auth_service_success_wrong_password_and_disabled() -> None:
    uow = FakeUnitOfWork()
    admin = Admin.create(employee_id=10, first_name="Admin", login="admin", password="Strong1!")
    uow.admins.save(admin)
    service = AdminAuthService(uow)
    auth = service.authenticate_user(LoginRequest(username="admin", password="Strong1!"))
    assert auth.id == 10 and auth.username == "admin"
    with pytest.raises(InvalidCredentialsError):
        service.authenticate_user(LoginRequest(username="admin", password="wrong"))
    admin.disable()
    assert service.validate_user_exists(LoginRequest(username="admin")) is False


def test_user_auth_service_checks_client_and_password() -> None:
    uow = FakeUnitOfWork()
    client = Client.create(client_id=100, name="Acme")
    user = User.create(employee_id=20, first_name="User", client_id=100, login="user", password="Strong1!")
    uow.clients.save(client); uow.users.save(user)
    service = UserAuthService(uow)
    auth = service.authenticate_user(LoginRequest(username="user", password="Strong1!"))
    assert auth.id == 20
    client.disable()
    with pytest.raises(InvalidCredentialsError):
        service.authenticate_user(LoginRequest(username="user", password="Strong1!"))
    assert service.validate_user_exists(LoginRequest(username="user")) is False
