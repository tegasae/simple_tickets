from abc import ABC, abstractmethod

from src.domain.employee import Admin


class AdminRepository(ABC):
    """
    Repository for the Admin aggregate.

    Aggregate structure:
        Admin
          ├ Employee data
          ├ Admin data
          ├ Roles
          └ Optional Account

    All persistence details (tables, joins, etc.) are hidden here.
    """

    # -------------------------
    # Reads
    # -------------------------

    @abstractmethod
    def get(self, admin_id: int) -> Admin:
        """
        Get admin by employee_id.

        Raises:
            ItemNotFoundError if admin does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[Admin]:
        """Return all admins."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, admin_id: int) -> bool:
        """Check whether admin exists."""
        raise NotImplementedError

    @abstractmethod
    def find_by_login(self, *, login: str) -> Admin:
        """
        Find admin by account login.

        Raises:
            ItemNotFoundError if login not found.
        """
        raise NotImplementedError


    # -------------------------
    # Writes (Aggregate)
    # -------------------------

    @abstractmethod
    def save(self, admin: Admin) -> Admin:
        """
        Persist the entire Admin aggregate.

        Handles:
            - employees table
            - admins table
            - roles
            - account

        Uses optimistic locking based on Admin.version.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, admin_id: int) -> None:
        """
        Delete admin aggregate.

        Removes:
            - account
            - roles
            - admin row
            - employee row
        """
        raise NotImplementedError


    # -------------------------
    # Role operations
    # -------------------------

    @abstractmethod
    def grant_role(self, *, employee_id: int, role_id: int) -> None:
        """Assign role to admin."""
        raise NotImplementedError

    @abstractmethod
    def revoke_role(self, *, employee_id: int, role_id: int) -> None:
        """Remove role from admin."""
        raise NotImplementedError

    @abstractmethod
    def get_role_ids(self, *, employee_id: int) -> set[int]:
        """Return role ids assigned to admin."""
        raise NotImplementedError


    # -------------------------
    # Account operations
    # -------------------------

    @abstractmethod
    def set_no_account(self, *, employee_id: int) -> None:
        """Remove account from admin."""
        raise NotImplementedError

    @abstractmethod
    def set_account_from_plain_password(
        self,
        *,
        employee_id: int,
        login: str,
        plain_password: str
    ) -> None:
        """Create or update admin account."""
        raise NotImplementedError