from enum import StrEnum



#class PermissionLike(Protocol):
#    value: str


class PermissionBase(StrEnum):
    @classmethod
    def from_value(cls, v: str) -> "PermissionBase":
        return cls(v)  # выбросит ValueError если нет такого значения

class PermissionUser(PermissionBase):
    """User-specific permissions"""
    CREATE_USER = "create_user"          # SuperUsers only
    VIEW_USER = "view_user"              # All users
    UPDATE_USER = "update_user"          # SuperUsers only
    DISABLE_USER = "disable_user"        # SuperUsers only
    DELETE_USER = "delete_user"          # SuperUsers only
    CREATE_TICKET = "create_ticket"      # All users
    DELETE_OWN_TICKET = "delete_own_ticket"  # All users
    DELETE_ANY_TICKET = "delete_any_ticket"  # SuperUsers only
    VIEW_ANY_TICKET = "view_any_ticket"  #superuser
    VIEW_OWN_TICKET = "view_ticket" #all user


class PermissionAdmin(PermissionBase):
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
