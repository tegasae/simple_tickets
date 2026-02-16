# src/domain/services/client.py
from __future__ import annotations

from src.domain.client import Client
from src.domain.exceptions import DomainOperationError
from src.domain.repositories.client_repository import ClientRepository
from src.domain.repositories.employee_repository import UserRepository


# ---------------------------
# Service (use-case orchestration)
# ---------------------------

class ClientService:
    """
    Orchestrates client operations.

    This service:
      - validates cross-entity rules (like "unique name")
      - calls entity methods for state changes
      - persists through ClientRepository
      - does NOT manage transactions (UoW can wrap it later)
    """

    def __init__(self, client_repository: ClientRepository, user_repository: UserRepository) -> None:
        self._client_repository = client_repository
        self._user_repository= user_repository

    def create(
        self,
        *,
        client_id:int,
        name: str,
        created_by_admin_id: int,
        email: str | None = None,
        address: str | None = None,
        phone: str | None = None,
        enabled: bool = True,
    ) -> Client:
        # Example business rule: unique client name (optional; remove if not needed)

        #if self._client_repository.exists_by_name(name):
        #    raise ItemValidationError(f"Client with name '{name}' already exists")
        client = Client.create(
                client_id=client_id,
                name=name,
                email=email,
                address=address,
                phone=phone,
                created_by_admin_id=created_by_admin_id,
                enabled=enabled,
            )
        self._client_repository.save(client)
        return client

    def update_contact_info(
        self,
        *,
        client_id: int,
        email: str | None = None,
        address: str | None = None,
        phone: str | None = None,
    ) -> Client:
        client = self._client_repository.get(client_id)
        client.update_contact_info(email=email, address=address, phone=phone)
        self._client_repository.save(client)
        return client

    def disable(self, *, client_id: int) -> Client:
        client = self._client_repository.get(client_id)

        client.disable()
        self._client_repository.save(client)
        return client

    def enable(self, *, client_id: int) -> Client:
        client = self._client_repository.get(client_id)

        client.enable()
        self._client_repository.save(client)
        return client

    def _check_users(self, *, client_id:int)->bool:
        """
        :param client_id:
        :return: true if number of client users non zere
        """
        list_of_users=self._user_repository.get_all_by_client(client_id=client_id)
        return bool(len(list_of_users))



    def delete(self, *, client_id: int) -> None:
        """
        Hard delete should be rare. You can add checks here later,
        e.g. "cannot hard-delete client if they have tickets".
        """
        client=self._client_repository.get(client_id)
        if client.enabled:
            raise DomainOperationError(message=f"Client {client.name} is active")
        if self._check_users(client_id=client.client_id):
            raise DomainOperationError(message=f"Client {client.name} has users")
        # Optional: allow hard delete only if already soft-deleted
        # if not client.is_deleted:
        #     raise DomainOperationError("Hard delete requires soft delete first")

        self._client_repository.hard_delete(client_id)


