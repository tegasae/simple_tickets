#value_objects.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar, Generic, ClassVar

T = TypeVar('T')

@dataclass(frozen=True, order=True)  # frozen=immutable, order=can be sorted
class ValueObject(ABC, Generic[T]):
    value:T
    def __post_init__(self):

        object.__setattr__(self, 'value', self._validate())

    @abstractmethod
    def _validate(self)->Any:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        """Value objects are equal if they have the same type and value"""
        if not isinstance(other, type(self)):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """Hash based on type and value"""
        return hash((type(self).__name__, self.value))


@dataclass(frozen=True, order=True)  # frozen=immutable, order=can be sorted
class Emails(ValueObject):
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
class Address(ValueObject):
    value:str=""
    def _validate(self)->str:
        new_value=self.value.strip()

        if self.value!="" and new_value=="":
            raise ValueError("Address cannot be only whitespace")
            # Update the frozen dataclass
        return new_value



@dataclass(frozen=True, order=True)  # frozen=immutable, order=can be sorted
class Phones(ValueObject):
    value:str=""
    def _validate(self)->str:
        new_value=self.value.strip()

        if self.value!="" and new_value=="":
            raise ValueError("Phones cannot be only whitespace")
            # Update the frozen dataclass
        return new_value



@dataclass(frozen=True,order=True)
class Name(ValueObject):
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



