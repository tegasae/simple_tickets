from typing import Any

from src.domain.repositories.refresh_session_repository import RefreshSession, SubjectType
from src.domain.uow.unit_of_work import UnitOfWork
from src.web.auth import tokens
from src.web.auth.exceptions import TokenError, TokenNotFoundError
from src.web.auth.models import LoginRequest, LogoutRequest, RefreshRequest
from src.web.auth.services.auth_service import AuthServiceAbstract
from src.web.auth.services.services import AuthManager, TokenService
from src.web.config import Settings


class SharedSessionAuthManager:
    """Issue, rotate and revoke refresh sessions through the business UoW."""

    def __init__(
        self, *, uow: UnitOfWork, auth_service: AuthServiceAbstract,
        subject_type: SubjectType, settings: Settings,
    ) -> None:
        self.uow = uow
        self.auth_service = auth_service
        self.subject_type = subject_type
        self.settings = settings

    def login(self, *, login_request: LoginRequest) -> dict[str, Any]:
        with self.uow:
            user = self.auth_service.authenticate_user(login_request, for_session=True)
            scope = AuthManager._resolve_scope(
                allowed_scope=user.scope, requested_scope=login_request.scope,
            )
            pair = tokens.JWTToken.create(
                settings=self.settings, username=user.username, subject_id=user.id,
                subject_type=self.subject_type, scope=scope,
            )
            credential = pair.refresh_token
            session = RefreshSession(
                account_id=user.account_id, subject_id=user.id, subject_type=self.subject_type,
                username=user.username, created_at=credential.created_at,
                expires_at=credential.expires_at, scope=tuple(scope),
            )
            response = self._encode(pair, session)
            self.uow.refresh_sessions.remove_expired(now=tokens.utcnow())
            self.uow.refresh_sessions.add(credential.token_hash, session)
            return response

    def refresh(self, *, refresh_request: RefreshRequest) -> dict[str, Any]:
        with self.uow:
            previous_hash = tokens.hash_token(refresh_request.refresh_token)
            session = self._get(previous_hash)
            if session.expires_at <= tokens.utcnow():
                raise TokenError("Invalid refresh session")
            if not self.auth_service.validate_user_exists(
                LoginRequest(username=session.username),
                expected_subject_id=session.subject_id,
                expected_account_id=session.account_id,
                for_session=True,
            ):
                raise TokenError("Invalid refresh session")

            pair = tokens.JWTToken.create(
                settings=self.settings, username=session.username, subject_id=session.subject_id,
                subject_type=session.subject_type, scope=list(session.scope),
            )
            response = self._encode(pair, session)
            if not self.uow.refresh_sessions.remove(previous_hash):
                raise TokenNotFoundError()
            self.uow.refresh_sessions.add(pair.refresh_token.token_hash, session)
            return response

    def logout(self, *, logout_request: LogoutRequest, access_token: str | None = None) -> None:
        with self.uow:
            if logout_request.refresh_token:
                token_hash = tokens.hash_token(logout_request.refresh_token)
                self._get(token_hash)
                if not self.uow.refresh_sessions.remove(token_hash):
                    raise TokenNotFoundError()
                return

            if not logout_request.username or access_token is None:
                raise TokenError("Refresh token or authenticated username is required")

            principal = TokenService.verify_access_token(access_token, settings=self.settings)
            subject_id = (
                principal.get_admin_id() if self.subject_type == "admin" else principal.get_user_id()
            )
            # A different username is a scoped no-op. The touch inside this check
            # also serializes logout-all against issuance and rotation.
            if self.auth_service.validate_user_exists(
                LoginRequest(username=logout_request.username),
                expected_subject_id=subject_id,
                for_session=True,
            ):
                self.uow.refresh_sessions.revoke_subject(
                    subject_type=self.subject_type, subject_id=subject_id,
                )

    def _get(self, token_hash: str) -> RefreshSession:
        session = self.uow.refresh_sessions.get(token_hash)
        if session is None or session.subject_type != self.subject_type:
            raise TokenNotFoundError()
        return session

    def _encode(self, pair: tokens.JWTToken, session: RefreshSession) -> dict[str, Any]:
        if session.expires_at <= tokens.utcnow():
            raise TokenError("Invalid refresh session")
        pair.access_token.exp = min(pair.access_token.exp, session.expires_at)
        return pair.encode(settings=self.settings)
