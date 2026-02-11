from abc import ABC, abstractmethod
from typing import Generic, Iterable

from pydantic.v1 import Protocol

from src.domain.rbac.role import Role, P


class RoleRepository(ABC, Generic[P]):
    """In-memory role registry for ONE realm (Admin OR User)."""

    @abstractmethod
    def add(self, role: Role[P]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, role_id: int) -> Role[P]:
        raise NotImplementedError

    def all(self) -> Iterable[Role[P]]:
        raise NotImplementedError
