from typing import Iterable


from src.domain.rbac.role_new import Role
from src.domain.rbac.typevar import P
from src.domain.repositories.role_repository import RoleRepository


class RoleRepo(RoleRepository):
    """In-memory role registry for ONE realm (Admin OR User)."""
    def __init__(self) -> None:
        self._by_id: dict[int, Role] = {}

    def add(self, role: Role[P]) -> None:
        if role.role_id in self._by_id:
            raise ValueError(f"Role already exists: id={role.role_id}")
        self._by_id[role.role_id] = role

    def get(self, role_id: int) -> Role[P]:
        try:
            return self._by_id[role_id]
        except KeyError:
            raise LookupError(f"Unknown role_id={role_id}") from None

    def all(self) -> Iterable[Role[P]]:
        return self._by_id.values()
