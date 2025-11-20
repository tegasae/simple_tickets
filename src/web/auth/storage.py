from threading import Lock
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Optional

from src.web.auth.exceptions import TokenNotFoundError
from src.web.auth.tokens import RefreshToken


class TokenStorage(ABC):
    @abstractmethod
    def put(self, refresh_token: RefreshToken):
        raise NotImplementedError

    @abstractmethod
    def get(self, token_id: str) -> Optional[RefreshToken]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, token_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens, return count removed"""
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
    def clear(self):
        raise NotImplementedError


class TokenStorageMemory(TokenStorage):
    _instance = None
    _lock = Lock()

    def __init__(self):
        # Prevent reinitialization in singleton
        if not hasattr(self, '_initialized'):
            self._refresh_tokens = {}
            self._initialized = True

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def put(self, refresh_token: RefreshToken):
        with self._lock:
            self._refresh_tokens[refresh_token.token_id] = refresh_token

    def get(self, token_id: str) -> RefreshToken:
        with self._lock:
            token = self._refresh_tokens.get(token_id)  # ✅ Fixed: access dictionary directly
            if token is None:
                raise TokenNotFoundError(token_id)
            return token

    def delete(self, token_id: str):
        """Delete token by ID, raises exception if not found"""
        with self._lock:
            if token_id not in self._refresh_tokens:
                raise TokenNotFoundError(token_id)
            del self._refresh_tokens[token_id]

    def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from storage"""
        with self._lock:
            current_time = datetime.now(timezone.utc)
            expired_tokens = [
                token_id for token_id, token in self._refresh_tokens.items()
                if token.expires_at < current_time or token.used
            ]
            for token_id in expired_tokens:
                del self._refresh_tokens[token_id]
            return len(expired_tokens)

    def get_user_tokens(self, username: str) -> list[RefreshToken]:
        """Get all tokens for a specific user"""
        with self._lock:
            return [
                token for token in self._refresh_tokens.values()
                if token.username == username
            ]

    def revoke_user_tokens(self, username: str) -> int:
        """Revoke all tokens for a user (e.g., on password change)"""
        with self._lock:
            user_tokens = [
                token for token in self._refresh_tokens.values()
                if token.username == username
            ]
            for token in user_tokens:
                token.used = True
            return len(user_tokens)

    def count(self) -> int:
        """Get total number of stored tokens"""
        with self._lock:
            return len(self._refresh_tokens)

    def clear(self):
        """Clear all tokens (mainly for testing)"""
        with self._lock:
            self._refresh_tokens.clear()
