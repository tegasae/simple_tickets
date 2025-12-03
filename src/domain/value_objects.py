from dataclasses import dataclass

from src.domain.exceptions import ItemValidationError


@dataclass(frozen=True, order=True)  # frozen=immutable, order=can be sorted
class Emails:
    """We haven't validated emails yet. We'll do it later. We need to create a value object and use to"""
    """An email or emails can be empty. If they aren't empty they won't contain spaces."""
    emails:str=""
    def __post_init__(self):
        new_emails=self.emails.strip()

        if self.emails!="" and new_emails=="":
            raise ValueError("Email cannot be only whitespace")
            # Update the frozen dataclass
        object.__setattr__(self, 'emails', new_emails)

    def __str__(self) -> str:
        return self.emails


@dataclass(frozen=True, order=True)  # frozen=immutable, order=can be sorted
class Address:
    address:str=""
    def __post_init__(self):
        new_address=self.address.strip()

        if self.address!="" and new_address=="":
            raise ValueError("Address cannot be only whitespace")
            # Update the frozen dataclass
        object.__setattr__(self, 'address', new_address)

    def __str__(self) -> str:
        return self.address


@dataclass(frozen=True, order=True)  # frozen=immutable, order=can be sorted
class Phones:
    phones:str=""
    def __post_init__(self):
        new_phones=self.phones.strip()

        if self.phones!="" and new_phones=="":
            raise ValueError("Address cannot be only whitespace")
            # Update the frozen dataclass
        object.__setattr__(self, 'address', new_phones)

    def __str__(self) -> str:
        return self.phones


@dataclass(frozen=True)
class ClientName:
    """Value Object for validated client name"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Client name cannot be empty")
        # Trim and update
        object.__setattr__(self, 'value', self.value.strip())

    def __str__(self) -> str:
        return self.value
