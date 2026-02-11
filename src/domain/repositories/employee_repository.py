# src/domain/repositories/employee_repository.py
from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.employee import Admin, User





@runtime_checkable
class AdminRepository(Protocol):
    """
    Optional subtype repo (same note as UserRepository).
    """
    def get(self, admin_id: int) -> Admin: ...
    def get_all(self) -> list[Admin]: ...
    def exists(self, admin_id: int) -> bool: ...
    def save(self, admin: Admin): ...
    def soft_delete(self, admin_id: int): ...
    def hard_delete(self, admin_id: int): ...




@runtime_checkable
class UserRepository(Protocol):
    """
    Optional narrower repository if you prefer using subtype-specific repos.
    Useful when User and Admin are stored differently.

    If you keep one table + discriminator, you can skip this interface
    and use only EmployeeRepository.
    """
    def get(self, user_id: int) -> User: ...
    def get_all(self) -> list[User]: ...
    def exists(self, user_id: int) -> bool: ...
    def save(self, user: User): ...
    def soft_delete(self, user_id: int): ...
    def hard_delete(self, user_id: int): ...

