# services/admin_service.py
from typing import List

from src.domain.exceptions import AdminOperationError
from src.domain.model import Admin, AdminAbstract
from src.services.service_layer.base import BaseService
from src.services.service_layer.data import CreateAdminData


class AdminService(BaseService[Admin]):
    """
    Service for admin management operations
    Handles business logic and coordinates with UoW
    """

    def execute(self, operation: str, **kwargs) -> AdminAbstract:
        """
        Main entry point for admin operations
        Uses a command pattern for different operations
        """
        self._validate_input(operation=operation, **kwargs)

        operation_methods = {
            'create': self._create_admin,
            'get_by_name': self._get_admin_by_name,
            'get_by_id': self._get_admin_by_id,
            'update_email': self._update_admin_email,
            'toggle_status': self._toggle_admin_status,
            'change_password': self._change_admin_password,
            'remove_by_id': self._remove_admin_by_id,
        }

        if operation not in operation_methods:
            raise AdminOperationError(f"Unknown operation: {operation}")

        return operation_methods[operation](**kwargs)

    def _create_admin(self, create_admin_data: CreateAdminData) -> AdminAbstract:
        """Create a new admin with validation"""
        self._log_operation("create_admin", name=create_admin_data.name, email=create_admin_data.email)


        try:
            with self.uow:
                aggregate = self.uow.admins.get_list_of_admins()

                # Create admin through aggregate
                aggregate.create_admin(
                    admin_id=0,  # Let database generate ID
                    name=create_admin_data.name,
                    email=create_admin_data.email,
                    password=create_admin_data.password,
                    enabled=create_admin_data.enabled
                )

                # Persist changes
                self.uow.admins.save_admins(aggregate)
                self.uow.commit()

                # ✅ GOOD: Reload to get database-generated ID and ensure consistency
                fresh_admin = self._get_admin_by_name(create_admin_data.name)

                if fresh_admin.admin_id == 0:
                    raise AdminOperationError("Admin was created but ID wasn't properly generated")

                return fresh_admin
        except AdminOperationError:
            raise  # Re-raise domain exceptions
        except Exception as e:
            self.logger.error(f"Unexpected error creating admin: {e}")
            raise AdminOperationError("Failed to create admin") from e

    def _get_admin_by_name(self, name: str) -> AdminAbstract:
        """Get admin by name - throws exception if not found"""
        self._log_operation("get_admin_by_name", name=name)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            return aggregate.require_admin_by_name(name)

    def _get_admin_by_id(self, admin_id: int) -> AdminAbstract:
        """Get admin by ID - throws exception if not found"""
        self._log_operation("get_admin_by_id", admin_id=admin_id)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()

            admin = aggregate.get_admin_by_id(admin_id=admin_id)
            return admin

    def _update_admin_email(self, name: str, new_email: str) -> AdminAbstract:
        """Update admin email with validation"""
        self._log_operation("update_admin_email", name=name, new_email=new_email)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()

            # This already throws if admin doesn't exist
            aggregate.require_admin_by_name(name)

            aggregate.change_admin_email(name, new_email)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

            return aggregate.require_admin_by_name(name)

    def _toggle_admin_status(self, name: str) -> AdminAbstract:
        """Toggle admin enabled/disabled status"""
        self._log_operation("toggle_admin_status", name=name)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            admin = aggregate.require_admin_by_name(name)

            aggregate.toggle_admin_status(name)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

            new_status = "enabled" if not admin.enabled else "disabled"
            self.logger.info(f"Admin {name} status toggled to {new_status}")
            return aggregate.require_admin_by_name(name)

    def _change_admin_password(self, name: str, new_password: str) -> AdminAbstract:
        """Change admin password with validation"""
        self._log_operation("change_admin_password", name=name)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            aggregate.require_admin_by_name(name)  # Validate existence

            aggregate.change_admin_password(name, new_password)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

            self.logger.info(f"Password changed for admin: {name}")
            return aggregate.require_admin_by_name(name)

    def _remove_admin_by_id(self, admin_id: int) -> None:
        """Remove admin by ID"""
        self._log_operation("remove_admin_by_id", admin_id=admin_id)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            aggregate.remove_admin_by_id(admin_id)
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

            self.logger.info(f"Admin removed: (ID: {admin_id})")

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
