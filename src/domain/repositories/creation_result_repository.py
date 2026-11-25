from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CreationKey:
    employee_id: int
    key: str


@dataclass(frozen=True)
class CreationResult:
    fingerprint: str
    status_code: int
    body: str
    expires_at: float | None = None


class CreationAlreadyReserved(Exception):
    """Another transaction owns this scoped key."""


class CreationResultRepository(ABC):
    @abstractmethod
    def get(self, key: CreationKey) -> CreationResult | None:
        raise NotImplementedError

    @abstractmethod
    def reserve(self, key: CreationKey, *, fingerprint: str) -> None:
        """Claim the key or raise CreationAlreadyReserved if it already exists."""
        raise NotImplementedError

    @abstractmethod
    def complete(self, key: CreationKey, *, result: CreationResult) -> None:
        raise NotImplementedError

    @abstractmethod
    def forget_expired(self, key: CreationKey, *, now: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def pending_deadlines(self) -> list[CreationKey]:
        raise NotImplementedError

    @abstractmethod
    def set_deadline(self, key: CreationKey, *, expires_at: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def prune_expired(self, *, now: float) -> None:
        raise NotImplementedError
