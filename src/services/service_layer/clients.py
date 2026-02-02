# services/client.py



from src.domain.clients import Client
from src.domain.exceptions import ItemNotFoundError, DomainOperationError

from src.domain.permissions.permission import PermissionAdmin
from src.domain.services.clients_admins import AdminClientManagementService
from src.services.service_layer.base import BaseService, with_permission_check
from src.services.service_layer.data import CreateClientData
from src.services.uow.uowsqlite import AbstractUnitOfWork


class ClientService(BaseService[Client]):
    """
    Service for client management operations
    Follows same pattern as AdminService
    """

    def __init__(self, uow: AbstractUnitOfWork, requesting_admin_name: str = ""):
        super().__init__(uow, requesting_admin_name)
        # Client service doesn't need additional services in constructor
        # Domain service (AdminClientManagementService) is created per-operation

    # ========== CRUD OPERATIONS ==========

    @with_permission_check(PermissionAdmin.CREATE_CLIENT)
    def create_client(self, create_client_data: CreateClientData) -> Client:
        """Create a new client"""
        with (self.uow):


            # Create domain service
            service = AdminClientManagementService()

            # Determine admin ID (creator or specified)
            admin_id = create_client_data.admin_id or self.requesting_admin.admin_id

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
            self.uow.commit()

            return client

    @with_permission_check(PermissionAdmin.UPDATE_CLIENT)
    def update_client_email(self, client_id: int, new_email: str) -> Client:
        """Update client email"""
        return self._update_client_attribute(
            client_id=client_id,
            new_value=new_email,
            domain_service_method=lambda svc, val: svc.update_client(emails=val)
        )

    @with_permission_check(PermissionAdmin.UPDATE_CLIENT)
    def change_client_status(self, client_id: int, enabled: bool) -> Client:
        """Enable/disable client"""
        return self._update_client_attribute(
            client_id=client_id,
            new_value=enabled,
            domain_service_method=lambda svc, val: svc.update_client(enabled=val)
        )

    @with_permission_check(PermissionAdmin.UPDATE_CLIENT)
    def update_client_phones(self, client_id: int, phones: str) -> Client:
        """Update client phone numbers"""
        return self._update_client_attribute(
            client_id=client_id,
            new_value=phones,
            domain_service_method=lambda svc, val: svc.update_client(phones=val)
        )

    @with_permission_check(PermissionAdmin.UPDATE_CLIENT)
    def update_client_address(self, client_id: int, address: str) -> Client:
        """Update client address"""
        return self._update_client_attribute(
            client_id=client_id,
            new_value=address,
            domain_service_method=lambda svc, val: svc.update_client(address=val)
        )

    @with_permission_check(PermissionAdmin.UPDATE_CLIENT)
    def update_client_name(self, client_id: int, name: str) -> Client:
        """Update client name"""
        return self._update_client_attribute(
            client_id=client_id,
            new_value=name,
            domain_service_method=lambda svc, val: svc.update_client(name=val)
        )

    @with_permission_check(PermissionAdmin.UPDATE_CLIENT)
    def change_client_admin(self, client_id: int, new_admin_id: int) -> Client:
        """Change which admin owns the client"""
        # Prevent transferring to invalid admin
        if new_admin_id <= 0:
            raise DomainOperationError("Invalid admin ID")

        return self._update_client_attribute(
            client_id=client_id,
            new_value=new_admin_id,
            domain_service_method=lambda svc, val: svc.update_client(admin_id=val)
        )

    @with_permission_check(PermissionAdmin.DELETE_CLIENT)
    def remove_client_by_id(self, client_id: int) -> None:
        """Delete a client"""
        with self.uow:


            # Get client
            client = self.uow.clients_repository.get_client_by_id(client_id)
            if client.is_empty:
                raise ItemNotFoundError(f"Client ID {client_id} not found")

            # Check if client is already deleted
            if client.is_deleted:
                raise DomainOperationError(f"Client {client.name} is already deleted")

            # Create domain service
            service = AdminClientManagementService(
                client=client
            )

            # Delete client (business logic in domain service)
            service.delete_client()

            # Mark as deleted (soft delete) or remove (hard delete)
            # Depending on your requirements:
            # Option 1: Hard delete
            # self.uow.clients.delete_client(client_id)

            # Option 2: Soft delete (recommended)
            client.is_deleted = True
            self.uow.clients_repository.save_client(client)

            self.uow.commit()

    # ========== QUERY METHODS (no permission needed) ==========

    def get_client_by_id(self, client_id: int) -> Client:
        """Get client by ID"""
        client = self.uow.clients_repository.get_client_by_id(client_id)
        if client.is_empty:
            raise ItemNotFoundError(f"Client ID {client_id} not found")
        return client

    def get_client_by_name(self, name: str) -> list[Client]:
        """Get all clients with matching name"""
        return [
            client for client in self.uow.clients_repository.get_all_clients()
            if client.name.value == name and not client.is_deleted
        ]

    def get_all_clients(self) -> list[Client]:
        """Get all non-deleted clients"""
        return [
            client for client in self.uow.clients_repository.get_all_clients()
            if not client.is_deleted
        ]

    def get_enabled_clients(self) -> list[Client]:
        """Get only enabled, non-deleted clients"""
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

    def get_my_clients(self) -> list[Client]:
        """Get clients created by the currently authenticated admin"""
        if not self.requesting_admin:
            raise DomainOperationError("No authenticated admin")

        return self.get_clients_by_admin(self.requesting_admin.admin_id)

    def client_exists(self, name: str) -> bool:
        """Check if a client with given name exists (non-deleted)"""
        return any(
            client.name.value == name and not client.is_deleted
            for client in self.uow.clients_repository.get_all_clients()
        )

    # ========== BULK OPERATIONS ==========

    @with_permission_check(PermissionAdmin.UPDATE_CLIENT)
    def enable_all_clients(self) -> list[Client]:
        """Enable all clients belonging to the authenticated admin"""
        enabled_clients = []

        with self.uow:

            my_clients = self.get_my_clients()

            for client in my_clients:
                if not client.enabled:
                    service = AdminClientManagementService(client)
                    updated = service.update_client(enabled=True)
                    self.uow.clients_repository.save_client(updated)
                    enabled_clients.append(updated)

            self.uow.commit()

        return enabled_clients

    @with_permission_check(PermissionAdmin.UPDATE_CLIENT)
    def disable_all_clients(self) -> list[Client]:
        """Disable all clients belonging to the authenticated admin"""
        disabled_clients = []

        with self.uow:

            my_clients = self.get_my_clients()

            for client in my_clients:
                if client.enabled:
                    service = AdminClientManagementService(client)
                    updated = service.update_client(enabled=False)
                    self.uow.clients_repository.save_client(updated)
                    disabled_clients.append(updated)

            self.uow.commit()

        return disabled_clients

    # ========== PRIVATE HELPER METHODS ==========

    def _update_client_attribute(self, client_id: int,
                                 new_value: any, domain_service_method) -> Client:
        """
        Generic helper for updating client attributes
        """
        with self.uow:


            # Get client
            client = self.uow.clients_repository.get_client_by_id(client_id)
            if client.is_empty:
                raise ItemNotFoundError(f"Client ID {client_id} not found")

            # Check if client is deleted
            if client.is_deleted:
                raise DomainOperationError(f"Cannot update deleted client {client.name}")

            # Create domain service
            service = AdminClientManagementService(
                client=client
            )

            # Update using provided method
            updated_client = domain_service_method(service, new_value)

            # Persist changes
            self.uow.clients_repository.save_client(updated_client)
            self.uow.commit()

            return updated_client