from typing import Optional

from pydantic import BaseModel, Field


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


class UserAuth(BaseModel):
    id: int = 0
    username: str
    scope: Optional[list[str]] = Field(default_factory=list)
