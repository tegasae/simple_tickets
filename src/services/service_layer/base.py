# services/base.py
from abc import ABC
from contextlib import contextmanager
from typing import Generic, TypeVar, Generator, overload
import logging

from src.domain.exceptions import DomainOperationError
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


class BaseService(ABC, Generic[T]):
    """
    Base service class with common functionality
    All services should inherit from this
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.admin_roles_management_service = AdminRolesManagementService(
            roles_registry=RoleRegistry()
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.operation_methods={}

    def _check_admin_permissions(self, requesting_admin_id: int, permission: Permission):
        """Check if admin has permission"""
        aggregate = self._get_fresh_aggregate()
        requesting_admin = aggregate.get_admin_by_id(requesting_admin_id)
        self.admin_roles_management_service.check_permission(
            admin=requesting_admin,
            permission=permission
        )

    def _get_fresh_aggregate(self) -> AdminsAggregate:
        """Get fresh aggregate from UoW"""
        return self.uow.admins.get_list_of_admins()

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
        self._check_admin_permissions(requesting_admin_id, permission)

        # 3. Get fresh aggregate and execute
        with self.uow:
            aggregate = self._get_fresh_aggregate()
            yield aggregate  # Give aggregate to the operation

            # 4. Save and commit (only if no exception)

            self.uow.admins.save_admins(aggregate)
            self.uow.commit()

    def _get_admin_by_id(self, admin_id: int) -> Admin:
        """Get admin by ID"""
        aggregate = self._get_fresh_aggregate()
        admin = aggregate.get_admin_by_id(admin_id)
        if admin.is_empty():
            raise DomainOperationError(f"Admin ID {admin_id} not found")
        return admin


    @overload
    def execute(self, requesting_admin_id: int, operation: str, **kwargs) -> None:
        ...

    @overload
    def execute(self, requesting_admin_id: int, operation: str, **kwargs) -> T:
        ...

    @overload
    def execute(self, requesting_admin_id: int, operation: str, **kwargs) -> list[T]:
        ...

    def execute(self, requesting_admin_id: int, operation: str, **kwargs) -> T|list[T]|None:
        """All operations need to know WHO is performing them"""
        _validate_input(**kwargs)

        if operation not in self.operation_methods:
            raise DomainOperationError(f"Unknown operation: {operation}")

        # Get requesting admin for validation
        requesting_admin = self._get_admin_by_id(requesting_admin_id)
        return self.operation_methods[operation](requesting_admin.admin_id, **kwargs)

    def _log_operation(self, operation: str, **details) -> None:
        """Structured logging for service operations"""
        self.logger.info(f"{operation} - {details}")