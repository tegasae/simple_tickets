from abc import ABC, abstractmethod

from src.domain.employee import User


class UserRepository(ABC):
    """
    Repository interface for User aggregate.

    Implementations:
        - UserRepositorySQLite
        - (future) UserRepositorySQLAlchemy
        - (future) UserRepositoryPostgres

    The repository manages the whole User aggregate:
        - employees table
        - users table
        - users_roles table
        - accounts table (optional)
    """

    # ---------- reads ----------

    @abstractmethod
    def get(self, user_id: int) -> User:
        """
        Get a user by id.

        Raises:
            ItemNotFoundError if user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[User]:
        """Return all users."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, user_id: int) -> bool:
        """Check whether user exists."""
        raise NotImplementedError

    # ---------- persistence ----------

    @abstractmethod
    def save(self, user: User) -> User:
        """
        Save the User aggregate.

        Must handle:
            - insert (employee_id == 0)
            - update (optimistic locking)
            - roles synchronization
            - account synchronization
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, user_id: int) -> None:
        """
        Delete user aggregate.

        Must remove:
            - account
            - roles
            - users row
            - employees row
        """
        raise NotImplementedError

    # ---------- account queries ----------

    @abstractmethod
    def find_by_login(self, *, login: str) -> User:
        """
        Find user by account login.

        Raises:
            ItemNotFoundError if login not found.
        """
        raise NotImplementedError

    @abstractmethod
    def exist_login(self, login: str) -> bool:
        """Check whether login exists."""
        raise NotImplementedError