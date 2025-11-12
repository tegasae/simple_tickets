import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt
from pydantic import BaseModel, Field

from src.web.dependicies_auth import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS


class AccessToken(BaseModel):
    # ✅ REQUIRED: Subject (user identifier)
    sub: str
    # ✅ REQUIRED: Expiration time
    exp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    # ✅ REQUIRED: Issued at
    iat: datetime = Field(default_factory=datetime.now(timezone.utc))
    # ✅ RECOMMENDED: Issuer (your app)
    iss: str = ""
    # ✅ RECOMMENDED: Audience (who token is for)
    aud: str = ""
    # ✅ OPTIONAL: Token ID (unique identifier)
    jti: str = ""
    # ✅ OPTIONAL: Scopes (what user can do)
    scope: str = ""

    def encode(self):
        payload = {
            key: value for key, value in self.dict().items()
            if value not in [None, ""]  # Remove empty fields
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @classmethod
    def decode(cls, token: str) -> 'AccessToken':
        """Decode JWT back to AccessToken instance"""
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )
            return cls(**payload)
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")


class RefreshToken(BaseModel):
    token_id: Field(default_factory=lambda: secrets.token_urlsafe(32))
    username: str
    user_id: int
    # ✅ REQUIRED: Timing information
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    # ✅ REQUIRED: Usage tracking
    used: bool = False
    last_used_at: Optional[datetime] = None
    use_count: int = 0
    # ✅ RECOMMENDED: Security context
    client_id: str = ""


class JWTToken(BaseModel):
    access_token: AccessToken
    refresh_id: str
    scopes: str

    def encode(self):
        current_time = datetime.now(timezone.utc)
        expires_in = int((self.access_token.exp - current_time).total_seconds())
        return {"access_token": self.access_token.encode(),
                "token_type": "bearer",
                "scope": self.access_token.scope,
                "expires_in": max(expires_in, 0),  # Ensure non-negative
                "refresh_token": self.refresh_id  # Standard field name
                }
