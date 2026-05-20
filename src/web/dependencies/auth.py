from datetime import datetime, timedelta, timezone
import os
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer


JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


admin_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth_old/admin/login",
    scheme_name="AdminAuth",
)

user_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth_old/user/login",
    scheme_name="UserAuth",
)


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


async def get_current_user(
    request: Request,

) -> dict:
    """Authenticate user and store username in request"""

    request.state.current_user = {"username": "1"}
    print("1234")
    return {"username": "1"}
