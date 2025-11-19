from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.services.service_layer.admins import AdminService
from src.services.service_layer.factory import ServiceFactory
from src.web import settings
from src.web.auth.services import AuthService, TokenService, AuthManager
from src.web.auth.storage import TokenStorageMemory, TokenStorage
from src.web.dependencies import get_service_factory

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scopes={
    "read": "Read access to user data",
    "write": "Write access to user data",
    "admin": "Administrator access"
})


def get_token_storage() -> TokenStorage:
    """Factory function to create token storage based on configuration"""
    try:
        storage_type = settings.token_storage_type
        # if storage_type == "redis":
        #    return TokenStorageRedis(redis_url=settings.redis_url)
        # elif storage_type == "database":
        #    return TokenStorageDatabase(database_url=settings.database_url)
        if storage_type == 'memory':
            return TokenStorageMemory()
        else:  # memory (default)
            return TokenStorageMemory()
    except:
        return TokenStorageMemory()


def get_admin_service(sf: ServiceFactory = Depends(get_service_factory)) -> AdminService:
    return sf.get_admin_service()


def get_auth_manager(
        admin_service: AdminService = Depends(get_admin_service),
        token_storage: TokenStorage = Depends(get_token_storage)
) -> AuthManager:
    return AuthManager(admin_service, token_storage=token_storage)


def get_current_user_new(token: str = Depends(oauth2_scheme), auth_manager: AuthManager = Depends(get_auth_manager)) \
        -> str:
    """Dependency for getting current user from access token"""
    return auth_manager.token_service.verify_access_token(token)
