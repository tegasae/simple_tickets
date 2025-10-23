from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pydantic import BaseModel
from starlette import status

from src.domain.model import AdminEmpty, Admin
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

def unauthorized():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},

    )




def create_access_token(data: dict, expires_delta: timedelta = 0):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def check_login(sf: ServiceFactory = Depends(get_service_factory),
                credentials_exception:HTTPException=Depends(unauthorized)):
    admin_service = sf.get_admin_service()
    admin = admin_service.execute('get_by_name', name=username)
    if admin.verify_password(password=password) and admin.enabled:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": admin.name}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")
    else:
        raise credentials_exception

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           sf: ServiceFactory = Depends(get_service_factory), credentials_exception:HTTPException=Depends(unauthorized)):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    admin_service = sf.get_admin_service()
    admin = admin_service.execute('get_by_name', name=username)
    if admin is AdminEmpty:
        raise credentials_exception
    return admin
