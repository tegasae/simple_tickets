from src.domain.client import Client
from src.domain.exceptions import DomainOperationError


class ClientPolicy:
    @staticmethod
    def ensure_can_delete(
        *,
        client: Client,
        has_users: bool,
        has_tickets: bool,
        has_user_tickets: bool,
    ) -> None:
        if has_users:
            raise DomainOperationError(
                f"Client {client.client_id} cannot be deleted because it has users"
            )

        if has_tickets:
            raise DomainOperationError(
                f"Client {client.client_id} cannot be deleted because it has tickets"
            )

        if has_user_tickets:
            raise DomainOperationError(
                f"Client {client.client_id} cannot be deleted because it has user tickets"
            )