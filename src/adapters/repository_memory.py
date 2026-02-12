# src/domain/services/client_service.py
from src.domain.client import Client
from src.domain.exceptions import DomainOperationError
from src.domain.repositories.client_repository import ClientRepository


# ---------------------------
# Optional: in-memory repository for now
# ---------------------------

class InMemoryClientRepo(ClientRepository):
    def __init__(self) -> None:
        self._data: dict[int, Client] = {}
        self._seq: int = 0



    def get(self, client_id: int) -> Client:
        try:
            return self._data[client_id]
        except KeyError:
            raise DomainOperationError(f"Client {client_id} not found") from None

    def save(self, client: Client) -> None:
        self._data[client.client_id] = client

    def hard_delete(self, client_id: int) -> None:
        self._data.pop(client_id, None)

    def exists_by_name(self, name: str) -> bool:
        key = name.strip().lower()
        return any(str(c.name).strip().lower() == key for c in self._data.values())

    def get_all(self) -> list[Client]:
        return list(self._data.values())

    def exits(self, client_id: int) -> bool:
        return bool(self._data.get(client_id,None))

    def find_by_name(self, name: str) -> Client:
        for key, value in self._data.items():
            if value == name:
                return value

        raise DomainOperationError(f"Client {name} not found") from None
