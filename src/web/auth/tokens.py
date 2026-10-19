import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Self

import jwt
from pydantic import BaseModel, Field, ValidationError

from src.web.auth.exceptions import TokenError
from src.web.config import Settings


SubjectType = Literal["admin", "user"]
AccessTokenType = Literal["access"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_token(token: str) -> str:
    """
    Use this when storing refresh tokens in DB.

    Store the hash, not the raw refresh token.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AccessToken(BaseModel):
    """
    JWT access token.

    Used for normal API requests.

    Required claims:
        sub          -> subject id as string
        subject_type -> admin/user
        token_type   -> access
        exp          -> expiration
        iat          -> issued at

    Recommended claims:
        iss -> issuer
        aud -> audience
        jti -> token id
    """

    sub: str
    subject_type: SubjectType
    token_type: AccessTokenType = "access"

    exp: datetime
    iat: datetime = Field(default_factory=utcnow)

    iss: str
    aud: str
    jti: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    scope: list[str] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        settings: Settings,
        subject_id: int,
        subject_type: SubjectType,
        scope: list[str] | None = None,
    ) -> Self:
        now = utcnow()

        return cls(
            sub=str(subject_id),
            subject_type=subject_type,
            scope=scope or [],
            iat=now,
            exp=now + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
            iss=settings.JWT_ISSUER,
            aud=settings.JWT_AUDIENCE,
        )

    def scope_to_str(self) -> str:
        return " ".join(self.scope)

    @staticmethod
    def scope_from_str(value: str | None) -> list[str]:
        if not value:
            return []

        return [
            item.strip()
            for item in value.split(" ")
            if item.strip()
        ]

    def to_payload(self) -> dict[str, Any]:
        payload = self.model_dump()

        if self.scope:
            payload["scope"] = self.scope_to_str()
        else:
            payload.pop("scope", None)

        return payload

    def encode(
        self,
        *,
        settings: Settings,
    ) -> str:
        return jwt.encode(
            self.to_payload(),
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    @classmethod
    def decode(
        cls,
        token: str,
        *,
        settings: Settings,
    ) -> Self:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )

            if payload.get("token_type") != "access":
                raise TokenError("Invalid token type")

            if "scope" in payload:
                payload["scope"] = cls.scope_from_str(
                    payload.get("scope")
                )

            return cls(**payload)

        except jwt.ExpiredSignatureError as exc:
            raise TokenError("Token has expired") from exc

        except jwt.InvalidTokenError as exc:
            raise TokenError(
                f"Invalid token: {exc}"
            ) from exc

        except ValidationError as exc:
            raise TokenError(
                f"Invalid token payload: {exc}"
            ) from exc

    def is_valid(self) -> bool:
        if not self.sub:
            return False

        exp = self.exp

        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        return exp > utcnow()

    def get_admin_id(self) -> int:
        if self and self.subject_type == "admin":
            return int(self.sub)

        raise TokenError("Invalid admin token type")

    def get_user_id(self) -> int:
        if self and self.subject_type == "user":
            return int(self.sub)

        raise TokenError("Invalid user token type")

    def __bool__(self) -> bool:
        return self.is_valid()


class RefreshToken(BaseModel):
    """
    Opaque refresh token.

    This is NOT a JWT.

    The client receives token_id.
    The server should store hash_token(token_id) in DB.
    """

    token_id: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32)
    )

    subject_id: int
    subject_type: SubjectType
    username: str

    created_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime

    used: bool = False
    revoked: bool = False

    last_used_at: datetime | None = None
    use_count: int = 0

    client_id: str = ""
    scope: list[str] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        settings: Settings,
        subject_id: int,
        subject_type: SubjectType,
        username: str,
        client_id: str = "",
        scope: list[str] | None = None,
    ) -> Self:
        now = utcnow()

        return cls(
            subject_id=subject_id,
            subject_type=subject_type,
            username=username,
            client_id=client_id,
            scope=scope or [],
            created_at=now,
            expires_at=now + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
        )

    @property
    def token_hash(self) -> str:
        return hash_token(self.token_id)

    def mark_used(self) -> None:
        self.used = True
        self.last_used_at = utcnow()
        self.use_count += 1

    def revoke(self) -> None:
        self.revoked = True

    def is_valid(self) -> bool:
        if self.subject_id <= 0:
            return False

        if not self.username:
            return False

        expires_at = self.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= utcnow():
            return False

        if self.used:
            return False

        if self.revoked:
            return False

        return True

    def __bool__(self) -> bool:
        return self.is_valid()


class JWTToken(BaseModel):
    """
    Token pair returned from login endpoint.

    access_token  -> JWT string
    refresh_token -> opaque random string
    """

    access_token: AccessToken
    refresh_token: RefreshToken

    @classmethod
    def create(
        cls,
        *,
        settings: Settings,
        subject_id: int,
        subject_type: SubjectType,
        username: str,
        client_id: str = "",
        scope: list[str] | None = None,
    ) -> Self:
        normalized_scope = scope or []

        return cls(
            access_token=AccessToken.create(
                settings=settings,
                subject_id=subject_id,
                subject_type=subject_type,
                scope=normalized_scope,
            ),
            refresh_token=RefreshToken.create(
                settings=settings,
                subject_id=subject_id,
                subject_type=subject_type,
                username=username,
                client_id=client_id,
                scope=normalized_scope,
            ),
        )

    def encode(
        self,
        *,
        settings: Settings,
    ) -> dict[str, Any]:
        now = utcnow()

        exp = self.access_token.exp

        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        expires_in = int(
            (exp - now).total_seconds()
        )

        return {
            "access_token": self.access_token.encode(
                settings=settings
            ),
            "refresh_token": self.refresh_token.token_id,
            "token_type": "bearer",
            "expires_in": max(expires_in, 0),
            "scope": self.access_token.scope_to_str(),
        }

    def is_valid(self) -> bool:
        return (
            bool(self.access_token)
            and bool(self.refresh_token)
        )

    def __bool__(self) -> bool:
        return self.is_valid()