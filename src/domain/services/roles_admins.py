from src.domain.exceptions import ItemNotFoundError, DomainOperationError, DomainSecurityError
from src.domain.model import Admin
from src.domain.permissions.rbac import RoleRegistry, Permission


class AdminRolesManagementService:
    """Domain Service for admin operations with cross-aggregate rules"""

    def __init__(self, roles_registry: RoleRegistry):
        self.roles_registry=roles_registry

    def assign_role_to_admin(self, admin: Admin, role_id: int) -> Admin:
        """Assign role to admin (requires UPDATE_ADMIN permission)"""
        role = self.roles_registry.get_role_by_id(role_id)
        admin.assign_role(role.role_id, self.roles_registry)
        return admin


    def remove_role_from_admin(self, admin:Admin, role_id: int) -> Admin:

        """Remove role from admin"""

        role=self.roles_registry.get_role_by_id(role_id)
        admin.remove_role(role.role_id)
        return admin

    def check_permission(self, admin: Admin, permission: Permission) -> None:
        if admin.is_empty():
            raise ItemNotFoundError(f"Admin ID {admin.admin_id} not found")

        if not admin.enabled:
            raise DomainOperationError(f"Admin '{admin.name}' is disabled")


        # ← HERE'S WHERE YOU USE YOUR EXISTING METHOD!
        if not admin.has_permission(permission, self.roles_registry):
            raise DomainSecurityError(
                f"Admin '{admin.name}' lacks permission: {permission.value}"
            )