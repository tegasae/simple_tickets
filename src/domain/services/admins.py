from functools import wraps

from src.domain.exceptions import DomainSecurityError, DomainOperationError, ItemNotFoundError
from src.domain.model import AdminsAggregate, AdminAbstract, AdminEmpty
from src.domain.permissions.rbac import Permission, RoleRegistry





class AdminManagementService:
    """Domain Service for admin operations with cross-aggregate rules"""

    def __init__(self, admins_aggregate: AdminsAggregate, roles_registry: RoleRegistry):
        self.admins = admins_aggregate
        self.roles=roles_registry


    @staticmethod
    def require_permission(permission: Permission):
        def decorator(func):
            @wraps(func)
            def wrapper(self, requesting_admin_id: int, *args, **kwargs):
                requesting_admin = self._check_admin_permissions(
                    requesting_admin_id, permission
                )

                return func(self, requesting_admin_id, *args, **kwargs)

            return wrapper

        return decorator

    def _check_admin_permissions(self,requesting_admin_id:int,permission: Permission)->AdminAbstract:
        requesting_admin = self.admins.get_admin_by_id(requesting_admin_id)

        if requesting_admin.is_empty():
            raise ItemNotFoundError(f"Admin '{requesting_admin_id}' not found")

        if not requesting_admin.enabled:
            raise DomainOperationError(f"Admin '{requesting_admin.name}' is disabled")

        # ← HERE'S WHERE YOU USE YOUR EXISTING METHOD!
        if not requesting_admin.has_permission(permission, self.roles):
            raise DomainSecurityError(
                f"Admin '{requesting_admin.name}' lacks permission: {permission.value}"
            )
        return requesting_admin



    @require_permission(permission=Permission.DELETE_ADMIN)
    def delete_admin(
            self,
            requesting_admin_id: int,
            targeting_admin_id: int
    ) -> None:
        """
        Delete an admin with business rules:
        - Rule 5: Admin can't delete itself
        - Additional: Check if admin has created clients
        """
        if requesting_admin_id==targeting_admin_id:
            raise DomainSecurityError("Admin cannot delete themselves")

        # 4. Check if admin to delete has created any clients
        admin_to_delete=self.admins.get_admin_by_id(targeting_admin_id)

        # 5. Delete the admin
        self.admins.remove_admin_by_id(admin_to_delete.admin_id)

    @require_permission(Permission.UPDATE_ADMIN)
    def disable_admin(
            self,
            requesting_admin_id:int,
            targeting_admin_id: int
    ) -> None:
        """Disable an admin (softer than delete)"""

        # Can't disable yourself
        if requesting_admin_id==targeting_admin_id:
            raise DomainSecurityError("Admin cannot disable themselves")


        self.admins.set_admin_status(targeting_admin_id, False)

    @require_permission(Permission.UPDATE_ADMIN)
    def enable_admin(
            self,
            requesting_admin_id: int,
            targeting_admin_id: int
    ) -> None:
        """Disable an admin (softer than delete)"""

        self.admins.set_admin_status(targeting_admin_id, True)

    @require_permission(Permission.CREATE_ADMIN)
    def create_admin(self,requesting_admin_id:int,
                     name:str,email:str,password:str,enabled:bool=True,roles:set[int]=())->AdminAbstract:

        admin=self.admins.create_admin(admin_id=0, name=name,email=email,password=password,enabled=enabled,roles=roles)
        return admin

    @require_permission(Permission.UPDATE_ADMIN)
    def update_admin(self,requesting_admin_id:int, targeting_admin_id: int, email:str=None,
                     password:str=None)->AdminAbstract:
        admin=AdminEmpty()
        if email:
            admin=self.admins.change_admin_email(admin_id=targeting_admin_id,new_email=email)
        if password:
            admin=self.admins.change_admin_password(admin_id=targeting_admin_id,new_password=password)
        return admin

    @require_permission(Permission.UPDATE_ADMIN)
    def assign_role_to_admin(self, requesting_admin_id: int,
                             targeting_admin_id: int, role_id: int) -> AdminAbstract:
        """Assign role to admin (requires UPDATE_ADMIN permission)"""

        role = self.roles.get_role_by_id(role_id)
        admin=self.admins.get_admin_by_id(admin_id=targeting_admin_id)
        admin.assign_role(role.role_id, self.roles)
        self.admins.change_admin(admin=admin)
        return admin

    @require_permission(Permission.UPDATE_ADMIN)
    def remove_role_from_admin(self, requesting_admin_id: int,
                               targeting_admin_id: int, role_id: int) -> AdminAbstract:

        """Remove role from admin"""


        role=self.roles.get_role_by_id(role_id)
        admin = self.admins.get_admin_by_id(admin_id=targeting_admin_id)
        admin.remove_role(role.role_id)
        return admin

if __name__=="__main__":
    aggregate=AdminsAggregate()
    aggregate.create_admin(admin_id=1,name="admin1",email="1@11.ru",password="123567890",roles={1,2,3})
    aggregate.create_admin(admin_id=2, name="admin2", email="2@22.ru", password="123567890", roles={1, 2, 3})
    print(aggregate.get_all_admins())
    rr=RoleRegistry()
    admin_management_service=AdminManagementService(admins_aggregate=aggregate,roles_registry=rr)
    admin_management_service.disable_admin(requesting_admin_id=1,targeting_admin_id=2)

    print(aggregate.get_all_admins())