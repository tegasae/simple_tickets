from datetime import datetime, timedelta, timezone
import os
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status, Request


from src.services.uow.uow import UnitOfWork
from src.web.auth.services.auth_service import AdminAuthService, UserAuthService
from src.web.auth.services.services import AuthManager, TokenService
from src.web.auth.storage import TokenStorageMemory
from src.web.dependencies.scheme import admin_oauth2_scheme, user_oauth2_scheme
from src.web.dependencies.services import get_uow

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))




def create_access_token(*, subject_id: int, subject_type: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(subject_id),
        "subject_type": subject_type,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if "sub" not in payload or "subject_type" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def get_current_admin_principal(
    token: str = Depends(admin_oauth2_scheme),
) -> dict[str, Any]:
    return decode_token(token)


def get_current_user_principal(
    token: str = Depends(user_oauth2_scheme),
) -> dict[str, Any]:
    return decode_token(token)


def require_current_admin(
    payload=Depends(get_current_admin_principal),
) -> int:
    if payload.get("subject_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return int(payload["sub"])


def require_current_user(
    payload=Depends(get_current_user_principal),
) -> int:
    if payload.get("subject_type") != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required",
        )

    return int(payload["sub"])

#######
def get_auth_manager_admin(uow: UnitOfWork = Depends(get_uow)) -> AuthManager:
    return AuthManager(auth_service=AdminAuthService(uow=uow), token_storage=TokenStorageMemory(),subject_type="admin")


def get_auth_manager_user(uow: UnitOfWork = Depends(get_uow)) -> AuthManager:
    return AuthManager(auth_service=UserAuthService(uow=uow), token_storage=TokenStorageMemory(),subject_type="user")



#

async def get_current_admin(
    request: Request,
    token: str = Depends(admin_oauth2_scheme)
) -> dict:
    """Authenticate user and store username in request"""
    access_token = TokenService.verify_access_token(token)
    request.state.current_user_id = {"user_id": access_token.get_admin_id()}
    return {"user_id": request.state.current_user_id}


async def get_current_user(
    request: Request,
    token: str = Depends(user_oauth2_scheme)
) -> dict:
    """Authenticate user and store username in request"""
    access_token = TokenService.verify_access_token(token)
    request.state.current_user_id = {"user_id": access_token.get_user_id()}
    return {"user_id": request.state.current_user_id}


async def get_user_id_from_request(request: Request) -> int:

    user_id = request.state.current_user_id  # ← Extract from request
    return user_id


