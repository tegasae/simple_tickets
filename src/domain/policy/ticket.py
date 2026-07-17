# src/domain/policies/ticket.py


from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser


class TicketPolicy:
    """
    Domain policy для проверок связей между агрегатами.

    Здесь нет:
    - RBAC;
    - проверки permissions;
    - загрузки из repository;
    - сохранения в repository;
    - проверки workflow-графа статусов.

    Здесь только cross-aggregate правила:
    - Client enabled;
    - Admin/User enabled;
    - User принадлежит Client;
    - Ticket принадлежит Client;
    - TicketUser принадлежит Client;
    - Ticket связан с TicketUser;
    - Ticket и TicketUser согласованы по client_id/user_id/contact_user_id.
    """

    @staticmethod
    def ensure_client_enabled(client: Client) -> None:
        if not client.enabled:
            raise DomainOperationError(
                f"Cannot create or manage ticket for disabled client "
                f"{client.client_id}"
            )

    @staticmethod
    def ensure_admin_enabled(admin: Admin) -> None:
        if not admin.enabled:
            raise DomainOperationError(
                f"Cannot manage ticket with disabled admin "
                f"{admin.employee_id}"
            )

    @staticmethod
    def ensure_user_enabled(user: User) -> None:
        if not user.enabled:
            raise DomainOperationError(
                f"Cannot manage ticket for disabled user "
                f"{user.employee_id}"
            )

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

    @staticmethod
    def ensure_ticket_has_no_ticket_user(
        *,
        ticket: Ticket,
    ) -> None:
        """
        Проверка для обычной внутренней Ticket.

        Если Ticket создаётся напрямую Admin,
        она не должна быть уже связана с TicketUser.
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
        Проверка для Ticket, созданной из пользовательской TicketUser.
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
        Проверяет саму ссылку:

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
        Проверяет, что Ticket и TicketUser действительно описывают
        одну и ту же пользовательскую заявку.

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

    @staticmethod
    def ensure_ticket_has_no_admin_yet(
        *,
        ticket: Ticket,
    ) -> None:
        """
        Проверка перед принятием Ticket, созданной из TicketUser.

        До ACCEPTED такая Ticket имеет:

            admin_id = 0

        После ACCEPTED aggregate Ticket назначит admin_id
        из actor_employee_id записи ACCEPTED.
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