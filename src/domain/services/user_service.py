# src/domain/services/user_service.py

from dataclasses import dataclass

from src.domain.client import Client
from src.domain.employee import User
from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_sync_service import TicketSyncService
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser


@dataclass(frozen=True, slots=True)
class UserDisableResult:
    """
    Dependent aggregates changed as a result of disabling User.

    User itself is not included because it is modified directly
    by UserService and persisted separately by application layer.
    """

    tickets: tuple[Ticket, ...]
    ticket_users: tuple[TicketUser, ...]


class UserService:
    """
    Domain facade for User operations.

    Provides a single domain entry point for business operations
    involving User.

    Responsibilities:
    - create User;
    - update User;
    - manage User account;
    - enable / disable User;
    - apply disable cascade to related Ticket / TicketUser;
    - enforce Client/User state rules;
    - validate User deletion.

    Does not handle:
    - repositories;
    - UnitOfWork;
    - persistence;
    - transactions;
    - RBAC;
    - permissions;
    - RoleManager;
    - loading aggregates.

    Disable rules
    =============

    When User is disabled, related Tickets are those where:

        Ticket.user_id == User.employee_id

    or:

        Ticket.contact_user_id == User.employee_id

    Related Tickets:

    terminal:
        no change;

    AT_WORK:
        no change;

    SUSPENDED:
        no change;

    any other non-terminal status:
        -> SUSPENDED.

    Linked TicketUser is synchronized through TicketSyncService.
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
        client: Client,
        employee_id: int,
        first_name: str,
        last_name: str = "",
        email: str = "",
        phone: str = "",
        enabled: bool = True,
        login: str = "",
        password: str = "",
        enabled_account: bool = True,
        version: int = 0,
        roles: set[int] | None = None,
    ) -> User:
        """
        Create User.

        User cannot be created for disabled Client.
        """

        UserService._ensure_client_enabled(
            client=client,
        )

        return User.create(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            enabled=enabled,
            login=login,
            password=password,
            enabled_account=enabled_account,
            version=version,
            client_id=client.client_id,
            roles=roles or set(),
        )

    # ==================================================================
    # Update
    # ==================================================================

    @staticmethod
    def update(
        *,
        user: User,
        client: Client,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        phone: str = "",
    ) -> None:
        """
        Update User.

        Client and User must both be enabled.
        """

        UserService._ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        UserService._ensure_client_enabled(
            client=client,
        )

        UserService._ensure_user_enabled(
            user=user,
        )

        user.update(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
        )

    # ==================================================================
    # Account
    # ==================================================================

    @staticmethod
    def attach_account(
        *,
        user: User,
        client: Client,
        login: str,
        password: str,
        enabled_account: bool,
    ) -> None:
        """
        Attach Account to User.

        Client and User must be enabled.
        """

        UserService._ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        UserService._ensure_client_enabled(
            client=client,
        )

        UserService._ensure_user_enabled(
            user=user,
        )

        user.add_account(
            login=login,
            password=password,
            enabled_account=enabled_account,
        )

    @staticmethod
    def detach_account(
        *,
        user: User,
        client: Client,
    ) -> None:
        """
        Remove Account from User.

        Client must be enabled.

        User itself may already be disabled.
        """

        UserService._ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        UserService._ensure_client_enabled(
            client=client,
        )

        user.remove_account()

    @staticmethod
    def change_password(
        *,
        user: User,
        client: Client,
        password: str,
    ) -> None:
        """
        Change User password.

        Client must be enabled.

        Preserves current aggregate behavior: User itself is not
        required to be enabled for password change.
        """

        UserService._ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        UserService._ensure_client_enabled(
            client=client,
        )

        user.change_password(
            password=password,
        )

    # ==================================================================
    # Enable
    # ==================================================================

    @staticmethod
    def enable(
        *,
        user: User,
        client: Client,
    ) -> None:
        """
        Enable User.

        User cannot be enabled while its Client is disabled.

        Enabling User does not restore Ticket / TicketUser statuses.
        """

        UserService._ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        UserService._ensure_client_enabled(
            client=client,
        )

        user.enable()

    # ==================================================================
    # Disable
    # ==================================================================

    def disable(
        self,
        *,
        user: User,
        tickets: list[Ticket],
        ticket_users: dict[int, TicketUser],
        actor_employee_id: int,
    ) -> UserDisableResult:
        """
        Disable User and suspend related Tickets when required.

        ticket_users mapping:

            TicketUser.user_ticket_id -> TicketUser

        Duplicate Tickets are allowed in input because application layer
        may combine:

            get_by_user_id()
            get_by_contact_user_id()

        They are deduplicated here.
        """

        if actor_employee_id <= 0:
            raise DomainOperationError(
                "Actor employee id must be positive"
            )

        unique_tickets = self._unique_tickets(
            tickets=tickets,
        )

        # --------------------------------------------------------------
        # Validate context before mutation
        # --------------------------------------------------------------

        self._validate_tickets(
            user=user,
            tickets=unique_tickets,
        )

        tickets_to_suspend = [
            ticket
            for ticket in unique_tickets
            if self._should_suspend(ticket)
        ]

        self._validate_ticket_users(
            tickets=tickets_to_suspend,
            ticket_users=ticket_users,
        )

        # --------------------------------------------------------------
        # User
        # --------------------------------------------------------------

        user.disable()

        # --------------------------------------------------------------
        # Ticket / TicketUser
        # --------------------------------------------------------------

        changed_tickets: list[Ticket] = []
        changed_ticket_users: list[TicketUser] = []

        for ticket in tickets_to_suspend:
            ticket.suspend(
                actor_employee_id=actor_employee_id,
            )

            changed_tickets.append(ticket)

            if ticket.user_ticket_id == 0:
                continue

            ticket_user = ticket_users[
                ticket.user_ticket_id
            ]

            status_before = ticket_user.current_status()

            self._ticket_sync_service.sync_from_ticket(
                ticket,
                ticket_user,
            )

            if ticket_user.current_status() != status_before:
                changed_ticket_users.append(
                    ticket_user
                )

        return UserDisableResult(
            tickets=tuple(changed_tickets),
            ticket_users=tuple(changed_ticket_users),
        )

    # ==================================================================
    # Delete
    # ==================================================================

    @staticmethod
    def ensure_can_delete(
        *,
        user: User,
        has_ticket_user_references: bool,
        has_ticket_references: bool,
    ) -> None:
        """
        Validate that User can be deleted.

        Ticket references include User appearing as:
        - Ticket.user_id;
        - Ticket.contact_user_id.
        """

        if has_ticket_user_references:
            raise DomainOperationError(
                f"Cannot delete user {user.employee_id}: "
                f"user is referenced by user tickets"
            )

        if has_ticket_references:
            raise DomainOperationError(
                f"Cannot delete user {user.employee_id}: "
                f"user is referenced by tickets"
            )

    # ==================================================================
    # Disable rules
    # ==================================================================

    @staticmethod
    def _should_suspend(
        ticket: Ticket,
    ) -> bool:
        if ticket.is_terminal():
            return False

        current_status = ticket.current_status()

        if current_status == TicketStatus.AT_WORK:
            return False

        if current_status == TicketStatus.SUSPENDED:
            return False

        return True

    # ==================================================================
    # Context validation
    # ==================================================================

    @staticmethod
    def _validate_tickets(
        *,
        user: User,
        tickets: list[Ticket],
    ) -> None:
        """
        Every supplied Ticket must reference User either as
        main User or contact User.
        """

        for ticket in tickets:
            if (
                ticket.user_id != user.employee_id
                and ticket.contact_user_id != user.employee_id
            ):
                raise DomainOperationError(
                    f"Ticket {ticket.ticket_id} is not related "
                    f"to user {user.employee_id}"
                )

    def _validate_ticket_users(
        self,
        *,
        tickets: list[Ticket],
        ticket_users: dict[int, TicketUser],
    ) -> None:
        for ticket in tickets:
            if ticket.user_ticket_id == 0:
                continue

            ticket_user = ticket_users.get(
                ticket.user_ticket_id
            )

            if ticket_user is None:
                raise DomainOperationError(
                    f"TicketUser {ticket.user_ticket_id} "
                    f"required for ticket {ticket.ticket_id} "
                    f"was not provided"
                )

            self._ticket_sync_service.ensure_consistent(
                ticket,
                ticket_user,
            )

    # ==================================================================
    # Internal rules
    # ==================================================================

    @staticmethod
    def _ensure_client_enabled(
        *,
        client: Client,
    ) -> None:
        if not client.enabled:
            raise DomainOperationError(
                f"Operation with user is not allowed because "
                f"client {client.client_id} is disabled"
            )

    @staticmethod
    def _ensure_user_enabled(
        *,
        user: User,
    ) -> None:
        if not user.enabled:
            raise DomainOperationError(
                f"Operation is not allowed because "
                f"user {user.employee_id} is disabled"
            )

    @staticmethod
    def _ensure_user_belongs_to_client(
        *,
        user: User,
        client: Client,
    ) -> None:
        if user.client_id != client.client_id:
            raise DomainOperationError(
                f"User {user.employee_id} does not belong "
                f"to client {client.client_id}"
            )

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _unique_tickets(
        *,
        tickets: list[Ticket],
    ) -> list[Ticket]:
        """
        Remove duplicate Tickets by ticket_id while preserving order.
        """

        result: list[Ticket] = []
        seen: set[int] = set()

        for ticket in tickets:
            if ticket.ticket_id in seen:
                continue

            seen.add(ticket.ticket_id)
            result.append(ticket)

        return result

    @staticmethod
    def ensure_can_grant_roles(
            *,
            user: User,
            client: Client,
    ) -> None:
        """
        Validate domain state required for granting User roles.

        User must belong to Client and Client must be enabled.

        User.enabled is additionally enforced by User.grant_role()
        through RoleManager.
        """

        UserService._ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        UserService._ensure_client_enabled(
            client=client,
        )