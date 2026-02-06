#value_objects.py
import hashlib
import re

from dataclasses import dataclass, field
from typing import TypeVar, Generic, ClassVar, Self



T = TypeVar('T')

@dataclass(frozen=True, order=True)
class ValueObject(Generic[T]):
    value: T = field()

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", self._validate())

    def _validate(self) -> T:
        raise NotImplementedError

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value!r})"


@dataclass(frozen=True, order=True)  # frozen=immutable, order=can be sorted
class Email(ValueObject[str]):
    """We haven't validated emails yet. We'll do it later. We need to create a value object and use to"""
    """An email or emails can be empty. If they aren't empty they won't contain spaces."""

    value:str=""
    def _validate(self)->str:
        new_value=self.value.strip()

        if self.value!="" and new_value=="":
            raise ValueError("Email cannot be only whitespace")
            # Update the frozen dataclass
        return new_value




@dataclass(frozen=True, order=True)  # frozen=immutable, order=can be sorted
class Address(ValueObject[str]):
    value:str=""
    def _validate(self)->str:
        new_value=self.value.strip()

        if self.value!="" and new_value=="":
            raise ValueError("Address cannot be only whitespace")
            # Update the frozen dataclass
        return new_value



@dataclass(frozen=True, order=True)  # frozen=immutable, order=can be sorted
class Phone(ValueObject[str]):
    value:str=""
    def _validate(self)->str:
        new_value=self.value.strip()

        if self.value!="" and new_value=="":
            raise ValueError("Phones cannot be only whitespace")
            # Update the frozen dataclass
        return new_value



@dataclass(frozen=True,order=True)
class Name(ValueObject[str]):
    """Value Object for validated client name"""
    value: str
    MIN_LENGTH: ClassVar[int] = 2
    MAX_LENGTH: ClassVar[int] = 100
    def _validate(self)->str:
        new_value=self.value.strip()

        if new_value=="":
            raise ValueError("The name cannot be only whitespace")
        if len(new_value) < self.MIN_LENGTH:
            raise ValueError(f"The name must be at least {self.MIN_LENGTH} characters")

        if len(new_value) > self.MAX_LENGTH:
            raise ValueError(f"The name cannot exceed {self.MAX_LENGTH} characters")
        return new_value


@dataclass(frozen=True,order=True)
class Login(ValueObject[str]):
    """Value Object for validated client name"""
    value: str
    MIN_LENGTH: ClassVar[int] = 2
    MAX_LENGTH: ClassVar[int] = 100
    def _validate(self)->str:
        new_value=self.value.strip()

        if new_value=="":
            raise ValueError("The login cannot be only whitespace")
        if len(new_value) < self.MIN_LENGTH:
            raise ValueError(f"The login must be at least {self.MIN_LENGTH} characters")

        if len(new_value) > self.MAX_LENGTH:
            raise ValueError(f"The login cannot exceed {self.MAX_LENGTH} characters")
        return new_value



def hash_password(plain: str) -> str:
    # максимально просто (НЕ для реальных паролей в проде)
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


def verify_password(plain: str, password_hash: str) -> bool:
    return hash_password(plain) == password_hash

@dataclass(frozen=True, slots=True)
class Password:
    # ВАЖНО: тут всегда хранится ХЭШ, не plain
    value: str

    MIN_LENGTH: ClassVar[int] = 8
    MAX_LENGTH: ClassVar[int] = 128

    REQUIRE_UPPER: ClassVar[bool] = True
    REQUIRE_LOWER: ClassVar[bool] = True
    REQUIRE_DIGIT: ClassVar[bool] = True
    REQUIRE_SPECIAL: ClassVar[bool] = True

    @staticmethod
    def _validate_plain(plain: str) -> str:
        if plain is None:
            raise ValueError("Password cannot be None")
        if not isinstance(plain, str):
            raise TypeError("Password must be a string")
        if plain == "":
            raise ValueError("Password cannot be empty")
        if any(ch.isspace() for ch in plain):
            raise ValueError("Password cannot contain whitespace")

        if len(plain) < Password.MIN_LENGTH:
            raise ValueError(f"Password must be at least {Password.MIN_LENGTH} characters")
        if len(plain) > Password.MAX_LENGTH:
            raise ValueError(f"Password cannot exceed {Password.MAX_LENGTH} characters")

        if Password.REQUIRE_UPPER and not re.search(r"[A-Z]", plain):
            raise ValueError("Password must contain at least one uppercase letter")
        if Password.REQUIRE_LOWER and not re.search(r"[a-z]", plain):
            raise ValueError("Password must contain at least one lowercase letter")
        if Password.REQUIRE_DIGIT and not re.search(r"d", plain):
            raise ValueError("Password must contain at least one digit")
        if Password.REQUIRE_SPECIAL and not re.search(r"W", plain):
            raise ValueError("Password must contain at least one special character")
        return plain


    @classmethod
    def from_plain(cls, plain: str) -> Self:
        plain = cls._validate_plain(plain)
        return cls(value=hash_password(plain))

    @classmethod
    def from_hash(cls, password_hash: str) -> Self:
        if password_hash is None or password_hash == "":
            raise ValueError("Password hash cannot be empty")
        # тут НЕ валидируем как plain и НЕ хэшируем
        return cls(value=password_hash)

    def verify(self, plain: str) -> bool:
        return verify_password(plain, self.value)

    def __repr__(self) -> str:
        return "Password(value=**hidden**)"

    def __str__(self) -> str:
        return "**hidden**"

