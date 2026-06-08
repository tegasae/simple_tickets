from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.employee import Admin


class AdminRepository(ABC):
    """
    Abstract repository for the Admin aggregate.

    Aggregate boundary:
        Admin
            ├ Employee data
            ├ Admin data
            ├ Roles
            └ Optional Account

    Persistence responsibilities implemented by concrete repositories:
        - employees table
        - admins table
        - admins_roles table
        - accounts table
    """

    # -------------------------
    # Reads
    # -------------------------

    @abstractmethod
    def get(self, admin_id: int) -> Admin:
        """
        Retrieve an admin by employee_id.

        Raises:
            NotFoundError if admin does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[Admin]:
        """
        Retrieve all admins.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, admin_id: int) -> bool:
        """
        Check whether admin exists.
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_login(self, *, login: str) -> Admin:
        """
        Find admin by account login.

        Raises:
            NotFoundError if login not found.
        """
        raise NotImplementedError

    # -------------------------
    # Persistence
    # -------------------------

    @abstractmethod
    def save(self, admin: Admin) -> Admin:
        """
        Persist the Admin aggregate.

        Handles:
            - employees
            - admins
            - admins_roles
            - accounts

        Uses optimistic locking based on `Admin.version`.

        Raises:
            OptimisticLockError if version mismatch.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, admin_id: int) -> None:
        """
        Delete admin aggregate.

        Deletes in order:
            accounts -> admins_roles -> admins -> employees
        """
        raise NotImplementedError

    # -------------------------
    # Role operations
    # -------------------------

    @abstractmethod
    def grant_role(self, *, employee_id: int, role_id: int) -> None:
        """
        Assign role to admin.
        """
        raise NotImplementedError

    @abstractmethod
    def revoke_role(self, *, employee_id: int, role_id: int) -> None:
        """
        Remove role from admin.
        """
        raise NotImplementedError

    @abstractmethod
    def get_role_ids(self, *, employee_id: int) -> set[int]:
        """
        Return role IDs assigned to admin.
        """
        raise NotImplementedError

    # -------------------------
    # Account operations
    # -------------------------

    @abstractmethod
    def set_no_account(self, *, employee_id: int) -> None:
        """
        Remove account associated with admin.
        """
        raise NotImplementedError

    @abstractmethod
    def exist_login(self, login: str) -> bool:
        """Check whether login exists."""
        raise NotImplementedError

