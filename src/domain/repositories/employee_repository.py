# src/domain/repositories/employee_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from src.domain.employee import Admin, User





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
    def save(self, admin: Admin):
        raise NotImplementedError

    @abstractmethod
    def soft_delete(self, admin_id: int):
        raise NotImplementedError

    @abstractmethod
    def hard_delete(self, admin_id: int):
        raise NotImplementedError



class UserRepository(ABC):
    """
    Optional narrower repository if you prefer using subtype-specific repos.
    Useful when User and Admin are stored differently.

    If you keep one table + discriminator, you can skip this interface
    and use only EmployeeRepository.
    """

    @abstractmethod
    def get(self, user_id: int) -> User:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    def exists(self, user_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def save(self, user: User):
        raise NotImplementedError

    @abstractmethod
    def soft_delete(self, user_id: int):
        raise NotImplementedError

    @abstractmethod
    def hard_delete(self, user_id: int):
        raise NotImplementedError

