# domain_services.py
from typing import Optional

from src.domain.model import Admin, AdminEmpty, AdminAbstract, AdminsAggregate
from src.domain.clients import Client, ClientsAggregate
from src.domain.exceptions import (
    ItemNotFoundError, ItemAlreadyExistsError,
    ItemValidationError, AdminOperationError, AdminSecurityError
)


class ClientManagementService:
    """Domain Service for orchestrating client operations across aggregates"""

    def __init__(self, admins_aggregate: AdminsAggregate, clients_aggregate: ClientsAggregate):
        self.admins = admins_aggregate
        self.clients = clients_aggregate

    # ============ VALIDATION HELPERS ============

    def _require_active_admin(self, admin_name: str) -> Admin:
        """Get and validate admin exists and is active"""
        admin = self.admins.require_admin_by_name(admin_name)

        if admin.is_empty():
            raise ItemNotFoundError(f"Admin '{admin_name}' not found")

        if not admin.enabled:
            raise AdminOperationError(f"Admin '{admin_name}' is disabled")

        return admin  # type: ignore (we know it's Admin, not AdminEmpty)

    def _require_client_exists(self, client_id: int) -> Client:
        """Get and validate client exists"""
        client = self.clients.get_client_by_id(client_id)

        if client.is_empty:
            raise ItemNotFoundError(f"Client {client_id} not found")

        return client

    # ============ BUSINESS OPERATIONS ============

    def create_client(
            self,
            admin_name: str,
            client_name: str,
            address: str = "",
            phones: str = "",
            emails: str = "",
            enabled: bool = True
    ) -> Client:
        """
        Create a new client (Rule 1: Any admin can create a client)

        Args:
            admin_name: Name of admin creating the client
            client_name: Name for the new client
            ... other client details
        """
        # 1. Validate admin exists and is active
        admin = self._require_active_admin(admin_name)

        # 2. Create client with admin's ID as creator
        # Note: client_id=0 for new (unpersisted) clients
        client = self.clients.create_client(
            client_id=0,  # New client, no ID yet
            name=client_name,
            admin_id=admin.admin_id,  # Creator admin ID
            address=address,
            phones=phones,
            emails=emails,
            enabled=enabled
        )

        if client.is_empty:
            raise ItemAlreadyExistsError(f"Client '{client_name}' already exists")

        return client

    def update_client_address(
            self,
            admin_name: str,
            client_id: int,
            new_address: str
    ) -> Client:
        """
        Update client address (Rule 2: Any admin can update any client)
        """
        # 1. Validate admin exists and is active
        admin = self._require_active_admin(admin_name)

        # 2. Validate client exists
        client = self._require_client_exists(client_id)

        # 3. Update address (any admin can do this per Rule 2)
        self.clients.update_client_address(client_id, new_address)

        # Return updated client
        return self.clients.get_client_by_id(client_id)

    def update_client_contact(
            self,
            admin_name: str,
            client_id: int,
            emails: Optional[str] = None,
            phones: Optional[str] = None
    ) -> Client:
        """Update client contact info"""
        admin = self._require_active_admin(admin_name)
        client = self._require_client_exists(client_id)

        # Update logic would go here
        # For now, just return the client
        return client

    def enable_client(
            self,
            admin_name: str,
            client_id: int,
            enabled: bool = True
    ) -> Client:
        """Enable or disable a client"""
        admin = self._require_active_admin(admin_name)
        client = self._require_client_exists(client_id)

        self.clients.set_client_status(client_id, enabled)
        return self.clients.get_client_by_id(client_id)

    def delete_client(
            self,
            admin_name: str,
            client_id: int
    ) -> None:
        """
        Delete a client with business rules:
        - Rule 3: Any admin can delete any client
        - Rule 4: EXCEPT if admin created the client (then nobody can delete)
        - Rule 5: Admin can't delete itself (handled separately)
        """
        # 1. Validate admin exists and is active
        admin = self._require_active_admin(admin_name)

        # 2. Validate client exists
        client = self._require_client_exists(client_id)

        # 3. Apply Rule 4: Check if this admin created the client
        if client.admin_id == admin.admin_id:
            raise AdminOperationError(
                f"Admin '{admin_name}' created this client. "
                "Client cannot be deleted by anyone (Rule 4)."
            )

        # 4. Apply Rule 3: Any other admin can delete
        self.clients.remove_client(client_id)

    def transfer_client_ownership(
            self,
            admin_name: str,
            client_id: int,
            new_admin_name: str
    ) -> Client:
        """
        Transfer client to another admin.
        Only the current owner (creator) can transfer ownership.
        """
        # 1. Validate requesting admin
        requesting_admin = self._require_active_admin(admin_name)

        # 2. Validate client exists
        client = self._require_client_exists(client_id)

        # 3. Check if requesting admin is the creator
        if client.admin_id != requesting_admin.admin_id:
            raise AdminOperationError(
                f"Only the creator admin (ID: {client.admin_id}) "
                f"can transfer client ownership"
            )

        # 4. Validate new admin
        new_admin = self._require_active_admin(new_admin_name)

        # 5. Update client's admin_id (simplified - in real system,
        #    this might require domain events or more complex logic)
        # Note: Since Client is immutable, we'd need to create a new client
        # For now, this shows the business logic

        raise NotImplementedError("Client transfer requires client immutability handling")

    def get_clients_created_by_admin(
            self,
            admin_name: str
    ) -> list[Client]:
        """Get all clients created by a specific admin"""
        admin = self._require_active_admin(admin_name)
        return self.clients.get_clients_by_admin(admin.admin_id)

    def get_client_with_creator_info(
            self,
            client_id: int
    ) -> dict:
        """Get client info with creator admin details"""
        client = self._require_client_exists(client_id)

        # Find creator admin
        creator_admin = AdminEmpty()
        for admin in self.admins.get_all_admins():
            if admin.admin_id == client.admin_id:
                creator_admin = admin
                break

        return {
            'client': client,
            'creator_admin': creator_admin,
            'created_by_name': creator_admin.name if not creator_admin.is_empty() else "[Unknown]",
            'created_by_email': creator_admin.email if not creator_admin.is_empty() else "[Unknown]"
        }


class AdminManagementService:
    """Domain Service for admin operations with cross-aggregate rules"""

    def __init__(self, admins_aggregate: AdminsAggregate, clients_aggregate: ClientsAggregate):
        self.admins = admins_aggregate
        self.clients = clients_aggregate

    def _get_admins(self,requesting_admin_id:int,admin_to_operation)->tuple[AdminAbstract,AdminAbstract]:
        requesting_admin = self.admins.get_admin_by_id(requesting_admin_id)
        admin_to_operation=self.admins.get_admin_by_id(admin_to_operation)


        return requesting_admin,admin_to_operation

    def delete_admin(
            self,
            requesting_admin_id: int,
            admin_to_delete_id: int
    ) -> None:
        """
        Delete an admin with business rules:
        - Rule 5: Admin can't delete itself
        - Additional: Check if admin has created clients
        """
        # 1. Validate requesting admin exists and is active
        (requesting_admin,admin_to_delete)=(
            self._get_admins(requesting_admin_id=requesting_admin_id,admin_to_operation=admin_to_delete_id))
        if requesting_admin==admin_to_delete:
            raise AdminSecurityError("Admin cannot delete themselves")


        # 4. Check if admin to delete has created any clients
        clients_by_admin = self.clients.get_clients_by_admin(admin_to_delete.admin_id)
        if clients_by_admin:
            client_names = [str(c.name) for c in clients_by_admin]
            raise AdminOperationError(
                f"Cannot delete admin '{admin_to_delete.name}'. "
                f"They have created clients: {', '.join(client_names[:3])}"
                f"{'...' if len(client_names) > 3 else ''}"
            )

        # 5. Delete the admin
        self.admins.remove_admin_by_id(admin_to_delete.admin_id)

    def disable_admin(
            self,
            requesting_admin_id: int,
            admin_to_disable_id: int
    ) -> None:
        """Disable an admin (softer than delete)"""

        (requesting_admin, admin_to_disable) = (
            self._get_admins(requesting_admin_id=requesting_admin_id, admin_to_operation=admin_to_disable_id))

        # Can't disable yourself
        if requesting_admin==admin_to_disable:
            raise AdminSecurityError("Admin cannot disable themselves")
        self.admins.set_admin_status(admin_to_disable.name, False)