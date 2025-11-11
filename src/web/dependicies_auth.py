import secrets

from datetime import timedelta, datetime, timezone
from typing import Annotated, Dict, Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pydantic import BaseModel
from starlette import status

from src.domain.model import AdminEmpty
from src.services.service_layer.factory import ServiceFactory
from src.web.dependencies import get_service_factory

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 1
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None  # Add refresh token


class TokenRefresh(BaseModel):
    token_id: str
    username: str
    expires_at: datetime


class TokenData(BaseModel):
    username: str | None = None


class TokenStorage:
    _instance = None
    #_lock = Lock()

    def __init__(self):
        self._refresh_tokens = {}

    def __new__(cls, *args, **kwargs):
        #with cls._lock:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def store_refresh_token(self, refresh_token: TokenRefresh):
        self._refresh_tokens[refresh_token.token_id] = refresh_token
        self._refresh_tokens["used"] = False

    def is_valid_refresh_token(self, token_id: str) -> bool:
        refresh_token = self._refresh_tokens.get(token_id)
        return (refresh_token and
                not refresh_token["used"] and
                refresh_token["expires_at"] > datetime.now(timezone.utc))

    def mark_token_used(self, token_id: str):
        if token_id in self._refresh_tokens:
            self._refresh_tokens[token_id]["used"] = True


class UserVerifier:
    def __init__(self, sf: ServiceFactory = Depends(get_service_factory)):
        self.admin_service = sf.get_admin_service()
        self.credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        self.admin = AdminEmpty()
        self.token_storage = TokenStorage()

    def authenticate(self, username: str, password: str):
        admin = self.admin_service.execute('get_by_name', name=username)
        self.admin = admin

        # Check if admin exists and credentials are valid
        if (admin and
                not isinstance(admin, AdminEmpty) and
                admin.verify_password(password=password) and
                admin.enabled):
            refresh_token = self.create_refresh_token(admin.name)
            access_token = self.create_access_token(expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

            return self.create_access_token(expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        else:
            raise self.credentials_exception

    def create_access_token(self, expires_delta: timedelta | None = None):
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        to_encode = {"sub": self.admin.name, "exp": expire}
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return Token(access_token=encoded_jwt, token_type="bearer")

    def create_refresh_token(self, username: str) -> str:
        refresh_token_id = secrets.token_urlsafe(32)
        refresh_token = TokenRefresh(token_id=refresh_token_id, username=username,
                                     expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
        # Store in external storage
        self.token_storage.store_refresh_token(refresh_token=refresh_token)

        to_encode = {
            "sub": username,
            "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "type": "refresh",
            "jti": refresh_token_id
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def verify_refresh_token(self, refresh_token: str) -> str:
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            token_id = payload.get("jti")

            # Check external storage
            if not self.token_storage.is_valid_refresh_token(token_id):
                raise self.credentials_exception

            # Mark as used in external storage
            self.token_storage.mark_token_used(token_id)

            return payload.get("sub")
        except InvalidTokenError:
            raise self.credentials_exception

    def check(self, token: Annotated[str, Depends(oauth2_scheme)]):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            expires: int = payload.get("exp")

            # Check if token is expired or username is missing
            if not username or datetime.fromtimestamp(expires, tz=timezone.utc) < datetime.now(timezone.utc):
                raise self.credentials_exception

            # Validate token data
            token_data = TokenData(username=username)

            # Get admin from database
            admin = self.admin_service.execute('get_by_name', name=token_data.username)

            # Check if admin exists and is valid
            if not admin or isinstance(admin, AdminEmpty):
                raise self.credentials_exception

        except InvalidTokenError:
            raise self.credentials_exception
        except Exception as e:
            # Log the actual error for debugging
            print(f"Token validation error: {e}")
            raise self.credentials_exception

        return admin


# Dependency to create UserVerifier instance
async def get_user_verifier(sf: ServiceFactory = Depends(get_service_factory)):
    return UserVerifier(sf)


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        user_verifier: UserVerifier = Depends(get_user_verifier)
):
    """Get current user from token - simplified version"""
    return user_verifier.check(token=token)
