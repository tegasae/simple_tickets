#clients.py

from __future__ import annotations  # Add at the top of the file
from dataclasses import dataclass, field
from datetime import datetime

from src.domain.exceptions import ItemValidationError
from src.domain.value_objects import Emails, Address, Phones, ClientName

@dataclass
class Client:
    client_id: int    # ✅ Public field
    name: ClientName         # ✅ Public field
    emails: Emails
    address: Address
    phones: Phones
    admin_id: int=0
    enabled: bool = True
    date_created: datetime = field(default_factory=datetime.now)
    _is_empty: bool = field(default=False, init=False, repr=False)
    is_deleted:bool=False
    version:int=0


    @property
    def is_empty(self) -> bool:
        return self._is_empty

    @classmethod
    def empty_client(cls)->Client:
        c=cls(client_id=0, name=ClientName("----"), admin_id=0,
                   phones=Phones(),address=Address(),emails=Emails(),enabled=False)
        c._is_empty=True
        return c

    @classmethod
    def create(cls, *, admin_id:int,name: str, emails: str, address:str,phones:str,enabled:bool=True) -> Client:
    # доменные инварианты/валидации при создании
        try:
            client=cls(client_id=0,admin_id=admin_id, name=ClientName(name),emails=Emails(emails),
                        address=Address(address),phones=Phones(phones),enabled=enabled)
            return client
        except ValueError as e:
            raise ItemValidationError(message=str(e))





