from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.domain.admin_empty import AdminEmpty
from src.services.service_layer.admins import AdminService
from src.services.service_layer.factory import ServiceFactory
from src.web import settings
from src.web.auth.exceptions import UserNotValidError
from src.web.auth.models import UserAuth
from src.web.auth.services import AuthManager, AuthServiceAbstract
from src.web.auth.storage import TokenStorageMemory, TokenStorage
from src.web.dependicies.dependencies import get_service_factory

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scopes={
    "read": "Read access to user data",
    "write": "Write access to user data",
    "admin": "Administrator access"
})


class AuthService(AuthServiceAbstract):
    def __init__(self, admin_service: AdminService):
        self.admin_service = admin_service

    def authenticate_user(self, username: str, password: str) -> UserAuth:
        """Authenticate user credentials"""
        admin = self.admin_service.execute('get_by_name', name=username)

        if (admin and
                not isinstance(admin, AdminEmpty) and
                admin.verify_password(password=password) and
                admin.enabled):
            return UserAuth(id=admin.admin_id, username=admin.name, scopes=[])
        else:
            raise UserNotValidError(username)

    def validate_user_exists(self, username: str) -> bool:
        """Validate user exists and is enabled"""
        admin = self.admin_service.execute('get_by_name', name=username)

        if not admin or isinstance(admin, AdminEmpty) or not admin.enabled:
            return False

        return True


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


def get_auth_service_abstract(sf: ServiceFactory = Depends(get_service_factory)) -> AuthServiceAbstract:
    return AuthService(admin_service=sf.get_admin_service())


def get_auth_manager(
        auth_service_abstract: AuthServiceAbstract = Depends(get_auth_service_abstract),
        token_storage: TokenStorage = Depends(get_token_storage)
) -> AuthManager:
    return AuthManager(auth_service_abstract=auth_service_abstract, token_storage=token_storage)


def get_current_user_new(token: str = Depends(oauth2_scheme), auth_manager: AuthManager = Depends(get_auth_manager)) \
        -> str:
    """Dependency for getting current user from access token"""
    return auth_manager.token_service.verify_access_token(token)
