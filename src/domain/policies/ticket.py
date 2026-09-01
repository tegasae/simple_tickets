# src/domain/policies/ticket.py

from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser


class TicketPolicy:
    """
    Cross-aggregate domain policies для Ticket / TicketUser.

    Здесь нет:
    - RBAC;
    - permissions;
    - repository;
    - persistence;
    - workflow-графа;
    - конкретных TicketStatus.

    Здесь проверяются только отношения между aggregates:
    - enabled-state Client/Admin/User;
    - принадлежность User к Client;
    - принадлежность Ticket/TicketUser к Client;
    - связь Ticket <-> TicketUser;
    - согласованность связанных aggregates.
    """

    # ----------------------------
    # Enabled state
    # ----------------------------

    @staticmethod
    def ensure_client_enabled(
        client: Client,
    ) -> None:
        if not client.enabled:
            raise DomainOperationError(
                f"Cannot create or manage ticket for disabled client "
                f"{client.client_id}"
            )

    @staticmethod
    def ensure_admin_enabled(
        admin: Admin,
    ) -> None:
        if not admin.enabled:
            raise DomainOperationError(
                f"Cannot manage ticket with disabled admin "
                f"{admin.employee_id}"
            )

    @staticmethod
    def ensure_user_enabled(
        user: User,
    ) -> None:
        if not user.enabled:
            raise DomainOperationError(
                f"Cannot manage ticket for disabled user "
                f"{user.employee_id}"
            )

    # ----------------------------
    # Client relations
    # ----------------------------

    @staticmethod
    def ensure_user_belongs_to_client(
        *,
        user: User,
        client: Client,
    ) -> None:
        if user.client_id != client.client_id:
            raise DomainOperationError(
                f"User {user.employee_id} does not belong to client "
                f"{client.client_id}"
            )

    @staticmethod
    def ensure_contact_user_belongs_to_client(
        *,
        contact_user: User,
        client: Client,
    ) -> None:
        if contact_user.client_id != client.client_id:
            raise DomainOperationError(
                f"Contact user {contact_user.employee_id} does not belong "
                f"to client {client.client_id}"
            )

    @staticmethod
    def ensure_ticket_belongs_to_client(
        *,
        ticket: Ticket,
        client: Client,
    ) -> None:
        if ticket.client_id != client.client_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} does not belong to client "
                f"{client.client_id}"
            )

    @staticmethod
    def ensure_ticket_user_belongs_to_client(
        *,
        ticket_user: TicketUser,
        client: Client,
    ) -> None:
        if ticket_user.client_id != client.client_id:
            raise DomainOperationError(
                f"TicketUser {ticket_user.ticket_id} does not belong to "
                f"client {client.client_id}"
            )

    # ----------------------------
    # Ticket <-> TicketUser
    # ----------------------------

    @staticmethod
    def ensure_ticket_has_no_ticket_user(
        *,
        ticket: Ticket,
    ) -> None:
        """
        Ticket не должна быть связана с TicketUser.
        """
        if ticket.user_ticket_id != 0:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} already has linked TicketUser "
                f"{ticket.user_ticket_id}"
            )

    @staticmethod
    def ensure_ticket_has_ticket_user(
        *,
        ticket: Ticket,
    ) -> None:
        """
        Ticket должна иметь связанную TicketUser.
        """
        if ticket.user_ticket_id == 0:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} is not linked to TicketUser"
            )

    @staticmethod
    def ensure_ticket_linked_to_ticket_user(
        *,
        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        """
        Проверяет прямую связь:

            Ticket.user_ticket_id == TicketUser.ticket_id
        """
        if ticket.user_ticket_id == 0:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} is not linked to TicketUser"
            )

        if ticket.user_ticket_id != ticket_user.ticket_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} is linked to TicketUser "
                f"{ticket.user_ticket_id}, not {ticket_user.ticket_id}"
            )

    @staticmethod
    def ensure_ticket_matches_ticket_user(
        *,
        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        """
        Проверяет согласованность связанных Ticket и TicketUser.

        Проверяются:
        - user_ticket_id;
        - client_id;
        - user_id;
        - contact_user_id.
        """
        TicketPolicy.ensure_ticket_linked_to_ticket_user(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        if ticket.client_id != ticket_user.client_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} and TicketUser "
                f"{ticket_user.ticket_id} belong to different clients"
            )

        if ticket.user_id != ticket_user.user_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} and TicketUser "
                f"{ticket_user.ticket_id} belong to different users"
            )

        if ticket.contact_user_id != ticket_user.contact_user_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} and TicketUser "
                f"{ticket_user.ticket_id} have different contact users"
            )

    # ----------------------------
    # Admin relation
    # ----------------------------

    @staticmethod
    def ensure_ticket_has_no_admin_yet(
        *,
        ticket: Ticket,
    ) -> None:
        """
        Проверка перед назначением первого Admin
        связанной Ticket.

        Какой workflow допускает эту операцию,
        определяет сам Ticket / TicketStatusRecord.

        Policy проверяет только cross-aggregate факт:
        Admin ещё не должен быть зафиксирован.
        """
        if ticket.admin_id != 0:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} already has admin "
                f"{ticket.admin_id}"
            )

    @staticmethod
    def ensure_ticket_has_admin(
        *,
        ticket: Ticket,
    ) -> None:
        if ticket.admin_id <= 0:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} has no assigned admin"
            )

    # ----------------------------
    # User relations
    # ----------------------------

    @staticmethod
    def ensure_user_matches_ticket_user(
        *,
        user: User,
        ticket_user: TicketUser,
    ) -> None:
        if user.employee_id != ticket_user.user_id:
            raise DomainOperationError(
                f"User {user.employee_id} does not match TicketUser "
                f"{ticket_user.ticket_id}"
            )

    @staticmethod
    def ensure_user_matches_ticket(
        *,
        user: User,
        ticket: Ticket,
    ) -> None:
        if user.employee_id != ticket.user_id:
            raise DomainOperationError(
                f"User {user.employee_id} does not match Ticket "
                f"{ticket.ticket_id}"
            )

    @staticmethod
    def ensure_contact_user_matches_ticket_user(
        *,
        contact_user: User,
        ticket_user: TicketUser,
    ) -> None:
        if contact_user.employee_id != ticket_user.contact_user_id:
            raise DomainOperationError(
                f"Contact user {contact_user.employee_id} does not match "
                f"TicketUser {ticket_user.ticket_id}"
            )

    @staticmethod
    def ensure_contact_user_matches_ticket(
        *,
        contact_user: User,
        ticket: Ticket,
    ) -> None:
        if contact_user.employee_id != ticket.contact_user_id:
            raise DomainOperationError(
                f"Contact user {contact_user.employee_id} does not match "
                f"Ticket {ticket.ticket_id}"
            )


