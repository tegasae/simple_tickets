#src/domain/value_objects.py
"""Value Objects for Domain-Driven Design.

This module provides immutable value objects for common domain concepts
like email, phone, address, name, login, and password.
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import TypeVar, Generic, ClassVar, Self

T = TypeVar('T')


@dataclass(frozen=True, order=True)
class ValueObject(Generic[T]):
    """Base class for immutable value objects.

    Attributes:
        value: The underlying value

    Note:
        Subclasses must implement _validate() method
    """
    value: T = field()

    def __post_init__(self) -> None:
        """Validate and set the value after initialization."""
        object.__setattr__(self, "value", self._validate())

    def _validate(self) -> T:
        """Validate the value. Must be implemented by subclasses.

        Returns:
            The validated value

        Raises:
            ValueError: If validation fails
        """
        raise NotImplementedError

    def __str__(self) -> str:
        """String representation of the value object."""
        return str(self.value)

    def __repr__(self) -> str:
        """Debug representation of the value object."""
        return f"{self.__class__.__name__}(value={self.value!r})"


@dataclass(frozen=True, order=True)
class Email(ValueObject[str]):
    """Email address value object with validation.

    Attributes:
        value: Email address string

    Note:
        Allows empty strings. Non-empty emails are validated for format.
    """
    value: str = ""

    def _validate(self) -> str:
        """Validate email format.

        Returns:
            Normalized email address

        Raises:
            ValueError: If email format is invalid
        """
        new_value = self.value.strip()

        if self.value != "" and new_value == "":
            raise ValueError("Email cannot be only whitespace")

        # Basic email format validation (RFC 5322 simplified)
        if new_value and not self._is_valid_email(new_value):
            raise ValueError("Invalid email format")

        return new_value.lower()  # Normalize to lowercase

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Check if email has valid format.

        Args:
            email: Email to validate

        Returns:
            True if email format is valid
        """
        # Simplified RFC 5322 regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


@dataclass(frozen=True, order=True)
class Address(ValueObject[str]):
    """Physical address value object.

    Attributes:
        value: Address string
    """
    value: str = ""

    def _validate(self) -> str:
        """Validate address is not only whitespace.

        Returns:
            Normalized address

        Raises:
            ValueError: If address is only whitespace
        """
        new_value = self.value.strip()

        if self.value != "" and new_value == "":
            raise ValueError("Address cannot be only whitespace")
        return new_value


@dataclass(frozen=True, order=True)
class Phone(ValueObject[str]):
    """Phone number value object.

    Attributes:
        value: Phone number string
    """
    value: str = ""

    def _validate(self) -> str:
        """Validate phone number is not only whitespace.

        Returns:
            Normalized phone number

        Raises:
            ValueError: If phone number is only whitespace
        """
        new_value = self.value.strip()

        if self.value != "" and new_value == "":
            raise ValueError("Phone number cannot be only whitespace")

        # Optional: Add phone number format validation
        # if new_value and not self._is_valid_phone(new_value):
        #     raise ValueError("Invalid phone number format")

        return new_value


@dataclass(frozen=True, order=True)
class Name(ValueObject[str]):
    """Value object for validated person/entity name.

    Attributes:
        value: Name string
        MIN_LENGTH: Minimum allowed name length
        MAX_LENGTH: Maximum allowed name length
    """
    value: str
    MIN_LENGTH: ClassVar[int] = 2
    MAX_LENGTH: ClassVar[int] = 100

    def _validate(self) -> str:
        """Validate name length and content.

        Returns:
            Normalized name

        Raises:
            ValueError: If name is invalid
        """
        new_value = self.value.strip()

        if new_value == "":
            raise ValueError("Login cannot be empty or only whitespace")

        if len(new_value) < self.MIN_LENGTH:
            raise ValueError(f"Name must be at least {self.MIN_LENGTH} characters")

        if len(new_value) > self.MAX_LENGTH:
            raise ValueError(f"Name cannot exceed {self.MAX_LENGTH} characters")

        return new_value


@dataclass(frozen=True, order=True)
class Login(ValueObject[str]):
    """Value object for user login/username.

    Attributes:
        value: Login string
        MIN_LENGTH: Minimum allowed login length
        MAX_LENGTH: Maximum allowed login length
    """
    value: str
    MIN_LENGTH: ClassVar[int] = 2
    MAX_LENGTH: ClassVar[int] = 100

    def _validate(self) -> str:
        """Validate login length and content.

        Returns:
            Normalized login

        Raises:
            ValueError: If login is invalid
        """
        new_value = self.value.strip()

        if new_value == "":
            raise ValueError("Login cannot be empty or only whitespace")

        if len(new_value) < self.MIN_LENGTH:
            raise ValueError(f"Login must be at least {self.MIN_LENGTH} characters")

        if len(new_value) > self.MAX_LENGTH:
            raise ValueError(f"Login cannot exceed {self.MAX_LENGTH} characters")

        # Optional: Add login format restrictions (no spaces, special chars, etc.)
        if " " in new_value:
            raise ValueError("Login cannot contain spaces")

        return new_value


def hash_password(plain: str) -> str:
    """Hash a plain text password.

    Args:
        plain: Plain text password

    Returns:
        SHA-256 hash of the password

    Warning:
        This is a simple hash. In production, use a proper password
        hashing algorithm like bcrypt, scrypt, or Argon2.
    """
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


def verify_password(plain: str, password_hash: str) -> bool:
    """Verify a plain password against a hash.

    Args:
        plain: Plain text password to verify
        password_hash: Hash to compare against

    Returns:
        True if password matches hash
    """
    return hash_password(plain) == password_hash


@dataclass(frozen=True, slots=True)
class Password:
    """Immutable password value object storing only hashes.

    Attributes:
        value: Password hash (never plain text)
        MIN_LENGTH: Minimum password length
        MAX_LENGTH: Maximum password length
        REQUIRE_UPPER: Whether uppercase letters are required
        REQUIRE_LOWER: Whether lowercase letters are required
        REQUIRE_DIGIT: Whether digits are required
        REQUIRE_SPECIAL: Whether special characters are required
    """
    value: str

    MIN_LENGTH: ClassVar[int] = 8
    MAX_LENGTH: ClassVar[int] = 128

    REQUIRE_UPPER: ClassVar[bool] = True
    REQUIRE_LOWER: ClassVar[bool] = True
    REQUIRE_DIGIT: ClassVar[bool] = True
    REQUIRE_SPECIAL: ClassVar[bool] = True

    @staticmethod
    def _validate_plain(plain: str) -> str:
        """Validate plain text password.

        Args:
            plain: Plain text password to validate

        Returns:
            Validated plain text password

        Raises:
            ValueError: If password validation fails
            TypeError: If password is not a string
        """
        if plain is None:
            raise ValueError("Password cannot be None")

        if not isinstance(plain, str):
            raise TypeError("Password must be a string")

        if plain == "":
            raise ValueError("Password cannot be empty")

        if any(ch.isspace() for ch in plain):
            raise ValueError("Password cannot contain whitespace")

        if len(plain) < Password.MIN_LENGTH:
            raise ValueError(
                f"Password must be at least {Password.MIN_LENGTH} characters"
            )

        if len(plain) > Password.MAX_LENGTH:
            raise ValueError(
                f"Password cannot exceed {Password.MAX_LENGTH} characters"
            )

        if Password.REQUIRE_UPPER and not re.search(r"[A-Z]", plain):
            raise ValueError("Password must contain at least one uppercase letter")

        if Password.REQUIRE_LOWER and not re.search(r"[a-z]", plain):
            raise ValueError("Password must contain at least one lowercase letter")

        if Password.REQUIRE_DIGIT and not re.search(r"\d", plain):  # Fixed: r"\d"
            raise ValueError("Password must contain at least one digit")

        if Password.REQUIRE_SPECIAL and not re.search(r"\W", plain):  # Fixed: r"\W"
            raise ValueError("Password must contain at least one special character")

        return plain

    @classmethod
    def from_plain(cls, plain: str) -> Self:
        """Create Password from plain text.

        Args:
            plain: Plain text password

        Returns:
            Password instance with hash

        Raises:
            ValueError: If password validation fails
        """
        plain = cls._validate_plain(plain)
        return cls(value=hash_password(plain))

    @classmethod
    def from_hash(cls, password_hash: str) -> Self:
        """Create Password from existing hash.

        Args:
            password_hash: Existing password hash

        Returns:
            Password instance

        Raises:
            ValueError: If hash is empty
        """
        if not password_hash:
            raise ValueError("Password hash cannot be empty")

        return cls(value=password_hash)

    def verify(self, plain: str) -> bool:
        """Verify plain password against stored hash.

        Args:
            plain: Plain text password to verify

        Returns:
            True if password matches
        """
        return verify_password(plain, self.value)

    def __repr__(self) -> str:
        """Safe representation that doesn't reveal hash."""
        return "Password(value=**hidden**)"

    def __str__(self) -> str:
        """Safe string representation."""
        return "**hidden**"