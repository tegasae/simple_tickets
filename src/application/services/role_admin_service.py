from typing import Iterable


from src.domain.exceptions import DomainOperationError
from src.domain.rbac.role_new import Role
from src.domain.rbac.typevar import P
from src.services.uow.uow import UnitOfWork


class RoleService:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
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
        with self.uow:
            role = Role(
                role_id=0,
                name=name,
                permissions=frozenset(permissions),
                description=description,
                is_system_role=is_system_role,
            )

            role=self.uow.roles_admin.add(role)
        return role

    # -----------------------------
    # Delete role
    # -----------------------------

    def delete_role(self, role_id: int):
        with self.uow:
            role=self.get_role(role_id=role_id)
            if role.is_system_role:
                raise DomainOperationError("System role cannot be deleted")

        if self.uow.roles_admin.is_assigned(role_id=role_id):
            raise DomainOperationError(
                f"Role {role_id} cannot be deleted because it is assigned to users"
            )

        self.uow.roles_admin.delete(role_id=role_id)


    # -----------------------------
    # Queries
    # -----------------------------

    def get_role(self, role_id: int) -> Role[P]:
        return self.uow.roles_admin.get(role_id=role_id)

    def get_all_roles(self) -> Iterable[Role[P]]:
        return self.uow.roles_admin.all()