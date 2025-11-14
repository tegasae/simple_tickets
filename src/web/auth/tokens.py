import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt
from pydantic import BaseModel, Field

from src.web.config import get_settings


class AccessToken(BaseModel):
    # ✅ REQUIRED: Subject (user identifier)
    sub: str
    # ✅ REQUIRED: Expiration time
    exp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES))
    # ✅ REQUIRED: Issued at
    #iat: datetime = Field(default_factory=datetime.now(timezone.utc))
    iat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # ✅ RECOMMENDED: Issuer (your app)
    iss: str = ""
    # ✅ RECOMMENDED: Audience (who token is for)
    aud: str = ""
    # ✅ OPTIONAL: Token ID (unique identifier)
    jti: str = ""
    # ✅ OPTIONAL: Scopes (what user can do)
    scope: list[str] = []

    def scope2str(self) -> str:
        if not self.scope:
            return ""
        return " ".join(map(str, self.scope))

    @staticmethod
    def str2list(s: str) -> list[str]:
        """Convert space-separated string to scope list"""
        if not s or not s.strip():
            return []
        return [item.strip() for item in s.split(" ") if item.strip()]

    def encode(self) -> str:
        """Encode to JWT string"""
        payload = {}
        model_data = self.model_dump()  # ✅ Fixed method name

        for key, value in model_data.items():
            if key == "scope":
                # Handle scope conversion
                scope_str = self.scope2str()
                if scope_str:
                    payload["scope"] = scope_str
            elif value not in [None, "", []]:  # Include empty lists
                payload[key] = value

        return jwt.encode(payload, get_settings().SECRET_KEY, algorithm=get_settings().ALGORITHM)

    @classmethod
    def decode(cls, token: str) -> 'AccessToken':
        """Decode JWT back to AccessToken instance"""
        try:
            payload = jwt.decode(
                token,
                get_settings().SECRET_KEY,
                algorithms=[get_settings().ALGORITHM]
            )

            # Convert scope string back to list
            if "scope" in payload:
                scope_str = payload.get("scope", "")
                payload["scope"] = cls.str2list(scope_str)

            return cls(**payload)
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")

    def is_valid(self) -> bool:
        """Check if token is valid"""
        if not self.sub:
            return False
        if self.exp < datetime.now(timezone.utc):
            return False
        return True

    def __bool__(self) -> bool:
        """Boolean representation of token validity"""
        return self.is_valid()


class RefreshToken(BaseModel):
    token_id: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    username: str
    user_id: int
    # ✅ REQUIRED: Timing information
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=get_settings().REFRESH_TOKEN_EXPIRE_DAYS)
    )
    # ✅ REQUIRED: Usage tracking
    used: bool = False
    last_used_at: Optional[datetime] = None
    use_count: int = 0
    # ✅ RECOMMENDED: Security context
    client_id: str = ""

    def is_valid(self) -> bool:
        """Check if refresh token is valid"""
        if not self.user_id or not self.username:
            return False

        # ✅ FIXED: Handle None case for last_used_at
        if self.last_used_at and self.last_used_at < datetime.now(timezone.utc):
            return False

        # Check if expired
        if self.expires_at <= datetime.now(timezone.utc):
            return False

        # Check if already used
        if self.used:
            return False

        return True

    def __bool__(self) -> bool:
        """Boolean representation of token validity"""
        return self.is_valid()


class JWTToken(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken

    def encode(self) -> dict:
        """Encode to OAuth2 response format"""
        current_time = datetime.now(timezone.utc)
        expires_in = int((self.access_token.exp - current_time).total_seconds())

        return {
            "access_token": self.access_token.encode(),
            "token_type": "bearer",
            "expires_in": max(expires_in, 0),  # Ensure non-negative
            "refresh_token": self.refresh_token.token_id  # Standard field name
        }

    def is_valid(self) -> bool:
        """Check if both tokens are valid"""
        return bool(self.access_token) and bool(self.refresh_token)

    def __bool__(self) -> bool:
        """Boolean representation of token pair validity"""
        return self.is_valid()
