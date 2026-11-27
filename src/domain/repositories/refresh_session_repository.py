from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

SubjectType = Literal["admin", "user"]


@dataclass(frozen=True)
class RefreshSession:
    account_id: int
    subject_id: int
    subject_type: SubjectType
    username: str
    created_at: datetime
    expires_at: datetime
    scope: tuple[str, ...]


class RefreshSessionRepository(ABC):
    """Operate on hashes and metadata in the caller's transaction."""

    @abstractmethod
    def get(self, token_hash: str) -> RefreshSession | None:
        raise NotImplementedError

    @abstractmethod
    def add(self, token_hash: str, session: RefreshSession) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove(self, token_hash: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def revoke_subject(self, *, subject_type: SubjectType, subject_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove_expired(self, *, now: datetime) -> None:
        raise NotImplementedError
