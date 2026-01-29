# services/base.py
from abc import ABC
from contextlib import contextmanager
from functools import wraps
from typing import Generic, TypeVar, Generator, Optional
import logging

from src.domain.exceptions import DomainOperationError, DomainSecurityError
from src.domain.model import AdminsAggregate, Admin
from src.domain.permissions.rbac import RoleRegistry, Permission
from src.domain.services.roles_admins import AdminRolesManagementService
from src.services.uow.uowsqlite import AbstractUnitOfWork

logger = logging.getLogger(__name__)

T = TypeVar('T')


def _validate_input(**kwargs) -> None:
    """Common input validation - can be overridden by subclasses"""
    for key, value in kwargs.items():
        if value is None:
            raise ValueError(f"Parameter '{key}' cannot be None")

def with_permission_check(permission: Permission):
    """Decorator that checks permissions using self.requesting_admin"""

    def decorator(func):
        @wraps(func)
        def wrapper(self_instance:BaseService[T], *args, **kwargs):
            # Check if requesting_admin is set
            if not hasattr(self_instance, 'requesting_admin'):
                raise DomainSecurityError(
                    "No admin set. Call set_requesting_admin() first."
                )

            if self_instance.requesting_admin is None:
                raise DomainSecurityError("No admin authenticated")

            # Check permission
            self_instance.admin_roles_management_service.check_permission(
                admin=self_instance.requesting_admin,
                permission=permission
            )

            # Execute original method
            return func(self_instance, *args, **kwargs)

        return wrapper

    return decorator



class BaseService(ABC, Generic[T]):
    """
    Base service class with common functionality
    All services should inherit from this
    """

    def __init__(self, uow: AbstractUnitOfWork, requesting_admin_name: str = "",requesting_admin_id: int = 0):
        self.uow = uow
        self.admin_roles_management_service = AdminRolesManagementService(
            roles_registry=RoleRegistry()
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.operation_methods={}
        self.requesting_admin: Admin = Admin.create_empty()  # Store Admin object
        if requesting_admin_name:
            self.requesting_admin = self.uow.admins_repository.get_list_of_admins().get_admin_by_name(
                requesting_admin_name)
        if requesting_admin_id:
            self.requesting_admin = self.uow.admins_repository.get_by_id(requesting_admin_id)

    def _check_admin_permissions(self,
                                 aggregate: AdminsAggregate,  # Receive aggregate
                                 requesting_admin_id: int,
                                 permission: Permission):
        """Check if admin has permission using provided aggregate"""
        requesting_admin = aggregate.get_admin_by_id(requesting_admin_id)
        self.admin_roles_management_service.check_permission(
            admin=requesting_admin,
            permission=permission
        )

    def set_requesting_admin_name(self,requesting_admin_name: str):
        self.requesting_admin=self.uow.admins_repository.get_list_of_admins().get_admin_by_name(
                requesting_admin_name)

    def _get_fresh_aggregate(self) -> AdminsAggregate:
        """Get fresh aggregate from UoW"""
        return self.uow.admins.get_list_of_admins()


    def set_requesting_admin(self, admin: Admin) -> None:
        """Set the currently authenticated admin"""
        self.requesting_admin = admin

    def clear_requesting_admin(self) -> None:
        """Clear the current admin"""
        self.requesting_admin = None

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

        # 3. Get fresh aggregate and execute
        with self.uow:
            aggregate = self._get_fresh_aggregate()
            self._check_admin_permissions(aggregate,requesting_admin_id, permission)

            yield aggregate  # Give aggregate to the operation

            # 4. Save and commit (only if no exception)

            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

    def get_admin_by_id(self, admin_id: int) -> Admin:
        """Get admin by ID"""
        aggregate = self._get_fresh_aggregate()
        admin = aggregate.get_admin_by_id(admin_id)
        if admin.is_empty():
            raise DomainOperationError(f"Admin ID {admin_id} not found")
        return admin



    def _log_operation(self, operation: str, **details) -> None:
        """Structured logging for service operations"""
        self.logger.info(f"{operation} - {details}")