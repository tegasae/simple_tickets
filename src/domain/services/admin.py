from src.domain.clients import ClientsAggregate
from src.domain.exceptions import DomainSecurityError, DomainOperationError, ItemNotFoundError
from src.domain.model import AdminsAggregate, AdminAbstract
from src.domain.permissions.rbac import Permission


class AdminManagementService:
    """Domain Service for admin operations with cross-aggregate rules"""

    def __init__(self, admins_aggregate: AdminsAggregate, clients_aggregate: ClientsAggregate):
        self.admins = admins_aggregate
        self.clients = clients_aggregate

    def _get_admins(self,requesting_admin_id:int,admin_to_operation)->tuple[AdminAbstract,AdminAbstract]:
        requesting_admin = self.admins.get_admin_by_id(requesting_admin_id)
        admin_to_operation=self.admins.get_admin_by_id(admin_to_operation)
        return requesting_admin,admin_to_operation

    def _require_permission(self, admin_id: int, permission: Permission) -> AdminAbstract:
        """Reusable permission checker using your has_permission() method"""
        admin = self.admins.get_admin_by_id(admin_id)

        if admin.is_empty():
            raise ItemNotFoundError(f"Admin '{admin_id}' not found")

        if not admin.enabled:
            raise DomainOperationError(f"Admin '{admin.name}' is disabled")

        # ← HERE'S WHERE YOU USE YOUR EXISTING METHOD!
        if not admin.has_permission(permission, self.roles):
            raise DomainSecurityError(
                f"Admin '{admin.name}' lacks permission: {permission.value}"
            )

        return admin

    def delete_admin(
            self,
            requesting_admin_id: int,
            admin_to_delete_id: int
    ) -> None:
        """
        Delete an admin with business rules:
        - Rule 5: Admin can't delete itself
        - Additional: Check if admin has created clients
        """
        # 1. Validate requesting admin exists and is active
        (requesting_admin,admin_to_delete)=(
            self._get_admins(requesting_admin_id=requesting_admin_id,admin_to_operation=admin_to_delete_id))
        if requesting_admin==admin_to_delete:
            raise DomainSecurityError("Admin cannot delete themselves")


        # 4. Check if admin to delete has created any clients
        clients_by_admin = self.clients.get_clients_by_admin(admin_to_delete.admin_id)
        if clients_by_admin:
            client_names = [str(c.name) for c in clients_by_admin]
            raise DomainOperationError(
                f"Cannot delete admin '{admin_to_delete.name}'. "
                f"They have created clients: {', '.join(client_names[:3])}"
                f"{'...' if len(client_names) > 3 else ''}"
            )

        # 5. Delete the admin
        self.admins.remove_admin_by_id(admin_to_delete.admin_id)

    def disable_admin(
            self,
            requesting_admin_id: int,
            admin_to_disable_id: int
    ) -> None:
        """Disable an admin (softer than delete)"""

        (requesting_admin, admin_to_disable) = (
            self._get_admins(requesting_admin_id=requesting_admin_id, admin_to_operation=admin_to_disable_id))

        # Can't disable yourself
        if requesting_admin==admin_to_disable:
            raise DomainSecurityError("Admin cannot disable themselves")
        if requesting_admin.has_permission(Permission.UPDATE_ADMIN, requesting_admin.roles):
            self.admins.set_admin_status(admin_to_disable.name, False)

    def create_admin(self,requesting_admin_id:int,
                     name:str,email:str,password:str,enable:bool=True)->AdminAbstract:

        requesting_admin=self.admins.get_admin_by_id(requesting_admin_id)
        if requesting_admin.is_empty() or not requesting_admin.enabled:
            raise DomainSecurityError(f"Admin {requesting_admin.name} cannot create a new admin")
        admin=self.admins.create_admin(admin_id=0, name=name,email=email,password=password,enabled=enable)
        return admin
