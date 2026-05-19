from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

JWT_SECRET = "change-me"
JWT_ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_current_principal(
    token: str = Depends(oauth2_scheme),
) -> dict:
    payload = decode_token(token)

    if "sub" not in payload or "subject_type" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return payload


def require_current_admin(
    payload: dict = Depends(get_current_principal),
) -> int:
    if payload["subject_type"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return int(payload["sub"])


def require_current_user(
    payload: dict = Depends(get_current_principal),
) -> int:
    if payload["subject_type"] != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required",
        )

    return int(payload["sub"])