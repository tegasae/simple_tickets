from abc import ABC, abstractmethod

from src.domain.employee import Admin


class AdminRepository(ABC):
    """
    Optional subtype repo (same note as UserRepository).
    """
    @abstractmethod
    def get(self, admin_id: int) -> Admin:
        raise NotImplementedError
    @abstractmethod
    def get_all(self) -> list[Admin]:
        raise NotImplementedError

    @abstractmethod
    def exists(self, admin_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def save(self, admin: Admin)->Admin:
        raise NotImplementedError


    @abstractmethod
    def delete(self, admin_id: int):
        raise NotImplementedError

    @abstractmethod
    def find_by_login(self, *, login: str) -> Admin:
        raise NotImplementedError

    @abstractmethod
    def exist_login(self, login: str) -> bool:
        raise NotImplementedError

