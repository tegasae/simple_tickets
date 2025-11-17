from typing import Annotated


from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jwt import InvalidTokenError
from pydantic import BaseModel

from starlette import status

from src.domain.model import AdminEmpty
from src.services.service_layer.factory import ServiceFactory
from src.web.auth.storage import TokenStorageMemory, TokenNotFoundError
from src.web.auth.tokens import AccessToken, RefreshToken, JWTToken
from src.web.dependencies import get_service_factory

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token",scopes={
        "read": "Read access to user data",
        "write": "Write access to user data",
        "admin": "Administrator access"
    })



class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserVerifier:
    def __init__(self, sf: ServiceFactory = Depends(get_service_factory)):
        self.admin_service = sf.get_admin_service()
        self.credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        self.admin = AdminEmpty()
        self.token_storage = TokenStorageMemory()

    def authenticate(self, username: str, password: str,scope:list[str]) -> dict:
        admin = self.admin_service.execute('get_by_name', name=username)
        self.admin = admin

        # Check if admin exists and credentials are valid
        if (admin and
                not isinstance(admin, AdminEmpty) and
                admin.verify_password(password=password) and
                admin.enabled):

            access_token=AccessToken(sub=admin.name,scope=scope)
            refresh_token = RefreshToken(user_id=admin.admin_id,username=admin.name,scope=access_token.scope.copy())
            self.token_storage.put(refresh_token=refresh_token)
            jwt_token=JWTToken(access_token=access_token,refresh_token=refresh_token)
            return jwt_token.encode()
        else:
            raise self.credentials_exception

    def renew_all_tokens(self,token_id:str) -> dict:
        try:
            refresh_token_old=self.token_storage.get(token_id=token_id)
            #self.token_storage.delete(token_id=token_id)
            admin = self.admin_service.execute('get_by_name', name=refresh_token_old.username)
            self.admin = admin

            # Check if admin exists and credentials are valid
            if (admin and
                    not isinstance(admin, AdminEmpty) and
                    admin.enabled):
                access_token = AccessToken(sub=admin.name, scope=refresh_token_old.scope)
                refresh_token_new = RefreshToken(user_id=admin.admin_id, username=admin.name,scope=refresh_token_old.scope.copy())
                self.token_storage.put(refresh_token=refresh_token_new)
                jwt_token = JWTToken(access_token=access_token, refresh_token=refresh_token_new)
                return jwt_token.encode()
            else:
                raise self.credentials_exception
        except TokenNotFoundError:
            raise self.credentials_exception

    def verify_refresh_token(self, token_id: str)->bool:
        try:

            refresh_token = self.token_storage.get(token_id=token_id)
            if not refresh_token.is_valid():
                raise self.credentials_exception
            # Check external storage
            return True
        except (InvalidTokenError,TokenNotFoundError):
            return False



    def verify_access_token(self, token: Annotated[str, Depends(oauth2_scheme)]):
        try:
            access_token=AccessToken.decode(token=token)
            if not access_token.is_valid():
                raise self.credentials_exception
            admin = self.admin_service.execute('get_by_name', name=access_token.sub)

            # Check if admin exists and is valid
            if not admin or isinstance(admin, AdminEmpty):
                raise self.credentials_exception
            return admin.name
        except InvalidTokenError:
            raise self.credentials_exception
        except Exception as e:
            # Log the actual error for debugging
            print(f"Token validation error: {e}")
            raise self.credentials_exception

    def revoke_refresh_token(self, token_id:str):
        try:
            self.token_storage.delete(token_id=token_id)
        except TokenNotFoundError:
            raise self.credentials_exception
        except Exception as e:
            # Log the actual error for debugging
            raise self.credentials_exception

    def revoke_user_tokens(self,username: str):
        try:
            self.token_storage.revoke_user_tokens(username=username)
        except TokenNotFoundError:
            raise self.credentials_exception

# Dependency to create UserVerifier instance
async def get_user_verifier(sf: ServiceFactory = Depends(get_service_factory)):
    return UserVerifier(sf)


async def get_current_user(
        security_scopes: SecurityScopes,
        token: Annotated[str, Depends(oauth2_scheme)],
        user_verifier: UserVerifier = Depends(get_user_verifier)
):
    """Get current user from token - simplified version"""
    
    return user_verifier.verify_access_token(token=token)
