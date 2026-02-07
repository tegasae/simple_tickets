#src/domain/account.py
"""Account Domain Model.

This module defines the Account entity and related value objects
for authentication and authorization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Self

from src.domain.value_objects import Login, Password


@dataclass(slots=True)
class Account:
    """User account entity for authentication.

    Attributes:
        account_id: Unique identifier for the account
        login: User's login/username
        password: Hashed password (never stored in plain text)
        enabled: Whether the account is active
        date_created: When the account was created
    """
    account_id: int
    login: Login
    password: Password
    enabled: bool = field(default=True)
    date_created: datetime = field(default_factory=datetime.now)


    @classmethod
    def create(cls, account_id: int, login: str, plain_password: str) -> Self:
        """Create a new account with validated credentials.

        Args:
            account_id: Unique account identifier
            login: User's login/username
            plain_password: Plain text password (will be hashed)

        Returns:
            New Account instance

        Raises:
            ValueError: If login or password validation fails
        """
        return cls(
            account_id=account_id,
            login=Login(login),
            password=Password.from_plain(plain_password),
        )

    @classmethod
    def from_database(cls, account_id: int, login: str, password_hash: str,
                      enabled: bool = True, date_created: datetime | None = None) -> Self:
        """Reconstitute an account from database data.

        Args:
            account_id: Unique account identifier
            login: User's login/username
            password_hash: Pre-hashed password from database
            enabled: Account status from database
            date_created: Account creation date from database

        Returns:
            Reconstructed Account instance
        """
        return cls(
            account_id=account_id,
            login=Login(login),
            password=Password.from_hash(password_hash),
            enabled=enabled,
            date_created=date_created or datetime.now(),
        )

    def verify_password(self, plain_password: str) -> bool:
        """Verify a plain text password against stored hash.

        Args:
            plain_password: Password to verify

        Returns:
            True if password matches
        """
        return self.password.verify(plain_password)

    def disable(self) -> None:
        """Disable the account."""
        self.enabled = False

    def enable(self) -> None:
        """Enable the account."""
        self.enabled = True


    def __eq__(self, other: object) -> bool:
        """Accounts are equal if they have the same account_id."""
        if not isinstance(other, Account):
            return NotImplemented
        return self.account_id == other.account_id

    def __hash__(self) -> int:
        """Hash based on account_id."""
        return hash(self.account_id)

    def __str__(self) -> str:
        """String representation for display."""
        return f"Account(id={self.account_id}, login={self.login})"

    def __repr__(self) -> str:
        """Debug representation."""
        return (f"Account(account_id={self.account_id}, "
                f"login={self.login!r}, enabled={self.enabled}, "
                f"date_created={self.date_created})")


@dataclass(frozen=True)
class NoAccount:
    """Null object representing absence of a system account.

    This explicitly indicates that an employee has no account
    in this system, avoiding None checks throughout the codebase.
    """
    @staticmethod
    def verify_password(plain_password: str) -> bool:
        """No account means no password to verify."""
        plain_password.encode('utf-8')
        return False

    @property
    def enabled(self) -> bool:
        """No account is never enabled."""
        return False

    @property
    def account_id(self) -> int:
        """No account has no ID."""
        return -1

    @property
    def login(self) -> str:
        """No account has no login."""
        return "<no-account>"

    @property
    def date_created(self) -> datetime:
        """No account has no creation date."""
        return datetime.min

    def __bool__(self) -> bool:
        """Always False to indicate no account."""
        return False

    def __str__(self) -> str:
        """String representation."""
        return "<no-account>"

    def __repr__(self) -> str:
        """Debug representation."""
        return "NoAccount()"


AccountType = Account | NoAccount