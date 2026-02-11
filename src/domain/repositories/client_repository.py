# src/domain/repositories/account_repository.py

from typing import Protocol, runtime_checkable

from src.domain.client import Client


@runtime_checkable
class ClientRepository(Protocol):
    """
    Repository for clients.
    """

    # -------- Reads --------

    def get(self, client_id: int) -> Client: ...
    def get_all(self) -> list[Client]: ...
    def exits(self,client_id:int)->bool: ...

    #Often useful:
    def find_by_name(self, name: str) -> Client: ...

    # -------- Writes --------

    def save(self, client: Client): ...
    def hard_delete(self, client_id: int): ...
