# services/client.py
from typing import Protocol, Optional


from src.domain.clients import Client
from src.domain.exceptions import ItemNotFoundError
from src.domain.model import AdminsAggregate
from src.domain.permissions.rbac import Permission
from src.domain.services.clients_admins import AdminClientManagementService
from src.services.service_layer.base import BaseService
from src.services.service_layer.data import CreateClientData
from src.services.uow.uowsqlite import AbstractUnitOfWork


class ServiceFactoryProtocol(Protocol):
    """Protocol for service factories"""

    def __call__(self, aggregate: AdminsAggregate, client: Client) -> AdminClientManagementService:
        ...


class ClientService(BaseService[Client]):
    """
    Service for client management operations
    Handles business logic and coordinates with UoW
    """

    def __init__(self,
                 uow: AbstractUnitOfWork,
                 service_factory: Optional[ServiceFactoryProtocol] = None):
        """
        Args:
            uow: Unit of Work for database operations
            service_factory: Factory to create AdminClientManagementService instances
                            Defaults to AdminClientManagementService class
        """
        super().__init__(uow)


        # Service factory (dependency injection for testability)
        self.service_factory = service_factory or AdminClientManagementService

    # ========== HELPER METHODS ==========

    def _execute_client_update(self,
                               requesting_admin_id: int,
                               client_id: int,
                               operation_name: str,
                               **update_kwargs) -> Client:
        """
        Helper method for all client update operations
        Handles: permissions, aggregate loading, service creation, saving
        """
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name=operation_name,
                client_id=client_id,
                **update_kwargs
        ) as aggregate:
            # Get client INSIDE transaction (fresh state)
            client = self.uow.clients_repository.get_client_by_id(client_id)
            if client.is_empty:
                raise ItemNotFoundError(f"Client ID {client_id} not found")

            # Create service instance
            service = self.service_factory(aggregate, client)

            # Execute update
            updated_client = service.update_client(**update_kwargs)

            # Persist changes
            self.uow.clients_repository.save_client(updated_client)
            return updated_client

    def _execute_client_creation(self,
                                 requesting_admin_id: int,
                                 create_client_data: CreateClientData) -> Client:
        """Helper for client creation"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.CREATE_CLIENT,
                operation_name="create_client",
                name=create_client_data.name,
                email=create_client_data.email
        ) as aggregate:
            # Determine admin ID (creator or specified)
            admin_id = create_client_data.admin_id or requesting_admin_id

            # Create service instance (no client yet)
            service = self.service_factory(aggregate, Client.empty_client())

            # Create client
            client = service.create_client(
                admin_id=admin_id,
                name=create_client_data.name,
                emails=create_client_data.email,
                address=create_client_data.address,
                phones=create_client_data.phones,
                enabled=create_client_data.enabled
            )

            # Persist
            self.uow.clients_repository.save_client(client)
            return client

    def _execute_client_deletion(self,
                                 requesting_admin_id: int,
                                 client_id: int) -> None:
        """Helper for client deletion"""
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.DELETE_CLIENT,  # Assuming you have this permission
                operation_name="delete_client",
                client_id=client_id
        ) as aggregate:
            # Get client
            client = self.uow.clients_repository.get_client_by_id(client_id)
            if client.is_empty:
                raise ItemNotFoundError(f"Client ID {client_id} not found")

            # Create service instance
            service = self.service_factory(aggregate, client)

            # Delete (business logic in domain service)
            service.delete_client()

            # Persist deletion
            self.uow.clients_repository.delete_client(client_id)

    # ========== OPERATION METHODS ==========

    def create_client(self,
                       requesting_admin_id: int,
                       create_client_data: CreateClientData) -> Client:
        """Create a new client"""
        return self._execute_client_creation(requesting_admin_id, create_client_data)

    def update_client_email(self,
                             requesting_admin_id: int,
                             client_id: int,
                             new_email: str) -> Client:
        """Update client email"""
        return self._execute_client_update(
            requesting_admin_id=requesting_admin_id,
            client_id=client_id,
            operation_name="update_client_email",
            emails=new_email
        )

    def change_client_status(self,
                              requesting_admin_id: int,
                              client_id: int,
                              enabled: bool) -> Client:
        """Enable/disable client"""
        return self._execute_client_update(
            requesting_admin_id=requesting_admin_id,
            client_id=client_id,
            operation_name="change_client_status",
            enabled=enabled
        )

    def update_client_phones(self,
                              requesting_admin_id: int,
                              client_id: int,
                              phones: str) -> Client:
        """Update client phone numbers"""
        return self._execute_client_update(
            requesting_admin_id=requesting_admin_id,
            client_id=client_id,
            operation_name="update_client_phones",
            phones=phones
        )

    def update_client_address(self,
                               requesting_admin_id: int,
                               client_id: int,
                               address: str) -> Client:
        """Update client address"""
        return self._execute_client_update(
            requesting_admin_id=requesting_admin_id,
            client_id=client_id,
            operation_name="update_client_address",
            address=address  # Fixed typo: was "adrress"
        )

    def update_client_name(self,
                            requesting_admin_id: int,
                            client_id: int,
                            name: str) -> Client:
        """Update client name"""
        return self._execute_client_update(
            requesting_admin_id=requesting_admin_id,
            client_id=client_id,
            operation_name="update_client_name",  # Fixed: was "update_client_address"
            name=name
        )

    def change_client_admin(self,
                             requesting_admin_id: int,
                             client_id: int,
                             admin_id: int = 0) -> Client:
        """Change which admin owns the client"""
        # Use requesting admin if not specified
        target_admin_id = admin_id if admin_id != 0 else requesting_admin_id

        return self._execute_client_update(
            requesting_admin_id=requesting_admin_id,
            client_id=client_id,
            operation_name="change_client_admin",
            admin_id=target_admin_id
        )

    def remove_client_by_id(self,  # Renamed for clarity
                             requesting_admin_id: int,
                             client_id: int) -> None:
        """Delete a client"""
        self._execute_client_deletion(requesting_admin_id, client_id)

    # ========== QUERY METHODS ==========

    def get_client_by_name(self, name: str) -> list[Client]:
        """Get all clients with matching name"""
        return [
            client for client in self.uow.clients_repository.get_all_clients()
            if client.name == name
        ]

    def get_client_by_id(self, client_id: int) -> Client:
        """Get client by ID (outside transaction - for queries only)"""
        client = self.uow.clients_repository.get_client_by_id(client_id)
        if client.is_empty:
            raise ItemNotFoundError(f"Client ID {client_id} not found")
        return client

    def get_all_clients(self) -> list[Client]:
        """Get all clients (for listing/display)"""
        return self.uow.clients_repository.get_all_clients()

    def get_enabled_clients(self) -> list[Client]:
        """Get only enabled clients"""
        return [
            client for client in self.get_all_clients()
            if client.enabled
        ]

    def get_clients_by_admin(self, admin_id: int) -> list[Client]:
        """Get all clients created by a specific admin"""
        return [
            client for client in self.get_all_clients()
            if client.admin_id == admin_id
        ]

    def client_exists(self, name: str) -> bool:
        """Check if a client with given name exists"""
        return any(client.name == name for client in self.get_all_clients())

    # ========== BULK OPERATIONS ==========

    def enable_all_clients(self, requesting_admin_id: int) -> list[Client]:
        """Enable all clients (requires permission)"""
        enabled_clients = []

        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name="enable_all_clients"
        ) as aggregate:

            for client in self.get_all_clients():
                if not client.enabled:
                    service = self.service_factory(aggregate, client)
                    enabled_client = service.update_client(enabled=True)
                    self.uow.clients_repository.save_client(enabled_client)
                    enabled_clients.append(enabled_client)

            return enabled_clients

    def disable_all_clients(self, requesting_admin_id: int) -> list[Client]:
        """Disable all clients (requires permission)"""
        disabled_clients = []

        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name="disable_all_clients"
        ) as aggregate:

            for client in self.get_all_clients():
                if client.enabled:
                    service = self.service_factory(aggregate, client)
                    disabled_client = service.update_client(enabled=False)
                    self.uow.clients_repository.save_client(disabled_client)
                    disabled_clients.append(disabled_client)

            return disabled_clients