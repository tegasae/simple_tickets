from src.domain.exceptions import DomainSecurityError, DomainOperationError, ItemNotFoundError
from src.domain.model import AdminsAggregate, AdminAbstract, AdminEmpty, Admin
from src.domain.permissions.rbac import Permission, RoleRegistry


class AdminManagementService:
    """Domain Service for admin operations with cross-aggregate rules"""

    def __init__(self, admins_aggregate: AdminsAggregate, roles_registry: RoleRegistry):
        self.admins = admins_aggregate
        self.roles=roles_registry

    def _get_admins(self,requesting_admin_id:int,admin_to_operation:int,permission: Permission)->tuple[AdminAbstract,AdminAbstract]:
        requesting_admin = self.admins.get_admin_by_id(requesting_admin_id)
        if admin_to_operation!=0:
            admin_to_operation=self.admins.get_admin_by_id(admin_to_operation)
        else:
            admin_to_operation=AdminEmpty()

        if requesting_admin.is_empty():
            raise ItemNotFoundError(f"Admin '{requesting_admin_id}' not found")

        if not requesting_admin.enabled:
            raise DomainOperationError(f"Admin '{requesting_admin.name}' is disabled")

        # ← HERE'S WHERE YOU USE YOUR EXISTING METHOD!
        if not requesting_admin.has_permission(permission, self.roles):
            raise DomainSecurityError(
                f"Admin '{requesting_admin.name}' lacks permission: {permission.value}"
            )
        return requesting_admin,admin_to_operation


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
            self._get_admins(requesting_admin_id=requesting_admin_id,admin_to_operation=admin_to_delete_id,permission=Permission.DELETE_ADMIN))

        if requesting_admin==admin_to_delete:
            raise DomainSecurityError("Admin cannot delete themselves")


        # 4. Check if admin to delete has created any clients

        if admin_to_delete.created_clients!=0:
            raise DomainOperationError(
                f"Cannot delete admin '{admin_to_delete.name}'. It has {admin_to_delete.created_clients}."
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
            self._get_admins(requesting_admin_id=requesting_admin_id, admin_to_operation=admin_to_disable_id,permission=Permission.DISABLE_ADMIN))

        # Can't disable yourself
        if requesting_admin==admin_to_disable:
            raise DomainSecurityError("Admin cannot disable themselves")

        self.admins.set_admin_status(admin_to_disable.name, False)

    def create_admin(self,requesting_admin_id:int,
                     name:str,email:str,password:str,enabled:bool=True,roles:set[int]=())->AdminAbstract:

        (requesting_admin, _) = (
            self._get_admins(requesting_admin_id=requesting_admin_id, admin_to_operation=0,permission=Permission.CREATE_ADMIN))


        if requesting_admin.is_empty() or not requesting_admin.enabled:
            raise DomainSecurityError(f"Admin {requesting_admin.name} cannot create a new admin")
        admin=self.admins.create_admin(admin_id=0, name=name,email=email,password=password,enabled=enabled,roles=roles)
        return admin

    def update_admin(self,requesting_admin_id:int,new_admin:AdminAbstract)->AdminAbstract:
        self._get_admins(requesting_admin_id=requesting_admin_id, admin_to_operation=new_admin.admin_id,
                             permission=Permission.UPDATE_ADMIN)
        admin=self.admins.change_admin(admin=new_admin)
        return admin


    def assign_role_to_admin(self, requesting_admin_id: int,
                             target_admin_id: int, role_id: int) -> None:
        """Assign role to admin (requires UPDATE_ADMIN permission)"""
        (requesting_admin, target_admin) = (
            self._get_admins(requesting_admin_id=requesting_admin_id, admin_to_operation=target_admin_id,
                             permission=Permission.UPDATE_ADMIN))

        # 4. Assign role
        role=self.roles.get_role_by_id(role_id)
        target_admin.assign_role(role.role_id, self.roles)



    def remove_role_from_admin(self, requesting_admin_id: int,
                               target_admin_id: int, role_id: int) -> None:

        """Remove role from admin"""
        (requesting_admin, target_admin) = (
            self._get_admins(requesting_admin_id=requesting_admin_id, admin_to_operation=target_admin_id,
                             permission=Permission.UPDATE_ADMIN))

        role=self.roles.get_role_by_id(role_id)
        target_admin.remove_role(role.role_id)
