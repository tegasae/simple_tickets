# domain/services/user_role_service.py
from src.domain.exceptions import DomainSecurityError
from src.old.permissions.role_registry import NewRoleRegistry
from src.old.permissions.permission import PermissionUser
from src.domain.users import User


class UserRoleService:
    """Service for managing user roles and permissions"""

    def __init__(self, role_registry: NewRoleRegistry):
        self.role_registry = role_registry

    def check_permission(self, user: User, permission: PermissionUser) -> None:
        """Check if user has permission, raise exception if not"""
        if not user.has_permission(permission, self.role_registry):
            raise DomainSecurityError(
                f"User '{user.name}' lacks permission: {permission.value}"
            )

    def assign_role(self, user: User, role_id: int) -> User:
        """Assign role to user"""
        user.assign_role(role_id, self.role_registry)
        return user

    @staticmethod
    def remove_role(user: User, role_id: int) -> User:
        """Remove role from user"""
        user.remove_role(role_id)
        return user


