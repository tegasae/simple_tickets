from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pydantic import BaseModel
from starlette import status

from src.domain.model import AdminEmpty
from src.services.service_layer.factory import ServiceFactory
from dependicies import get_service_factory

ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserVerifier:
    def __init__(self, sf: ServiceFactory = Depends(get_service_factory)):
        self.admin_service=sf.get_admin_service()
        self.credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        self.admin = AdminEmpty()

    def authenticate(self, username: str, password: str):
        admin = self.admin_service.execute('get_by_name', name=username)
        self.admin = admin
        if admin.verify_password(password=password) and admin.enabled:
            return self.create_access_token(expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        else:
            raise self.credentials_exception

    def create_access_token(self, expires_delta: timedelta = 0):
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        encoded_jwt = jwt.encode({"sub": self.admin.name, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
        return Token(access_token=encoded_jwt, token_type="bearer")

    def check(self, token: Annotated[str, Depends(oauth2_scheme)]):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            expires=payload.get("exp")
            if (datetime.fromtimestamp(expires) - timedelta(minutes=30) > datetime.now()
                    or not username):
                raise self.credentials_exception
            TokenData(username=username)
            admin = self.admin_service.execute('get_by_name', name=username)
            if admin is AdminEmpty:
                raise self.credentials_exception
        except InvalidTokenError:
            raise self.credentials_exception
        except Exception:
            raise self.credentials_exception
        return admin


# Dependency to create UserVerifier instance
def get_user_verifier(sf: ServiceFactory = Depends(get_service_factory)):
    return UserVerifier(sf)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           sf: ServiceFactory = Depends(get_service_factory)):
    return UserVerifier(sf).check(token=token)
