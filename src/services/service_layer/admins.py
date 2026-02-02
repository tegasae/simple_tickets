# services/admin_service.py
from functools import wraps


from src.domain.exceptions import DomainOperationError
from src.domain.model import Admin
from src.domain.permissions.permission import PermissionAdmin
from src.domain.services.admins import AdminManagementService

from src.services.service_layer.base import BaseService, with_permission_check
from src.services.service_layer.data import CreateAdminData

from src.services.uow.uowsqlite import AbstractUnitOfWork


def with_permission_check_old(permission: PermissionAdmin):
    """Meta-decorator that works with instance methods"""

    def decorator(func):
        @wraps(func)
        def wrapper(self_instance, *args, **kwargs):
            # Type hint for IDE
            self: AdminService = self_instance

            self.admin_roles_management_service.check_permission(
                admin=self.requesting_admin,
                permission=permission
            )

            # Execute original method
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class AdminService(BaseService[Admin]):
    """
    Service for admin management operations
    Handles business logic and coordinates with UoW
    """

    def __init__(self, uow: AbstractUnitOfWork, requesting_admin_name="", requesting_admin_id=0):
        super().__init__(uow,requesting_admin_name, requesting_admin_id)
        self.management_service = AdminManagementService(
            client_repository=uow.clients_repository
        )



    @with_permission_check(PermissionAdmin.CREATE_ADMIN)
    def create_admin(self, create_admin_data: CreateAdminData) -> Admin:
        """Create a new admin"""
        with self.uow:
            aggregate = self._get_fresh_aggregate()
            # Create admin
            aggregate.create_admin(
                admin_id=0,  # Let DB generate ID
                name=create_admin_data.name,
                email=create_admin_data.email,
                enabled=create_admin_data.enabled,
                password=create_admin_data.password,
                roles=create_admin_data.roles
            )

            # Verify ID was generated
            self.uow.admins.save_admins(aggregate)
            aggregate = self._get_fresh_aggregate()
            fresh_admin = aggregate.require_admin_by_name(create_admin_data.name)

            if fresh_admin.admin_id == 0:
                raise DomainOperationError("Admin was created but ID wasn't properly generated")
            self.uow.commit()

        return fresh_admin

    def get_admin_by_name(self, name: str) -> Admin:
        """Get admin by name"""
        aggregate = self._get_fresh_aggregate()
        return aggregate.require_admin_by_name(name)

    @with_permission_check(PermissionAdmin.UPDATE_ADMIN)
    def update_admin_email(self,
                           target_admin_id: int,
                           new_email: str) -> Admin:
        """Update admin email"""
        with self.uow:
            aggregate = self._get_fresh_aggregate()
            admin = aggregate.change_admin_email(target_admin_id, new_email)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()
            return admin

    @with_permission_check(PermissionAdmin.UPDATE_ADMIN)
    def change_admin_status(self,
                            target_admin_id: int, enabled: bool) -> Admin:

        with self.uow:
            aggregate = self._get_fresh_aggregate()
            admin = aggregate.change_admin_status(target_admin_id, enabled=enabled)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()
            return admin

    @with_permission_check(PermissionAdmin.UPDATE_ADMIN)
    def change_admin_password(self,
                              target_admin_id: int,
                              new_password: str) -> Admin:
        """Change admin password"""
        with self.uow:
            aggregate = self._get_fresh_aggregate()
            admin = aggregate.change_admin_password(target_admin_id, new_password)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()
            return admin

    @with_permission_check(PermissionAdmin.DELETE_ADMIN)
    def remove_admin_by_id(self,
                           target_admin_id: int) -> None:
        """Remove admin"""

        if self.requesting_admin.admin_id == target_admin_id:
            raise DomainOperationError("Admin cannot delete themselves")
        with self.uow:
            aggregate = self._get_fresh_aggregate()
            self.management_service.delete_admin(admin_id=target_admin_id, aggregate=aggregate)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

    @with_permission_check(PermissionAdmin.UPDATE_ADMIN)
    def assign_role(self,
                    target_admin_id: int,
                    role_id: int) -> Admin:
        """Assign role to admin"""
        with self.uow:
            aggregate = self._get_fresh_aggregate()
            admin = aggregate.get_admin_by_id(target_admin_id)
            self.admin_roles_management_service.assign_role_to_admin(admin, role_id)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()
            return admin

    @with_permission_check(PermissionAdmin.UPDATE_ADMIN)
    def remove_role(self,
                    target_admin_id: int,
                    role_id: int) -> Admin:
        """Remove role from admin"""
        with self.uow:
            aggregate = self._get_fresh_aggregate()
            admin = aggregate.get_admin_by_id(target_admin_id)
            self.admin_roles_management_service.remove_role_from_admin(admin, role_id)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()
            return admin

    # Bulk operations
    def list_all_admins(self) -> list[Admin]:
        """Get all admins"""
        aggregate = self._get_fresh_aggregate()
        return aggregate.get_all_admins()

    def list_enabled_admins(self) -> list[Admin]:
        """Get only enabled admins"""
        aggregate = self._get_fresh_aggregate()
        return aggregate.get_enabled_admins()

    def admin_exists(self, name: str) -> bool:
        """Check if admin exists"""
        aggregate = self._get_fresh_aggregate()
        return aggregate.admin_exists(name)
