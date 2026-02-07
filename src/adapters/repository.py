from abc import ABC, abstractmethod

from src.domain.client import Client
from src.old.model import AdminsAggregate, Admin


class AdminRepository(ABC):
    """Abstract repository that works with AdminsAggregate"""
    @abstractmethod
    def get_list_of_admins(self) -> AdminsAggregate:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, admin_id: int)->Admin:
        raise NotImplementedError
    @abstractmethod
    def save_admins(self, aggregate: AdminsAggregate) -> None:
        """Save the entire aggregate to persistence"""
        raise NotImplementedError

class ClientRepository(ABC):
    @abstractmethod
    def get_all_clients(self) -> list[Client]:
        raise NotImplementedError
    @abstractmethod
    def get_client_by_id(self,client_id:int) -> Client:
        raise NotImplementedError

    @abstractmethod
    def get_client_by_admin_id(self, admin_id: int) -> list[Client]:
        raise NotImplementedError

    @abstractmethod
    def save_client(self, client:Client) -> None:
        raise NotImplementedError
    @abstractmethod
    def delete_client(self,client_id:int) -> None:
        raise NotImplementedError
