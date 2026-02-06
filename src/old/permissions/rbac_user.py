# domain/permissions/user_roles.py


from dataclasses import dataclass

from src.old.permissions.permission import PermissionUser
from src.old.permissions.role import UserRole


@dataclass(frozen=True)
class OrdinaryUserRole(UserRole):
    """Ordinary User Role - limited permissions"""

    def __init__(self):
        # Initialize with frozen=True dataclass pattern
        super().__init__(
            role_id=100,
            name="ordinary_user",
            description="Regular user with basic permissions",
            permissions=frozenset({
                PermissionUser.VIEW_USER,
                PermissionUser.CREATE_TICKET,
                PermissionUser.DELETE_OWN_TICKET
            }),
            is_system_role=True
        )


@dataclass(frozen=True)
class SuperUserRole(UserRole):
    """Super User Role - full permissions"""

    def __init__(self):
        super().__init__(
            role_id=200,
            name="super_user",
            description="Super user with administrative permissions",
            permissions=frozenset({
                PermissionUser.CREATE_USER,
                PermissionUser.VIEW_USER,
                PermissionUser.UPDATE_USER,
                PermissionUser.DISABLE_USER,
                PermissionUser.DELETE_USER,
                PermissionUser.CREATE_TICKET,
                PermissionUser.DELETE_OWN_TICKET,
                PermissionUser.DELETE_ANY_TICKET,
            }),
            is_system_role=True
        )


EMPTY_ROLE = Role(
    role_id=0,
    name="",
    description="",
    permissions=frozenset(),
    is_system_role=True,
)
