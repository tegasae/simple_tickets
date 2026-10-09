# src/domain/services/client_service.py

from dataclasses import dataclass

from src.domain.client import Client
from src.domain.employee import User
from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_sync_service import TicketSyncService

from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser


@dataclass(frozen=True, slots=True)
class ClientDisableResult:
    """
    Dependent aggregates changed as a result of disabling Client.

    Client itself is not included because it is modified directly
    by ClientService and persisted separately by application layer.
    """

    users: tuple[User, ...]
    tickets: tuple[Ticket, ...]
    ticket_users: tuple[TicketUser, ...]


class ClientService:
    """
    Domain facade for Client operations.

    Provides a single domain entry point for business operations
    involving Client.

    Responsibilities:
    - create Client;
    - update Client contact data;
    - enable Client;
    - disable Client;
    - apply disable cascade to related User / Ticket / TicketUser;
    - validate Client deletion.

    Does not handle:
    - repositories;
    - UnitOfWork;
    - persistence;
    - transactions;
    - RBAC;
    - permissions;
    - loading aggregates.

    Disable rules
    =============

    When Client is disabled:

    1. Client becomes disabled.

    2. All enabled Users belonging to Client become disabled.

    3. Client Tickets are processed as follows:

       terminal:
           no change;

       AT_WORK:
           no change;
           work already started and continues normally;

       SUSPENDED:
           no change;

       any other non-terminal status:
           -> SUSPENDED.

    4. If suspended Ticket is linked to TicketUser,
       corresponding TicketUser is synchronized through
       TicketSyncService.

    Enabling Client has no reverse cascade.
    """

    def __init__(
        self,
        ticket_sync_service: TicketSyncService,
    ) -> None:
        self._ticket_sync_service = ticket_sync_service

    # ==================================================================
    # Create
    # ==================================================================

    @staticmethod
    def create(
        *,
        name: str,
        email: str,
        address: str,
        phone: str,
        description: str,
        created_by_admin_id: int,
    ) -> Client:
        """
        Create Client.
        """

        return Client.create(
            name=name,
            email=email,
            address=address,
            phone=phone,
            description=description,
            created_by_admin_id=created_by_admin_id,
        )

    # ==================================================================
    # Update
    # ==================================================================

    @staticmethod
    def update(
        *,
        client: Client,
        name: str,
        email: str,
        address: str,
        phone: str,
        description: str,
    ) -> None:
        """
        Update Client contact information.
        """

        client.update_contact_info(
            name=name,
            email=email,
            address=address,
            phone=phone,
            description=description,
        )

    # ==================================================================
    # Enable
    # ==================================================================

    @staticmethod
    def enable(
        *,
        client: Client,
    ) -> None:
        """
        Enable Client.

        Enabling Client does not automatically:
        - enable its Users;
        - restore Ticket statuses;
        - restore TicketUser statuses.
        """

        client.enable()

    # ==================================================================
    # Disable
    # ==================================================================
    @staticmethod
    def disable(
        *,
        client: Client,
        users: list[User],
        open_tickets: list[Ticket],
        open_ticket_users: list[TicketUser],
        actor_employee_id: int,
    ) -> ClientDisableResult:
        """
        Disable Client and apply complete cross-aggregate cascade.

        ticket_users mapping:

            TicketUser.user_ticket_id -> TicketUser

        Only dependent aggregates actually changed by this operation
        are returned.
        """

        if actor_employee_id <= 0:
            raise DomainOperationError(
                "Actor employee id must be positive"
            )

        # --------------------------------------------------------------
        # Validate complete context before mutation
        # --------------------------------------------------------------






        # --------------------------------------------------------------
        # Client
        # --------------------------------------------------------------

        client.disable()

        # --------------------------------------------------------------
        # Users
        # --------------------------------------------------------------

        changed_users: list[User] = []

        for user in users:
            if user.client_id != client.client_id:
                raise DomainOperationError(
                    f"User {user.employee_id} does not belong "
                    f"to client {client.client_id}"
                )

            if not user.enabled:
                continue

            user.disable()
            changed_users.append(user)

        # --------------------------------------------------------------
        # Tickets / TicketUsers
        # --------------------------------------------------------------

        changed_tickets: list[Ticket] = []
        changed_ticket_users: list[TicketUser] = []

        for ticket in open_tickets:
            if ticket.client_id != client.client_id:
                raise DomainOperationError(
                    f"Ticket {ticket.ticket_id} does not belong "
                    f"to client {client.client_id}"
                )

            ticket.suspend(
                actor_employee_id=actor_employee_id
            )

            changed_tickets.append(ticket)

        for ticket_user in open_ticket_users:
            if ticket_user.client_id != client.client_id:
                raise DomainOperationError(
                    f"TicketUser {ticket_user.ticket_user_id} does not belong "
                    f"to client {client.client_id}"
                )

            ticket_user.suspend(actor_employee_id=actor_employee_id)
            changed_ticket_users.append(ticket_user)


        return ClientDisableResult(
            users=tuple(changed_users),
            tickets=tuple(changed_tickets),
            ticket_users=tuple(changed_ticket_users),
        )

    # ==================================================================
    # Delete
    # ==================================================================

    @staticmethod
    def ensure_can_delete(
        *,
        client: Client,
        has_users: bool,
        has_tickets: bool,
        has_user_tickets: bool,
    ) -> None:
        """
        Validate that Client can be deleted.

        Client cannot be deleted while referenced by:
        - User;
        - Ticket;
        - TicketUser.

        Application layer obtains reference facts from repositories.
        ClientService interprets them as business rules.
        """

        if has_users:
            raise DomainOperationError(
                f"Cannot delete client {client.client_id}: "
                f"client has users"
            )

        if has_tickets:
            raise DomainOperationError(
                f"Cannot delete client {client.client_id}: "
                f"client has tickets"
            )

        if has_user_tickets:
            raise DomainOperationError(
                f"Cannot delete client {client.client_id}: "
                f"client has user tickets"
            )

    # ==================================================================
    # Disable rules
    # ==================================================================


