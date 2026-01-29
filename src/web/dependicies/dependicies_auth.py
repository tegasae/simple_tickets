

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from src.domain.exceptions import ItemNotFoundError
from src.services.service_layer.admins import AdminService
from src.services.service_layer.factory import ServiceFactory
from src.services.uow.uowsqlite import SqliteUnitOfWork
from src.web import settings
from src.web.auth.exceptions import UserNotValidError
from src.web.auth.models import UserAuth
from src.web.auth.services import AuthManager, AuthServiceAbstract, TokenService
from src.web.auth.storage import TokenStorageMemory, TokenStorage
from src.web.dependicies.dependencies import get_service_factory, get_uow

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
        try:
            admin = self.admin_service.get_admin_by_name(name=username)
            if admin.enabled and admin.verify_password(password=password):
                return UserAuth(id=admin.admin_id, username=admin.name, scope=[])
        except ItemNotFoundError:
            raise UserNotValidError(username)
        else:
            raise UserNotValidError(username)

    def validate_user_exists(self, username: str) -> bool:
        """Validate user exists and is enabled"""
        try:
            admin = self.admin_service.get_admin_by_name(name=username)
            if admin.enabled:
                return True
        except ItemNotFoundError(item_name=username):
            return False

        return False


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


def get_service_factory_admin_name(uow: SqliteUnitOfWork = Depends(get_uow),admin_name:str=Depends(get_current_user_new)):
    return ServiceFactory(uow=uow,admin_name=admin_name)



def get_service_factory_admin_name_new(token: str = Depends(oauth2_scheme), uow: SqliteUnitOfWork = Depends(get_uow)):
    username=TokenService.verify_access_token(token)
    return ServiceFactory(uow=uow,admin_name=username)



async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> dict:
    """Authenticate user and store username in request"""
    username = TokenService.verify_access_token(token)
    request.state.current_user = {"username": username}
    return {"username": username}



def get_current_username(request: Request) -> str:
    return request.state.current_user["username"]


async def get_service_factory_auth(
    request: Request,  # ← Get request to extract username
    uow: SqliteUnitOfWork = Depends(get_uow)
) -> ServiceFactory:
    """
    Creates ServiceFactory with authenticated username
    """
    username = get_current_username(request)  # ← Extract from request
    return ServiceFactory(uow=uow, admin_name=username)  # ← Pass to factory



#def get_current_user_id(token: str = Depends(oauth2_scheme), auth_manager: AuthManager = Depends(get_auth_manager)) \
#        -> int:
#    """Dependency for getting current user from access token"""
#    return auth_manager.auth_service_abstract
