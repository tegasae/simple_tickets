# services/admin_service.py
from typing import List

from src.domain.exceptions import DomainOperationError
from src.domain.model import Admin, AdminAbstract
from src.domain.permissions.rbac import RoleRegistry
from src.domain.services.admins import AdminManagementService
from src.services.service_layer.base import BaseService
from src.services.service_layer.data import CreateAdminData


class AdminService(BaseService[Admin]):
    """
    Service for admin management operations
    Handles business logic and coordinates with UoW
    """

    def __init__(self, uow):
        """В конструкторе инициализируется сервим доменного слоя для операций с админами.
        Именно там контролируются права.
        В дальнейшем RoleRegistry будем брать из базы.
        """
        super().__init__(uow)
        self.role_registry = RoleRegistry()
        self.admins_aggregate = self.uow.admins.get_list_of_admins()
        self.admin_management_service = AdminManagementService(admins_aggregate=self.admins_aggregate,
                                                               roles_registry=self.role_registry)

    def execute(self, requesting_admin_id: int, operation: str, **kwargs) -> AdminAbstract:
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

    def _create_admin(self, requesting_admin_id: int, create_admin_data: CreateAdminData) -> AdminAbstract:
        """Create a new admin with validation"""
        """Создание админа происходит через сервис доменного слоя. UoW предоставляет аггрегат"""
        self._log_operation("create_admin", name=create_admin_data.name, email=create_admin_data.email)

        try:
            with self.uow:
                self.admin_management_service.admins=self.uow.admins.get_list_of_admins()
                # Create admin through aggregate
                self.admin_management_service.create_admin(requesting_admin_id=requesting_admin_id,
                                                           name=create_admin_data.name,
                                                           email=create_admin_data.email,
                                                           password=create_admin_data.password,
                                                           enabled=create_admin_data.enabled,
                                                           roles=create_admin_data.roles
                                                           )


                # Persist changes

                self.uow.admins.save_admins(self.admins_aggregate)
                self.uow.commit()

                # ✅ GOOD: Reload to get database-generated ID and ensure consistency
                fresh_admin = self._get_admin_by_name(create_admin_data.name)
                if fresh_admin.admin_id == 0:
                    raise DomainOperationError("Admin was created but ID wasn't properly generated")

                return fresh_admin
        except DomainOperationError:
            raise  # Re-raise domain exceptions
        except Exception as e:
            self.logger.error(f"Unexpected error creating admin: {e}")
            #raise AdminOperationError("Failed to create admin") from e
            raise

    def _get_admin_by_name(self, name: str) -> AdminAbstract:
        """Get admin by name - throws exception if not found"""
        self._log_operation("get_admin_by_name", name=name)

        aggregate = self.uow.admins.get_list_of_admins()
        return aggregate.require_admin_by_name(name)

    def _get_admin_by_id(self, admin_id: int) -> AdminAbstract:

        """Get admin by ID - throws exception if not found"""
        self._log_operation("get_admin_by_id", admin_id=admin_id)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()

            admin = aggregate.get_admin_by_id(admin_id=admin_id)
            return admin

    def _update_admin_email(self,requesting_admin_id: int, targeting_admin_id:int, new_email: str) -> AdminAbstract:
        """Update admin email with validation"""
        self._log_operation("update_admin_email", id=targeting_admin_id, new_email=new_email)

        with self.uow:
            self.admin_management_service.admins = self.uow.admins.get_list_of_admins()

            admin=self._get_admin_by_id(admin_id=targeting_admin_id)

            admin.email=new_email
            admin=self.admin_management_service.update_admin(requesting_admin_id=requesting_admin_id,new_admin=admin)
            self.uow.admins.save_admins(self.admin_management_service.admins)
            self.uow.commit()

            return admin

    def _toggle_admin_status(self, requesting_admin_id: int, targeting_admin_id:int) -> AdminAbstract:
        """Toggle admin enabled/disabled status"""
        self._log_operation("toggle_admin_status", id=targeting_admin_id)

        with self.uow:
            self.admin_management_service.admins = self.uow.admins.get_list_of_admins()
            admin = self._get_admin_by_id(admin_id=targeting_admin_id)
            admin.enabled=not admin.enabled
            self.admin_management_service.update_admin(requesting_admin_id=requesting_admin_id,new_admin=admin)
            self.uow.admins.save_admins(self.admin_management_service.admins)
            self.uow.commit()

            new_status = "enabled" if not admin.enabled else "disabled"
            self.logger.info(f"Admin {admin.name} status toggled to {new_status}")
            return admin

    def _change_admin_password(self, requesting_admin_id: int, targeting_admin_id:int,new_password:str) -> AdminAbstract:
        """Change admin password with validation"""
        self._log_operation("change_admin_password", id=targeting_admin_id)

        with self.uow:
            self.admin_management_service.admins = self.uow.admins.get_list_of_admins()
            admin = self._get_admin_by_id(admin_id=targeting_admin_id)
            admin.password=new_password
            self.admin_management_service.update_admin(requesting_admin_id=requesting_admin_id,new_admin=admin)

            #aggregate.change_admin_password(name, new_password)
            self.uow.admins.save_admins(self.admin_management_service.admins)
            self.uow.commit()

            self.logger.info(f"Password changed for admin: {admin.name}")
            return admin

    def _remove_admin_by_id(self, requesting_admin_id: int, admin_id: int) -> None:
        """Remove admin - requires DELETE_ADMIN permission"""
        self._log_operation("remove_admin_by_id",
                            requester=requesting_admin_id,
                            target=admin_id)

        # Can't delete yourself
        if requesting_admin_id == admin_id:
            raise DomainOperationError("Admin cannot delete themselves")

        with self.uow:
            self.admin_management_service.delete_admin(
                requesting_admin_id=requesting_admin_id,
                admin_to_delete_id=admin_id
            )

            # Persist
            self.uow.admins.save_admins(self.admin_management_service.admins)
            self.uow.commit()

            self.logger.info(f"Admin {admin_id} removed by admin {requesting_admin_id}")

    # Bulk operations
    def list_all_admins(self) -> List[Admin]:
        """Get all admins"""
        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            return [admin for admin in aggregate.get_all_admins() if isinstance(admin, Admin)]

    def list_enabled_admins(self) -> List[Admin]:
        """Get only enabled admins"""
        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            return [admin for admin in aggregate.get_enabled_admins() if isinstance(admin, Admin)]

    def admin_exists(self, name: str) -> bool:
        """Check if admin exists"""
        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            return aggregate.admin_exists(name)

    def _assign_role(self, requesting_admin_id: int, targeting_admin_id: int, role_id: int) -> AdminAbstract:
        """Assign role to admin - requires UPDATE_ADMIN permission"""

        self._log_operation("assign_role",
                            requester=requesting_admin_id,
                            target=targeting_admin_id,
                            role=role_id)

        with self.uow:
            self.admin_management_service.admins = self.uow.admins.get_list_of_admins()


            # Assign role (includes permission check)
            self.admin_management_service.assign_role_to_admin(
                requesting_admin_id=requesting_admin_id,
                target_admin_id=targeting_admin_id,
                role_id=role_id
            )

            # Persist
            self.uow.admins.save_admins(self.admin_management_service.admins)
            self.uow.commit()


            return self.admin_management_service.admins.get_admin_by_id(targeting_admin_id)

    def _remove_role(self,requesting_admin_id: int, targeting_admin_id: int, role_id: int):
        self._log_operation("remove_role",
                            requester=requesting_admin_id,
                            target=targeting_admin_id,
                            role=role_id)

        with self.uow:
            self.admin_management_service.admins = self.uow.admins.get_list_of_admins()

            # Assign role (includes permission check)
            self.admin_management_service.remove_role_from_admin(
                requesting_admin_id=requesting_admin_id,
                target_admin_id=targeting_admin_id,
                role_id=role_id
            )

            # Persist
            self.uow.admins.save_admins(self.admin_management_service.admins)
            self.uow.commit()
