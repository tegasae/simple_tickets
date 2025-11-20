from typing import Optional

from pydantic import BaseModel


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    scope: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str
    scope: Optional[list[str]] = None
