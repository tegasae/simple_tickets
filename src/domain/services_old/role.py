#src/domain/services/role.py

from typing import Iterable


from src.domain.exceptions import DomainOperationError
from src.domain.rbac.role_new import Role
from src.domain.rbac.role_repository import RoleRepository
from src.domain.rbac.typevar import P


class RoleService:

    def __init__(self, role_repository: RoleRepository[P]):
        self._role_repository = role_repository

    # -----------------------------
    # Create role
    # -----------------------------

    def create_role(
        self,
        *,
        name: str,
        permissions: Iterable[P],
        description: str = "",
        is_system_role: bool = False,
    ) -> Role[P]:

        role = Role(
            role_id=0,
            name=name,
            permissions=frozenset(permissions),
            description=description,
            is_system_role=is_system_role,
        )

        return self._role_repository.add(role)

    # -----------------------------
    # Delete role
    # -----------------------------

    def delete_role(self, role_id: int):

        role = self._role_repository.get(role_id)

        if role.is_system_role:
            raise DomainOperationError("System role cannot be deleted")

        if self._role_repository.is_assigned(role_id):
            raise DomainOperationError(
                f"Role {role_id} cannot be deleted because it is assigned to users"
            )

        self._role_repository.delete(role_id)

    # -----------------------------
    # Queries
    # -----------------------------

    def get_role(self, role_id: int) -> Role[P]:
        return self._role_repository.get(role_id)

    def get_all_roles(self) -> Iterable[Role[P]]:
        return self._role_repository.all()