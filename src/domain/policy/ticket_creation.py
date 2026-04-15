from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError


class TicketCreationPolicy:
    """
    Domain policy for ticket creation rules.
    """

    @staticmethod
    def ensure_client_enabled(client: Client) -> None:
        if not client.enabled:
            raise DomainOperationError(
                f"Cannot create a ticket for disabled client {client.client_id}"
            )

    @staticmethod
    def ensure_admin_enabled(admin: Admin) -> None:
        if not admin.enabled:
            raise DomainOperationError(
                f"Cannot create a ticket with disabled admin {admin.employee_id}"
            )

    @staticmethod
    def ensure_user_belongs_to_client(user: User, client: Client) -> None:
        if user.client_id != client.client_id:
            raise DomainOperationError(
                f"User {user.employee_id} does not belong to client {client.client_id}"
            )

    @staticmethod
    def ensure_user_enabled(user: User) -> None:
        if not user.enabled:
            raise DomainOperationError(
                f"User {user.employee_id} is disabled"
            )