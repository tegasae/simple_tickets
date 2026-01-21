from contextlib import contextmanager
from typing import Generator

from src.domain.clients import Client
from src.domain.model import AdminsAggregate
from src.domain.permissions.rbac import Permission
from src.services.service_layer.base import BaseService, T


class ClientService(BaseService[Client]):
    def __init__(self, uow):
        super().__init__(uow)
        self.admin_roles_management_service = AdminRolesManagementService(
            roles_registry=RoleRegistry()
        )
        self.operation_methods = {
            'create': self._create_client,
            'get_by_name': self._get_client_by_name,
            'get_by_id': self._get_client_by_id,
            'update_email': self._update_client_email,
            'change_status': self._change_client_status,
            'update_phones': self._update_client_phones,
            'update_address':self._update_client_address,
            'update_name': self._update_client_name,
            'change_admin': self._change_admin,
            'remove_by_id': self._remove_admin_by_id
        }

    @contextmanager
    def _with_client_operation(self,
                              requesting_admin_id: int,
                              permission: Permission,
                              operation_name: str,
                              **log_details) -> Generator[AdminsAggregate, None, None]:

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

    def execute(self, requesting_admin_id: int, operation: str, **kwargs) -> Client | None:
        """All operations need to know WHO is performing them"""
        self._validate_input(**kwargs)


        if operation not in self.operation_methods:
            raise DomainOperationError(f"Unknown operation: {operation}")

        # Get requesting admin for validation
        requesting_admin = self._get_admin_by_id(requesting_admin_id)
        return self.operation_methods[operation](requesting_admin.admin_id, **kwargs)


    # Bulk operations
    def list_all_clients(self) -> list[Client]:


    def list_enabled_clients(self) -> list[Client]:


    def client_exists(self, name: str) -> bool:
