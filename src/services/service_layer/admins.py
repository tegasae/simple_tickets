# services/admin_service.py
from contextlib import contextmanager
from typing import List, Generator

from src.domain.exceptions import DomainOperationError
from src.domain.model import Admin, AdminsAggregate
from src.domain.permissions.rbac import RoleRegistry, Permission
from src.domain.services.roles_admins import AdminRolesManagementService

from src.services.service_layer.base import BaseService
from src.services.service_layer.data import CreateAdminData



class AdminService(BaseService[Admin]):
    """
    Service for admin management operations
    Handles business logic and coordinates with UoW
    """
    admins_aggregate: AdminsAggregate

    def __init__(self, uow):
        """В конструкторе инициализируется сервим доменного слоя для операций с админами.
        Именно там контролируются права.
        В дальнейшем RoleRegistry будем брать из базы.
        """
        super().__init__(uow)
        self.admin_roles_management_service=AdminRolesManagementService(roles_registry=RoleRegistry())

    @contextmanager
    def _with_admin_operation(self,
                              requesting_admin_id: int,
                              permission: Permission,
                              operation_name: str,
                              **log_details) -> Generator[AdminsAggregate, None, None]:
        """
        Context manager for admin operations:
        1. Logs operation
        2. Checks permissions
        3. Provides fresh aggregate
        4. Commits on success
        """
        # 1. Log
        self._log_operation(operation_name, **log_details)

        # 2. Check permissions
        self.check_admin_permissions(requesting_admin_id, permission)

        # 3. Get fresh aggregate
        with self.uow:
            aggregate = self._get_fresh_aggregate()
            yield aggregate  # Give aggregate to the operation

            # 4. Save and commit (only if no exception)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

    def check_admin_permissions(self, requesting_admin_id: int, permission: Permission):
        aggregate = self._get_fresh_aggregate()  # Get fresh aggregate
        requesting_admin = aggregate.get_admin_by_id(requesting_admin_id)
        self.admin_roles_management_service.check_permission(admin=requesting_admin, permission=permission)


    def _get_fresh_aggregate(self) -> AdminsAggregate:
        """Get fresh aggregate from UoW"""
        return self.uow.admins.get_list_of_admins()

    def execute(self, requesting_admin_id: int, operation: str, **kwargs) -> Admin | None:
        """All operations need to know WHO is performing them"""
        self._validate_input(requesting_admin_id=requesting_admin_id, operation=operation, **kwargs)
        """
        Main entry point for admin operations
        Uses a command pattern for different operations
        """
        # Get requesting admin first
        requesting_admin = self._get_admin_by_id(requesting_admin_id)



        operation_methods = {
            'create': self._create_admin,
            'get_by_name': self._get_admin_by_name,
            'get_by_id': self._get_admin_by_id,
            'update_email': self._update_admin_email,
            'toggle_status': self._toggle_admin_status,
            'change_password': self._change_admin_password,
            'remove_by_id': self._remove_admin_by_id,
            'assign_role': self._assign_role,  # New
            'remove_role': self._remove_role,  # New
        }

        if operation not in operation_methods:
            raise DomainOperationError(f"Unknown operation: {operation}")

        return operation_methods[operation](requesting_admin.admin_id, **kwargs)

    def _create_admin(self, requesting_admin_id: int, create_admin_data: CreateAdminData) -> Admin:
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.CREATE_ADMIN,
                operation_name="create_admin",
                name=create_admin_data.name,
                email=create_admin_data.email
        ) as aggregate:
            # Just business logic
            admin = aggregate.create_admin(
                admin_id=0,
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


    def _get_admin_by_name(self, name: str) -> Admin:
        """Get admin by name - throws exception if not found"""
        self._log_operation("get_admin_by_name", name=name)

        admins_aggregate = self._get_fresh_aggregate()
        return admins_aggregate.require_admin_by_name(name)

    def _get_admin_by_id(self, admin_id: int) -> Admin:

        """Get admin by ID - throws exception if not found"""
        self._log_operation("get_admin_by_id", admin_id=admin_id)
        with self.uow:
            aggregate = self._get_fresh_aggregate()  # Use helper
            return aggregate.get_admin_by_id(admin_id)

    def _update_admin_email(self,requesting_admin_id: int, targeting_admin_id:int, new_email: str) -> Admin:
        """Update admin email with validation"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_ADMIN,
                operation_name="update_admin_email",
                target_id=targeting_admin_id
        ) as aggregate:
            # Just the business logic!
            return aggregate.change_admin_email(targeting_admin_id, new_email)


    def _toggle_admin_status(self, requesting_admin_id: int, targeting_admin_id:int) -> Admin:
        """Toggle admin enabled/disabled status"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_ADMIN,
                operation_name="toggle_status",
                target_id=targeting_admin_id,
        ) as aggregate:
            # Just the business logic!
            if requesting_admin_id==targeting_admin_id:
                raise DomainOperationError(message="Admin can't change the status themself")
            return aggregate.toggle_admin_status(targeting_admin_id)


    def _change_admin_password(self, requesting_admin_id: int, targeting_admin_id:int,new_password:str) -> Admin:
        """Change admin password with validation"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_ADMIN,
                operation_name="change_password",
                target_id=targeting_admin_id,
        ) as aggregate:
            # Just the business logic!
            return aggregate.change_admin_password(targeting_admin_id,new_password=new_password)

    def _remove_admin_by_id(self, requesting_admin_id: int, targeting_admin_id: int) -> None:
        """Remove admin - requires DELETE_ADMIN permission"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.DELETE_ADMIN,
                operation_name="remove_by_id",
                target_id=targeting_admin_id,
        ) as aggregate:
            # Just the business logic!
            if requesting_admin_id==targeting_admin_id:
                raise DomainOperationError(message="Admin can't remove themself")
            aggregate.remove_admin_by_id(targeting_admin_id)

    # Bulk operations
    def list_all_admins(self) -> List[Admin]:
        """Get all admins"""
        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            return [admin for admin in aggregate.get_all_admins() if isinstance(admin, Admin)]

    def list_enabled_admins(self) -> List[Admin]:
        """Get only enabled admins"""
        with self.uow:
            admins_aggregate = self._get_fresh_aggregate()
            return [admin for admin in admins_aggregate.get_enabled_admins()]

    def admin_exists(self, name: str) -> bool:
        """Check if admin exists"""
        with self.uow:
            admins_aggregate = self._get_fresh_aggregate()
            return admins_aggregate.admin_exists(name)

    def _assign_role(self, requesting_admin_id: int, targeting_admin_id: int, role_id: int) -> Admin:
        """Assign role to admin - requires UPDATE_ADMIN permission"""

        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_ADMIN,
                operation_name="assign_role",
                target_id=targeting_admin_id,
        ) as aggregate:
            # Just the business logic!
            self.admin_roles_management_service.assign_role_to_admin(aggregate.get_admin_by_id(targeting_admin_id), role_id)
            return aggregate.get_admin_by_id(targeting_admin_id)


    def _remove_role(self, requesting_admin_id: int, targeting_admin_id: int, role_id: int) -> Admin:
        """Remove role to admin - requires UPDATE_ADMIN permission"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_ADMIN,
                operation_name="remove_role",
                target_id=targeting_admin_id,
        ) as aggregate:
            # Just the business logic!
            self.admin_roles_management_service.remove_role_from_admin(aggregate.get_admin_by_id(targeting_admin_id), role_id)
            return aggregate.get_admin_by_id(targeting_admin_id)

