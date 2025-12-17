# rbac.py
from enum import Enum
from dataclasses import dataclass, field
from typing import FrozenSet
from datetime import datetime


class Permission(Enum):
    """All possible permissions in the system"""
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
    role_id: int
    name: str
    description: str = ""
    permissions: FrozenSet[Permission] = field(default_factory=frozenset)
    is_system_role: bool = False  # Cannot be modified/deleted
    date_created: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions

    def can_manage_clients(self) -> bool:
        client_permissions = {
            Permission.CREATE_CLIENT, Permission.VIEW_CLIENT,
            Permission.UPDATE_CLIENT, Permission.DELETE_CLIENT,
            Permission.ENABLE_CLIENT
        }
        return any(p in self.permissions for p in client_permissions)

    def can_manage_admins(self) -> bool:
        admin_permissions = {
            Permission.CREATE_ADMIN, Permission.VIEW_ADMIN,
            Permission.UPDATE_ADMIN, Permission.DISABLE_ADMIN,
            Permission.DELETE_ADMIN
        }
        return any(p in self.permissions for p in admin_permissions)