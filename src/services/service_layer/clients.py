from contextlib import contextmanager
from typing import Generator

from src.domain.clients import Client
from src.domain.model import AdminsAggregate
from src.domain.permissions.rbac import Permission
from src.services.service_layer.base import BaseService, T
from src.services.service_layer.data import CreateClientData


class ClientService(BaseService[Client]):
    def __init__(self, uow):
        super().__init__(uow)

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


    def execute(self, requesting_admin_id: int, operation: str, **kwargs) -> Client | None:
        """All operations need to know WHO is performing them"""
        self._validate_input(**kwargs)


        if operation not in self.operation_methods:
            raise DomainOperationError(f"Unknown operation: {operation}")

        # Get requesting admin for validation
        requesting_admin = self._get_admin_by_id(requesting_admin_id)
        return self.operation_methods[operation](requesting_admin.admin_id, **kwargs)

    def _create_client(self, requesting_admin_id: int, create_admin_data: CreateClientData) -> Client:


    # Bulk operations
    def list_all_clients(self) -> list[Client]:


    def list_enabled_clients(self) -> list[Client]:


    def client_exists(self, name: str) -> bool:
