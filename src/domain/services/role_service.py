from dataclasses import field




from src.domain.rbac.permissions import UserPermission, AdminPermission
from src.domain.rbac.role_new import AdminRole, UserRole
from src.domain.value_objects import Name


class RoleAdminService:
    @staticmethod
    def create_role(
        *,
        name: str,                    # human-readable (may change)
        permissions: frozenset[str] = field(default_factory=frozenset),
        description: str = "",
        is_system_role: bool = False

    ) -> AdminRole:
        role = AdminRole.create(
                name=name,
                permissions=frozenset(map(AdminPermission, permissions)),
                description=description,
                is_system_role=is_system_role,
            )

        return role

class RoleUserService:
    @staticmethod
    def create_role(
        *,
        name: str,                    # human-readable (may change)
        permissions: frozenset[str] = field(default_factory=frozenset),
        description: str = "",
        is_system_role: bool = False

    ) -> UserRole:

        role = UserRole.create(
                name=name,
                permissions=frozenset(map(UserPermission, permissions)),
                description=description,
                is_system_role=is_system_role,
            )

        return role



