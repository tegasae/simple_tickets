from abc import ABC, abstractmethod


from src.domain.client import Client


class ClientRepository(ABC):

    @abstractmethod
    def get(self, client_id: int) -> Client:
        raise NotImplementedError()

    @abstractmethod
    def get_all(self) -> list[Client]:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, client_id: int) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def save(self, client: Client) -> Client:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, client_id: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def create_by_admin(self, *, admin_id) ->bool:
        raise NotImplementedError()