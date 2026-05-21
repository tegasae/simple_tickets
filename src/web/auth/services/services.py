

from src.web.auth.exceptions import (
    TokenError,
    TokenNotFoundError,
    TokenExpiredError,
    UserNotValidError,
)
from src.web.auth.models import LoginRequest, RefreshRequest, LogoutRequest
from src.web.auth.services.auth_service import AuthServiceAbstract
from src.web.auth.storage import TokenStorage
from src.web.auth.tokens import AccessToken, JWTToken, SubjectType


class TokenService:
    """
    Service responsible for token issuing, verification, refresh and revocation.

    Model:
        - AccessToken is JWT.
        - RefreshToken is opaque token.
        - AccessToken.sub contains subject_id as string.
        - AccessToken.subject_type contains "admin" or "user".
    """

    def __init__(self, token_storage: TokenStorage):
        self.token_storage = token_storage

    def create_token_pair(
        self,
        *,
        username: str,
        subject_id: int,
        subject_type: SubjectType,
        scope: list[str] | None = None,
    ) -> dict:
        """
        Create new access + refresh token pair.

        Returns OAuth2-like response:

            {
                "access_token": "...",
                "refresh_token": "...",
                "token_type": "bearer",
                "expires_in": 3600,
                "scope": "..."
            }
        """
        token_pair = JWTToken.create(
            subject_id=subject_id,
            subject_type=subject_type,
            username=username,
            scope=scope or [],
        )

        self.token_storage.put(token_pair.refresh_token)

        return token_pair.encode()

    def renew_tokens(self, old_refresh_token_id: str) -> dict:
        """
        Create a new token pair using an existing refresh token.

        This implements refresh-token rotation:
            - validate old refresh token;
            - delete/revoke old refresh token;
            - issue new access + refresh token pair.
        """
        old_refresh_token = self.token_storage.get(old_refresh_token_id)

        if not old_refresh_token.is_valid():
            raise TokenError("Invalid refresh token")

        self.token_storage.delete(old_refresh_token_id)

        return self.create_token_pair(
            username=old_refresh_token.username,
            subject_id=old_refresh_token.subject_id,
            subject_type=old_refresh_token.subject_type,
            scope=old_refresh_token.scope,
        )

    @staticmethod
    def verify_access_token(token: str) -> AccessToken:
        """
        Verify JWT access token and return decoded AccessToken object.
        """
        try:
            access_token = AccessToken.decode(token)

            if not access_token.is_valid():
                raise TokenExpiredError()

            return access_token

        except TokenError:
            raise

        except Exception as exc:
            raise TokenError("Failed to verify access token") from exc

    def verify_refresh_token(self, refresh_token_id: str) -> bool:
        """
        Verify refresh token existence and validity.
        """
        try:
            refresh_token = self.token_storage.get(refresh_token_id)
            return refresh_token.is_valid()

        except TokenNotFoundError:
            return False

    def revoke_token(self, refresh_token_id: str) -> None:
        """
        Revoke one refresh token.
        """
        self.token_storage.delete(refresh_token_id)

    def revoke_user_tokens(self, username: str) -> None:
        """
        Revoke all refresh tokens belonging to one username.
        """
        self.token_storage.revoke_user_tokens(username)




class AuthManager:
    """
    High-level authentication manager.

    One AuthManager instance should be created for admin realm.
    Another AuthManager instance should be created for user realm.

    Example:

        admin_auth_manager = AuthManager(
            auth_service=AdminAuthService(...),
            token_storage=token_storage,
            subject_type="admin",
        )

        user_auth_manager = AuthManager(
            auth_service=UserAuthService(...),
            token_storage=token_storage,
            subject_type="user",
        )
    """

    def __init__(
        self,
        *,
        auth_service: AuthServiceAbstract,
        token_storage: TokenStorage,
        subject_type: SubjectType,
    ):
        self.auth_service = auth_service
        self.token_storage = token_storage
        self.subject_type = subject_type
        self.token_service = TokenService(token_storage=token_storage)

    def login(
        self,
        *,
        login_request:LoginRequest,
    ) -> dict:
        """
        Complete login flow.

        Important:
            Do not blindly issue requested_scope.
            Issue only scopes allowed for authenticated subject.
        """
        user_auth = self.auth_service.authenticate_user(
            login_request=login_request
        )

        issued_scope = self._resolve_scope(
            allowed_scope=user_auth.scope,
            requested_scope=login_request.scope,
        )

        return self.token_service.create_token_pair(
            username=user_auth.username,
            subject_id=user_auth.id,
            subject_type=self.subject_type,
            scope=issued_scope,
        )

    def refresh(
        self,
        *,
        refresh_request:RefreshRequest,
    ) -> dict:
        """
        Complete refresh flow.

        Checks:
            - refresh token exists;
            - refresh token is valid;
            - user/admin still exists;
            - refresh token belongs to the same subject_type as this AuthManager.
        """
        refresh_token = self.token_storage.get(refresh_request.refresh_token)

        if refresh_token.subject_type != self.subject_type:
            raise TokenError("Refresh token subject type mismatch")

        if not refresh_token.is_valid():
            raise TokenError("Invalid refresh token")

        if not self.auth_service.validate_user_exists(login_request=LoginRequest(username=refresh_token.username)):
            raise UserNotValidError(username=refresh_token.username)

        return self.token_service.renew_tokens(refresh_request.refresh_token)

    def logout(
        self,
        *,
        logout_request:LogoutRequest
    ) -> None:
        """
        Logout by revoking refresh tokens.

        You can revoke:
            - one refresh token by token id;
            - all tokens for username.
        """
        if logout_request.refresh_token:
            self.token_service.revoke_token(logout_request.refresh_token)
            return

        if logout_request.username:
            self.token_service.revoke_user_tokens(logout_request.username)
            return

        raise TokenError("refresh_token_id or username is required")

    @staticmethod
    def _resolve_scope(
        *,
        allowed_scope: list[str],
        requested_scope: list[str] | None,
    ) -> list[str]:
        """
        Resolve requested scopes safely.

        If requested_scope is empty:
            issue all allowed scopes.

        If requested_scope is provided:
            issue only requested scopes that are allowed.

        If requested_scope contains forbidden scope:
            raise TokenError.
        """
        allowed = set(allowed_scope)
        requested = set(requested_scope or [])

        if not requested:
            return list(allowed)

        forbidden = requested - allowed

        if forbidden:
            raise TokenError(
                f"Requested forbidden scopes: {sorted(forbidden)}"
            )

        return list(requested)