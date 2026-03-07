from abc import ABC, abstractmethod
from typing import Generic, Iterable



from src.domain.rbac.role_new import Role
from src.domain.rbac.typevar import P


class RoleRepository(ABC, Generic[P]):
    """In-memory role registry for ONE realm (Admin OR User)."""

    @abstractmethod
    def add(self, role: Role[P]) -> Role[P]:
        raise NotImplementedError

    @abstractmethod
    def get(self, role_id: int) -> Role[P]:
        raise NotImplementedError

    @abstractmethod
    def all(self) -> Iterable[Role[P]]:
        raise NotImplementedError

    @abstractmethod
    def delete(self,role_id):
        raise NotImplementedError

    @abstractmethod
    def is_assigned(self, role_id: int) -> bool:
        """Check whether role is assigned to any admin or user."""
        raise NotImplementedError


