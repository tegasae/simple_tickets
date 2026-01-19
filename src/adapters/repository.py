from abc import ABC, abstractmethod

from src.domain.clients import Client
from src.domain.model import AdminsAggregate


class AdminRepositoryAbstract(ABC):
    """Abstract repository that works with AdminsAggregate"""
    @abstractmethod
    def get_list_of_admins(self) -> AdminsAggregate:
        raise NotImplementedError

    @abstractmethod
    def save_admins(self, aggregate: AdminsAggregate) -> None:
        """Save the entire aggregate to persistence"""
        raise NotImplementedError

class ClientRepositoryAbstract(ABC):
    @abstractmethod
    def get_all_clients(self) -> list[Client]:
        raise NotImplementedError
    @abstractmethod
    def save_client(self, client:Client) -> None:
        raise NotImplementedError
    @abstractmethod
    def delete_client(self,client_id:int) -> None:
        raise NotImplementedError
