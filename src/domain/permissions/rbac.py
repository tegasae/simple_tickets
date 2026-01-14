# rbac.py
from enum import Enum
from dataclasses import dataclass, field
from typing import FrozenSet, Optional
from datetime import datetime

from src.domain.exceptions import ItemNotFoundError, ItemAlreadyExistsError, DomainSecurityError

#todo В дальнейшем хранить роли в базе.
class Permission(Enum):
    """All possible permissions in the system"""
    """Все возможные права. Просто перечисление."""
    # Client Operations
    CREATE_CLIENT = "create_client"
    VIEW_CLIENT = "view_client"
    UPDATE_CLIENT = "update_client"
    DELETE_CLIENT = "delete_client"
    ENABLE_CLIENT = "enable_client"

    # Admin Operations
    CREATE_ADMIN = "create_admin"
    VIEW_ADMIN = "view_admin"
    UPDATE_ADMIN = "update_admin"  # Includes role assignment
    DISABLE_ADMIN = "disable_admin"
    DELETE_ADMIN = "delete_admin"

    # Task Operations (for executors)
    EXECUTE_TASK_1 = "execute_task_1"
    EXECUTE_TASK_2 = "execute_task_2"
    EXECUTE_TASK_3 = "execute_task_3"

    # System Operations
    VIEW_AUDIT_LOG = "view_audit_log"
    EXPORT_DATA = "export_data"


@dataclass(frozen=True)
class Role:
    """Immutable role with permissions"""
    """Роль, включает в себя набор прав. Сейчас роли используются только для Admin. В дальнейшем у Client 
    тоже будет поведение и роли нужно будет предусмотреть для Client, но позже."""
    role_id: int
    name: str
    description: str = ""
    permissions: FrozenSet[Permission] = field(default_factory=frozenset)
    is_system_role: bool = False  # Cannot be modified/deleted
    date_created: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission: Permission) -> bool:
        """Ииееет ли роль указанное разрешение"""
        return permission in self.permissions

    def can_manage_clients(self) -> bool:
        """может ли эта роль управлять Client"""
        client_permissions = {
            Permission.CREATE_CLIENT, Permission.VIEW_CLIENT,
            Permission.UPDATE_CLIENT, Permission.DELETE_CLIENT,
            Permission.ENABLE_CLIENT
        }
        return any(p in self.permissions for p in client_permissions)

    def can_manage_admins(self) -> bool:
        """может ли эта роль управлять Admin"""
        admin_permissions = {
            Permission.CREATE_ADMIN, Permission.VIEW_ADMIN,
            Permission.UPDATE_ADMIN, Permission.DISABLE_ADMIN,
            Permission.DELETE_ADMIN
        }
        return any(p in self.permissions for p in admin_permissions)


@dataclass(frozen=True)
class EmptyRole(Role):
    """Immutable role with permissions"""
    """Пустая роль"""
    role_id: int=0
    name: str=""
    description: str = ""
    permissions: set=()
    is_system_role: bool = False  # Cannot be modified/deleted
    date_created: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission: Permission) -> bool:
        return False

    def can_manage_clients(self) -> bool:
        return False

    def can_manage_admins(self) -> bool:
        return False


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
                    Permission.EXECUTE_TASK_1,
                    Permission.EXECUTE_TASK_2,
                    Permission.EXECUTE_TASK_3
                }),
                is_system_role=True
            ),
            Role(
                role_id=2,
                name="manager",
                description="Can manage all client operations",
                permissions=frozenset({
                    Permission.CREATE_CLIENT,
                    Permission.VIEW_CLIENT,
                    Permission.UPDATE_CLIENT,
                    Permission.DELETE_CLIENT,
                    Permission.ENABLE_CLIENT
                }),
                is_system_role=True
            ),
            Role(
                role_id=3,
                name="supervisor",
                description="Can manage all admin operations",
                permissions=frozenset({
                    Permission.CREATE_ADMIN,
                    Permission.VIEW_ADMIN,
                    Permission.UPDATE_ADMIN,  # Includes role assignment!
                    Permission.DISABLE_ADMIN,
                    Permission.DELETE_ADMIN,
                    Permission.VIEW_AUDIT_LOG
                }),
                is_system_role=True
            )
        }

        for role in default_roles:
            self._roles_by_id[role.role_id] = role


    def get_role_by_id(self, role_id: int) -> Role:
        return self._roles_by_id.get(role_id,EmptyRole())

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
                           permissions: set[Permission]) -> Role:
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
                                new_permissions: set[Permission]) -> Role:
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