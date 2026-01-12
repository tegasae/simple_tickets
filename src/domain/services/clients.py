from typing import Optional

from src.domain.clients import ClientsAggregate, Client
from src.domain.exceptions import ItemNotFoundError, DomainOperationError, DomainSecurityError
from src.domain.model import AdminsAggregate, AdminAbstract
from src.domain.permissions.rbac import RoleRegistry, Permission


class ClientManagementService:
    """Domain Service for orchestrating client operations across aggregates"""

    def __init__(self, admins_aggregate: AdminsAggregate,
                 clients_aggregate: ClientsAggregate,
                 role_registry: RoleRegistry):
        self.admins = admins_aggregate
        self.clients = clients_aggregate
        self.roles = role_registry

    def _require_permission(self, admin_id: int, permission: Permission) -> AdminAbstract:
        """Get admin and verify they have required permission"""
        admin = self.admins.get_admin_by_id(admin_id)

        if admin.is_empty():
            raise ItemNotFoundError(f"Admin '{admin_id}' not found")

        if not admin.enabled:
            raise DomainOperationError(f"Admin '{admin.name}' is disabled")

        if not admin.has_permission(permission, self.roles):
            raise DomainSecurityError(
                f"Admin '{admin.name}' lacks permission: {permission.value}"
            )

        return admin

    # ============ VALIDATION HELPERS ============

    def _require_active_admin(self, admin_id: int) -> AdminAbstract:
        """Get and validate admin exists and is active"""
        admin = self.admins.get_admin_by_id(admin_id)

        if admin.is_empty():
            raise ItemNotFoundError(f"Admin '{admin_id}' not found")

        if not admin.enabled:
            raise DomainOperationError(f"Admin '{admin.name}' is disabled")
        return admin


    def _get_admin_client(self,admin_id:int,client_id)->tuple[AdminAbstract,Client]:
        admin = self._require_active_admin(admin_id=admin_id)
        client=self.clients.get_client_by_id(client_id=client_id)


        return admin,client



    # ============ BUSINESS OPERATIONS ============

    def create_client(
            self,
            admin_id: int,
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
            :param enabled:
            :param emails:
            :param phones:
            :param client_name:
            :param admin_id:
            :param address:
        """

        admin = self._require_permission(admin_id, Permission.CREATE_CLIENT)

        # 1. Validate admin exists and is active
        #admin = self._require_active_admin(admin_id)

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


        return client

    def update_client_address(
            self,
            admin_id: int,
            client_id: int,
            new_address: Optional[str] = "",
            new_emails: Optional[str] = "",
            new_phones: Optional[str] = ""

    ) -> Client:
        """
        Update client address (Rule 2: Any admin can update any client)
        """

        (admin,client)=self._get_admin_client(admin_id=admin_id,client_id=client_id)

        # 3. Update address (any admin can do this per Rule 2)
        self.clients.update_client_address(client_id=client.client_id,
                                           new_address=new_address,new_emails=new_emails,new_phones=new_phones)

        # Return updated client
        return self.clients.get_client_by_id(client_id)


    def enable_client(
            self,
            admin_id: int,
            client_id: int,
            enabled: bool = True
    ) -> Client:
        """Enable or disable a client"""
        (admin, client) = self._get_admin_client(admin_id=admin_id, client_id=client_id)
        client.enabled=enabled

        return client

    def delete_client(
            self,
            admin_id: int,
            client_id: int
    ) -> None:

        (admin, client) = self._get_admin_client(admin_id=admin_id, client_id=client_id)

        if client.admin_id != admin.admin_id:
            raise DomainOperationError(
                f"Admin '{admin.name}' created this client. "
                "Client cannot be deleted by anyone (Rule 4)."
            )


        self.clients.remove_client(client_id)




    def get_clients_created_by_admin(
            self,
            admin_id: int
    ) -> list[Client]:
        """Get all clients created by a specific admin"""
        admin = self._require_active_admin(admin_id)
        return self.clients.get_clients_by_admin(admin.admin_id)
