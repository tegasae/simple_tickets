from abc import ABC, abstractmethod

from jwt import InvalidTokenError

from src.web.auth.models import UserAuth
from src.web.auth.storage import TokenStorage
from src.web.auth.exceptions import TokenNotFoundError, TokenExpiredError, TokenError, UserNotValidError
from src.web.auth.tokens import AccessToken, RefreshToken, JWTToken


class TokenService:
    def __init__(self, token_storage: TokenStorage):
        self.token_storage = token_storage

    def create_token_pair(self, username: str, user_id: int, scope: list[str]) -> dict:
        """Create new access + refresh token pair"""
        access_token = AccessToken(sub=username, scope=scope)
        refresh_token = RefreshToken(user_id=user_id, username=username, scope=scope.copy())

        self.token_storage.put(refresh_token)

        jwt_token = JWTToken(access_token=access_token, refresh_token=refresh_token)
        return jwt_token.encode()

    def renew_tokens(self, old_token_id: str) -> dict:
        """Create new tokens using refresh token"""
        try:
            old_refresh_token = self.token_storage.get(old_token_id)
            self.token_storage.delete(old_token_id)  # Invalidate old token

            # Create new tokens with same scope
            return self.create_token_pair(
                username=old_refresh_token.username,
                user_id=old_refresh_token.user_id,
                scope=old_refresh_token.scope
            )
        except TokenNotFoundError:
            raise

    @staticmethod
    def verify_access_token(token: str) -> str:
        """Verify access token and return username"""
        try:
            access_token = AccessToken.decode(token=token)
            if not access_token.is_valid():
                raise TokenExpiredError(token)
            return access_token.sub
        except Exception:
            raise TokenError(token)

    def verify_refresh_token(self, token_id: str) -> bool:
        """Verify refresh token validity"""
        try:
            refresh_token = self.token_storage.get(token_id)
            if not refresh_token.is_valid():
                return False
            return refresh_token.is_valid()
        except (InvalidTokenError, TokenNotFoundError):
            return False

    def revoke_tokens(self, token_id: str = None, username: str = None):
        """Revoke tokens by ID or user"""
        if token_id:
            self.token_storage.delete(token_id)
        elif username:
            self.token_storage.revoke_user_tokens(username)


class AuthServiceAbstract(ABC):

    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> UserAuth:
        raise NotImplementedError

    @abstractmethod
    def validate_user_exists(self, username: str) -> bool:
        raise NotImplementedError


class AuthManager:
    def __init__(
            self,
            auth_service_abstract: AuthServiceAbstract,
            token_storage: TokenStorage
    ):
        self.token_storage = token_storage
        self.auth_service_abstract = auth_service_abstract
        # self.auth_service = AuthService(admin_service=admin_service)
        self.token_service = TokenService(token_storage=token_storage)

    def login(self, username: str, password: str, scope: list[str]) -> dict:
        """Complete login flow"""
        user_auth = self.auth_service_abstract.authenticate_user(username, password)
        ###check scope later
        return self.token_service.create_token_pair(user_auth.name, user_auth.admin_id, user_auth.scope)

    def refresh(self, refresh_token_id: str) -> dict:
        """Complete token refresh flow"""
        refresh_token = self.token_storage.get(token_id=refresh_token_id)
        if self.auth_service_abstract.validate_user_exists(refresh_token.username):
            raise UserNotValidError(user=refresh_token.username)
        if not self.token_service.verify_refresh_token(refresh_token_id):
            raise TokenError(refresh_token_id)
        return self.token_service.renew_tokens(refresh_token_id)

    def logout(self, refresh_token_id: str = None, username: str = None):
        """Logout by revoking tokens"""
        self.token_service.revoke_tokens(token_id=refresh_token_id, username=username)
