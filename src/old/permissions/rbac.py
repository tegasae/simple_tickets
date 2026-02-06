# rbac.py

from src.domain.exceptions import ItemNotFoundError, ItemAlreadyExistsError, DomainSecurityError
from src.old.permissions.permission import PermissionAdmin
from src.old.permissions.role import Role, EmptyRole


#from src.domain.permissions.permission import PermissionAdmin




# rbac.py (continued)
class RoleRegistry:
    """Aggregate for managing roles"""
    """Набор ролей. Пока роли только для Admin. Есть несколько предопределенных ролей."""
    """Роли хранятся по id."""
    #todo избавиться от хранения ролей по имени, хранить только по id.
    def __init__(self):
        self._roles_by_id: dict[int, Role] = {}  # ID → Role
        self._load_default_roles()



    def _load_default_roles(self):
        """Create default system roles"""
        """Предопределенные роли"""
        default_roles = {
            Role(
                role_id=1,
                name="executor",
                description="Can execute predefined tasks",
                permissions=frozenset({
                    PermissionAdmin.EXECUTE_TASK_1,
                    PermissionAdmin.EXECUTE_TASK_2,
                    PermissionAdmin.EXECUTE_TASK_3
                }),
                is_system_role=True
            ),
            Role(
                role_id=2,
                name="manager",
                description="Can manage all client operations",
                permissions=frozenset({
                    PermissionAdmin.CREATE_CLIENT,
                    PermissionAdmin.VIEW_CLIENT,
                    PermissionAdmin.UPDATE_CLIENT,
                    PermissionAdmin.DELETE_CLIENT,
                    PermissionAdmin.ENABLE_CLIENT
                }),
                is_system_role=True
            ),
            Role(
                role_id=3,
                name="supervisor",
                description="Can manage all admin operations",
                permissions=frozenset({
                    PermissionAdmin.CREATE_ADMIN,
                    PermissionAdmin.VIEW_ADMIN,
                    PermissionAdmin.UPDATE_ADMIN,  # Includes role assignment!
                    PermissionAdmin.DISABLE_ADMIN,
                    PermissionAdmin.DELETE_ADMIN,
                    PermissionAdmin.VIEW_AUDIT_LOG
                }),
                is_system_role=True
            )
        }

        for role in default_roles:
            self._roles_by_id[role.role_id] = role


    def get_role_by_id(self, role_id: int) -> Role:
        return self._roles_by_id.get(role_id, EmptyRole())

    def role_exists_by_name(self, role_name: str) -> bool:
        for role in self._roles_by_id.values():
            if role.name == role_name:
                return True
        return False

    def get_role_by_name(self, role_name: str) -> Role:
        for role in self._roles_by_id.values():
            if role.name == role_name:
                return role
        return EmptyRole()


    def role_exists_by_id(self, role_id: int) -> bool:
        return role_id in self._roles_by_id

    def create_custom_role(self, name: str, description: str,
                           permissions: set[PermissionAdmin]) -> Role:
        """Create a new custom role (for future extensibility)"""
        if self.role_exists_by_name(name):
            raise ItemAlreadyExistsError(f"Role '{name}' already exists")

        role = Role(
            role_id=len(self._roles_by_id) + 1,
            name=name,
            description=description,
            permissions=frozenset(permissions),
            is_system_role=False
        )

        self._roles_by_id[role.role_id] = role
        return role

    def update_role_permissions(self, role_id: int,
                                new_permissions: set[PermissionAdmin]) -> Role:
        """Update permissions for a role (cannot modify system roles)"""
        role = self.get_role_by_id(role_id)
        if not role:
            raise ItemNotFoundError(f"Role '{role_id}' not found")

        if role.is_system_role:
            raise DomainSecurityError("Cannot modify system roles")

        updated_role = Role(
            role_id=role.role_id,
            name=role.name,
            description=role.description,
            permissions=frozenset(new_permissions),
            is_system_role=False
        )
        self._roles_by_id[role.role_id] = updated_role
        return updated_role

    def get_all_roles(self) -> list[Role]:
        return list(self._roles_by_id.values())

    def require_role_by_id(self, role_id: int) -> Role:
        role = self.get_role_by_id(role_id)
        if not role:
            raise ItemNotFoundError(f"Role ID '{role_id}' not found")
        return role