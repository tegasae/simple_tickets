from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from src.services.service_layer.admins import AdminService
from src.services.service_layer.factory import ServiceFactory
from src.web.auth.service import AuthService, TokenService, AuthManager
from src.web.dependencies import get_service_factory

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scopes={
    "read": "Read access to user data",
    "write": "Write access to user data",
    "admin": "Administrator access"
})


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    scope: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str
    scope: Optional[list[str]] = None


def get_token_service() -> TokenService:
    return TokenService()


def get_admin_service(sf: ServiceFactory = Depends(get_service_factory)) -> AdminService:
    return sf.get_admin_service()


def get_auth_service(admin_service: AdminService = Depends(get_admin_service)) -> AuthService:
    return AuthService(admin_service)


def get_auth_manager(
        auth_service: AuthService = Depends(get_auth_service),
        token_service: TokenService = Depends(get_token_service)
) -> AuthManager:
    return AuthManager(auth_service, token_service)


def get_current_user_new(token: str = Depends(oauth2_scheme), auth_manager: AuthManager = Depends(get_auth_manager)) \
        -> str:
    """Dependency for getting current user from access token"""
    return auth_manager.token_service.verify_access_token(token)
