# src/domain/repositories/account_repository.py
from abc import ABC, abstractmethod
from typing import runtime_checkable

from src.domain.client import Client



class ClientRepository(ABC):
    """
    Repository for clients.
    """

    # -------- Reads --------
    @abstractmethod
    def get(self, client_id: int) -> Client:
        raise NotImplementedError
    @abstractmethod
    def get_all(self) -> list[Client]:
        raise NotImplementedError
    @abstractmethod
    def exits(self,client_id:int)->bool:
        raise NotImplementedError

    #Often useful:
    @abstractmethod
    def find_by_name(self, name: str) -> Client:
        raise NotImplementedError

    @abstractmethod
    def exists_by_name(self, name:str)->bool:
        raise NotImplementedError
    # -------- Writes --------
    @abstractmethod
    def save(self, client: Client):
        raise NotImplementedError
    @abstractmethod
    def hard_delete(self, client_id: int):
        raise NotImplementedError
