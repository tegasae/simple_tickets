# domain_services.py
from typing import Optional

from src.domain.model import AdminAbstract, AdminsAggregate
from src.domain.clients import Client, ClientsAggregate
from src.domain.exceptions import (
    ItemNotFoundError, DomainOperationError, DomainSecurityError
)
from src.domain.permissions.rbac import RoleRegistry, Permission
from src.domain.tickets import Ticket


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
            raise DomainSecurityError("Admin cannot delete themselves")


        # 4. Check if admin to delete has created any clients
        clients_by_admin = self.clients.get_clients_by_admin(admin_to_delete.admin_id)
        if clients_by_admin:
            client_names = [str(c.name) for c in clients_by_admin]
            raise DomainOperationError(
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
            raise DomainSecurityError("Admin cannot disable themselves")
        self.admins.set_admin_status(admin_to_disable.name, False)

    def create_admin(self,requesting_admin_id:int,
                     name:str,email:str,password:str,enable:bool=True)->AdminAbstract:

        requesting_admin=self.admins.get_admin_by_id(requesting_admin_id)
        if requesting_admin.is_empty() or not requesting_admin.enabled:
            raise DomainSecurityError(f"Admin {requesting_admin.name} cannot create a new admin")
        admin=self.admins.create_admin(admin_id=0, name=name,email=email,password=password,enabled=enable)
        return admin


    class TicketManagementService:
        """Domain Service enforcing cross-aggregate rules"""

        def __init__(
                self,
                admins_aggregate,  # Your existing AdminsAggregate
                clients_aggregate,  # Your existing ClientsAggregate
                tickets_aggregate  # New TicketsAggregate
        ):
            self.admins = admins_aggregate
            self.clients = clients_aggregate
            self.tickets = tickets_aggregate

        def create_ticket(
                self,
                admin_name: str,
                client_name: str,
                text: str,
                executor: str = "",
                comment: str = ""
        ) -> Ticket:
            """
            Business rule 4: Ticket can be created only by enabled Admin for enabled Client
            """
            # Check admin exists and enabled
            admin = self.admins.require_admin_by_name(admin_name)
            if admin.is_empty() or not admin.enabled:
                raise ValueError(f"Admin '{admin_name}' not enabled or doesn't exist")

            # Check client exists and enabled
            client = self.clients.get_client_by_name(client_name)
            if client.is_empty or not client.enabled:
                raise ValueError(f"Client '{client_name}' not enabled or doesn't exist")

            # Create ticket
            return self.tickets.create_ticket(
                admin_id=admin.admin_id,
                client_id=client.client_id,
                text=text,
                executor=executor,
                comment=comment
            )

        def delete_ticket(
                self,
                admin_name: str,
                ticket_id: int
        ) -> None:
            """
            Business rule 5: Ticket can be deleted only by enabled Admin
            """
            # Check admin exists and enabled
            admin = self.admins.require_admin_by_name(admin_name)
            if admin.is_empty() or not admin.enabled:
                raise ValueError(f"Admin '{admin_name}' not enabled or doesn't exist")

            # Delete ticket
            self.tickets.delete_ticket(ticket_id, admin.admin_id)

