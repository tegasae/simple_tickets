#users.py
from dataclasses import field, dataclass

from datetime import datetime

from src.domain.value_objects import Name, Emails, Address, Phones



@dataclass
class User:
    user_id: int    # ✅ Public field
    name: Name         # ✅ Public field
    login: Name
    password: str
    emails: Emails
    address: Address
    phones: Phones
    client_id: int
    enabled: bool = True
    date_created: datetime = field(default_factory=datetime.now)
    _is_empty: bool = field(default=False, init=False, repr=False)
    is_deleted:bool=False
    version:int=0
    roles: set[int] = field(default_factory=set)

