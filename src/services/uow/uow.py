from abc import ABC, abstractmethod

from src.domain.repositories.admin_repository import AdminRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.repositories.client_repository import ClientRepository


class UnitOfWork(ABC):

    admins: AdminRepository
    users: UserRepository
    clients: ClientRepository

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError