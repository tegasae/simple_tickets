#src/domain/client.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Self

from src.domain.exceptions import ItemValidationError
from src.domain.value_objects import Email, Address, Phone, Name

@dataclass
class Client:
    client_id: int    # ✅ Public field
    name: Name         # ✅ Public field
    email: Email|None
    address: Address|None
    phone: Phone|None
    created_by_admin_id: int=0
    enabled: bool = True
    date_created: datetime = field(default_factory=datetime.now)
    _is_empty: bool = field(default=False, init=False, repr=False)
    is_deleted:bool=False
    version:int=0

    @property
    def is_empty(self) -> bool:
        return self._is_empty

    @classmethod
    def create(cls, *, created_by_admin_id:int,name: str, email: str, address:str,phone:str,enabled:bool=True) -> Self:

        try:
            client=cls(client_id=0, created_by_admin_id=created_by_admin_id, name=Name(name), email=Email(email),
                       address=Address(address), phone=Phone(phone), enabled=enabled)
            return client
        except ValueError as e:
            raise ItemValidationError(message=str(e))

    @classmethod
    def create_empty(cls) -> Self:
        c = cls(client_id=0, name=Name("----"), created_by_admin_id=0,
                phone=Phone(), address=Address(), email=Email(), enabled=False)
        c._is_empty = True
        return c




