from src.domain.client import Client
from src.domain.exceptions import DomainOperationError
from src.domain.repositories.client_repository import ClientRepository


class ClientService:
    """
    Domain service for Client operations.

    Responsibilities:
        - create client
        - update client contact info
        - enable/disable client
        - delete client
        - read clients

    Notes:
        - transaction management should be handled in application layer
        - repository implements optimistic locking
    """

    def __init__(self, client_repository: ClientRepository):
        self._client_repository = client_repository

    # ---------------------------
    # Create client
    # ---------------------------

    def create_client(
        self,
        *,
        name: str,
        created_by_admin_id: int,
        email: str | None = None,
        address: str | None = None,
        phone: str | None = None,
    ) -> Client:

        client = Client.create(
            client_id=0,
            name=name,
            email=email,
            address=address,
            phone=phone,
            created_by_admin_id=created_by_admin_id,
        )

        return self._client_repository.save(client)

    # ---------------------------
    # Update contact info
    # ---------------------------

    def update_contact_info(
        self,
        *,
        client_id: int,
        email: str | None = None,
        address: str | None = None,
        phone: str | None = None,
    ) -> Client:

        client = self._client_repository.get(client_id)

        client.update_contact_info(
            email=email,
            address=address,
            phone=phone,
        )

        return self._client_repository.save(client)

    # ---------------------------
    # Enable / disable client
    # ---------------------------

    def disable_client(self, *, client_id: int) -> Client:

        client = self._client_repository.get(client_id)

        client.disable()

        return self._client_repository.save(client)

    def enable_client(self, *, client_id: int) -> Client:

        client = self._client_repository.get(client_id)

        client.enable()

        return self._client_repository.save(client)

    # ---------------------------
    # Delete client
    # ---------------------------

    def delete_client(
        self,
        *,
        client_id: int,
        number_of_users: int,
        number_of_tickets: int,
    ) -> None:

        """
        Domain rule:
            client cannot be deleted if users or tickets exist
        """

        if number_of_users != 0 or number_of_tickets != 0:
            raise DomainOperationError(
                f"Client {client_id} cannot be deleted because dependent entities exist"
            )

        self._client_repository.delete(client_id)

    # ---------------------------
    # Queries
    # ---------------------------

    def get_by_id(self, *, client_id: int) -> Client:

        return self._client_repository.get(client_id)

    def get_all(self) -> list[Client]:

        return self._client_repository.get_all()