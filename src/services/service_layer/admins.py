# services/admin_service.py
from typing import List
from src.domain.model import Admin, AdminsAggregate, AdminAbstract
from src.services.service_layer.base import BaseService
from src.services.service_layer.data import CreateAdminData


class AdminService(BaseService[Admin]):
    """
    Service for admin management operations
    Handles business logic and coordinates with UoW
    """

    def execute(self, operation: str, **kwargs) -> Admin:
        """
        Main entry point for admin operations
        Uses a command pattern for different operations
        """
        self._validate_input(operation=operation, **kwargs)

        operation_methods = {
            'create': self._create_admin,
            'get_by_name': self._get_admin_by_name,
            'update_email': self._update_admin_email,
            'toggle_status': self._toggle_admin_status,
            'change_password': self._change_admin_password,
        }

        if operation not in operation_methods:
            raise ValueError(f"Unknown operation: {operation}")

        return operation_methods[operation](**kwargs)

    def _create_admin(self, create_admin_data: CreateAdminData) -> AdminAbstract:
        """Create a new admin with validation"""
        try:
            self._log_operation("create_admin", name=create_admin_data.name, email=create_admin_data.email)

            with self.uow:
                aggregate = self.uow.admins.get_list_of_admins()

                # Business logic validation
                if aggregate.admin_exists(create_admin_data.name):
                    raise ValueError(f"Admin with name '{create_admin_data.name}' already exists")

                # Create admin through aggregate (enforces business rules)
                admin = aggregate.create_admin(
                    admin_id=0,
                    name=create_admin_data.name,
                    email=create_admin_data.email,
                    password=create_admin_data.password,
                    enabled=create_admin_data.enabled
                )

                # Persist changes
                self.uow.admins.save_admins(aggregate)
                admin_aggregate = self.uow.admins.get_list_of_admins()
                created_admin = admin_aggregate.get_admin_by_name(name=create_admin_data.name)
                if not isinstance(admin, Admin):
                    raise ValueError(f"Admin didn't create successfully: {create_admin_data.name}")
                if created_admin.admin_id == 0:
                    raise ValueError("Admin was created but ID wasn't properly generated")
                self.uow.commit()

                self.logger.info(f"Admin created successfully: {create_admin_data.name}")
                return created_admin
        except ValueError as e:
            self.logger.error(f"Failed to create admin: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating admin: {e}")
            raise RuntimeError("Failed to create admin") from e

    def _get_admin_by_name(self, name: str) -> AdminAbstract:
        """Get admin by name - throws exception if not found"""
        self._log_operation("get_admin_by_name", name=name)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            admin = aggregate.require_admin_by_name(name)
            return admin

    def _update_admin_email(self, name: str, new_email: str) -> AdminAbstract:
        """Update admin email with validation"""
        self._log_operation("update_admin_email", name=name, new_email=new_email)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()

            if not aggregate.admin_exists(name):
                raise ValueError(f"Admin '{name}' not found")

            # Update through aggregate (enforces business rules)
            aggregate.change_admin_email(name, new_email)

            # Persist changes
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

            # Return updated admin
            return aggregate.require_admin_by_name(name)

    def _toggle_admin_status(self, name: str) -> AdminAbstract:
        """Toggle admin enabled/disabled status"""
        self._log_operation("toggle_admin_status", name=name)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            admin = aggregate.require_admin_by_name(name)

            aggregate.toggle_admin_status(name)

            # Persist changes
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

            new_status = "enabled" if admin.enabled else "disabled"
            self.logger.info(f"Admin {name} status toggled to {new_status}")
            return aggregate.require_admin_by_name(name)

    def _change_admin_password(self, name: str, new_password: str) -> AdminAbstract:
        """Change admin password with validation"""
        self._log_operation("change_admin_password", name=name)

        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()

            if not aggregate.admin_exists(name):
                raise ValueError(f"Admin '{name}' not found")

            # Update through aggregate
            aggregate.change_admin_password(name, new_password)

            # Persist changes
            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

            self.logger.info(f"Password changed for admin: {name}")
            return aggregate.require_admin_by_name(name)

        # Bulk operations

    def list_all_admins(self) -> List[AdminAbstract]:
        """Get all admins"""
        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            return aggregate.get_all_admins()

    def list_enabled_admins(self) -> List[AdminAbstract]:
        """Get only enabled admins"""
        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            return aggregate.get_enabled_admins()

    def admin_exists(self, name: str) -> bool:
        """Check if admin exists"""
        with self.uow:
            aggregate = self.uow.admins.get_list_of_admins()
            return aggregate.admin_exists(name)
