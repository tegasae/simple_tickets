from abc import ABC, abstractmethod
from typing import Generic, Iterable



from src.domain.rbac.role import P
from src.domain.rbac.role_new import Role


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
