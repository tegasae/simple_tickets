# services/admin_service.py

from src.domain.exceptions import DomainOperationError
from src.domain.model import Admin
from src.domain.permissions.rbac import Permission


from src.services.service_layer.base import BaseService
from src.services.service_layer.data import CreateAdminData


class AdminService(BaseService[Admin]):
    """
    Service for admin management operations
    Handles business logic and coordinates with UoW
    """

    def __init__(self, uow):
        super().__init__(uow)

        self.operation_methods = {
            'create': self._create_admin,
            'get_by_id': self._get_admin_by_id,
            'update_email': self._update_admin_email,
            'toggle_status': self._toggle_admin_status,
            'change_password': self._change_admin_password,
            'remove_by_id': self._remove_admin_by_id,
            'assign_role': self._assign_role,
            'remove_role': self._remove_role,
        }



    def _create_admin(self, requesting_admin_id: int, create_admin_data: CreateAdminData) -> Admin:
        """Create a new admin"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.CREATE_ADMIN,
                operation_name="create_admin",
                name=create_admin_data.name,
                email=create_admin_data.email
        ) as aggregate:
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
            fresh_admin = aggregate.require_admin_by_name(create_admin_data.name)
            if fresh_admin.admin_id == 0:
                raise DomainOperationError("Admin was created but ID wasn't properly generated")

            return fresh_admin



    def get_admin_by_name(self, name: str) -> Admin:
        """Get admin by name"""
        aggregate = self._get_fresh_aggregate()
        return aggregate.require_admin_by_name(name)


    def _update_admin_email(self,
                            requesting_admin_id: int,
                            target_admin_id: int,
                            new_email: str) -> Admin:
        """Update admin email"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_ADMIN,
                operation_name="update_admin_email",
                target_id=target_admin_id,
                new_email=new_email
        ) as aggregate:
            return aggregate.change_admin_email(target_admin_id, new_email)

    def _toggle_admin_status(self,
                             requesting_admin_id: int,
                             target_admin_id: int) -> Admin:


        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_ADMIN,
                operation_name="toggle_admin_status",
                target_id=target_admin_id
        ) as aggregate:
            return aggregate.toggle_admin_status(target_admin_id)

    def _change_admin_password(self,
                               requesting_admin_id: int,
                               target_admin_id: int,
                               new_password: str) -> Admin:
        """Change admin password"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_ADMIN,
                operation_name="change_admin_password",
                target_id=target_admin_id
        ) as aggregate:
            return aggregate.change_admin_password(target_admin_id, new_password)

    def _remove_admin_by_id(self,
                            requesting_admin_id: int,
                            target_admin_id: int) -> None:
        """Remove admin"""
        if requesting_admin_id == target_admin_id:
            raise DomainOperationError("Admin cannot delete themselves")

        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.DELETE_ADMIN,
                operation_name="remove_admin_by_id",
                target_id=target_admin_id
        ) as aggregate:
            aggregate.remove_admin_by_id(target_admin_id)

    def _assign_role(self,
                     requesting_admin_id: int,
                     target_admin_id: int,
                     role_id: int) -> Admin:
        """Assign role to admin"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_ADMIN,  # Fixed!
                operation_name="assign_role",
                target_id=target_admin_id,
                role_id=role_id
        ) as aggregate:
            admin = aggregate.get_admin_by_id(target_admin_id)
            self.admin_roles_management_service.assign_role_to_admin(admin, role_id)
            return admin

    def _remove_role(self,
                     requesting_admin_id: int,
                     target_admin_id: int,
                     role_id: int) -> Admin:
        """Remove role from admin"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_ADMIN,  # Fixed!
                operation_name="remove_role",
                target_id=target_admin_id,
                role_id=role_id
        ) as aggregate:
            admin = aggregate.get_admin_by_id(target_admin_id)
            self.admin_roles_management_service.remove_role_from_admin(admin, role_id)
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