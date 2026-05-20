from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from threading import Lock

from src.web.auth_old.exceptions import TokenNotFoundError
from src.web.auth.tokens import RefreshToken, hash_token


class TokenStorage(ABC):
    @abstractmethod
    def put(self, refresh_token: RefreshToken) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, token_id: str) -> RefreshToken:
        raise NotImplementedError

    @abstractmethod
    def delete(self, token_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired/used/revoked tokens.

        Returns:
            Number of removed tokens.
        """
        raise NotImplementedError

    @abstractmethod
    def get_user_tokens(self, username: str) -> list[RefreshToken]:
        raise NotImplementedError

    @abstractmethod
    def revoke_user_tokens(self, username: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError


class TokenStorageMemory(TokenStorage):
    """
    In-memory refresh token storage.

    Good for:
        - development
        - tests
        - local experiments

    Not good for production:
        - data is lost after process restart
        - not shared between multiple workers/processes
    """

    _instance: "TokenStorageMemory | None" = None
    _instance_lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._lock = Lock()

        # Key: sha256(raw refresh token)
        # Value: RefreshToken object
        self._refresh_tokens: dict[str, RefreshToken] = {}

        self._initialized = True

    def put(self, refresh_token: RefreshToken) -> None:
        """
        Store refresh token by hash, not by raw token_id.
        """
        with self._lock:
            self._refresh_tokens[refresh_token.token_hash] = refresh_token

    def get(self, token_id: str) -> RefreshToken:
        """
        Get refresh token by raw token_id.

        The raw token is hashed before lookup.
        """
        token_hash = hash_token(token_id)

        with self._lock:
            token = self._refresh_tokens.get(token_hash)

            if token is None:
                raise TokenNotFoundError(token_id)

            return token

    def delete(self, token_id: str) -> None:
        """
        Delete refresh token by raw token_id.
        """
        token_hash = hash_token(token_id)

        with self._lock:
            if token_hash not in self._refresh_tokens:
                raise TokenNotFoundError(token_id)

            del self._refresh_tokens[token_hash]

    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired, used, or revoked refresh tokens.
        """
        now = datetime.now(timezone.utc)

        with self._lock:
            removable_token_hashes = [
                token_hash
                for token_hash, token in self._refresh_tokens.items()
                if token.expires_at <= now
                or token.used
                or token.revoked
            ]

            for token_hash in removable_token_hashes:
                del self._refresh_tokens[token_hash]

            return len(removable_token_hashes)

    def get_user_tokens(self, username: str) -> list[RefreshToken]:
        """
        Get all refresh tokens for username.
        """
        with self._lock:
            return [
                token
                for token in self._refresh_tokens.values()
                if token.username == username
            ]

    def revoke_user_tokens(self, username: str) -> int:
        """
        Revoke all refresh tokens for username.

        Useful for:
            - logout from all devices
            - password change
            - account disable
        """
        count = 0

        with self._lock:
            for token in self._refresh_tokens.values():
                if token.username == username:
                    token.revoke()
                    count += 1

        return count

    def count(self) -> int:
        with self._lock:
            return len(self._refresh_tokens)

    def clear(self) -> None:
        """
        Clear all tokens.

        Mainly useful for tests.
        """
        with self._lock:
            self._refresh_tokens.clear()