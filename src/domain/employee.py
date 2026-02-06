#src/domain/employee.py
from dataclasses import field, dataclass
from datetime import datetime
from typing import FrozenSet, Self

from src.domain.account import Account, NoAccount
from src.domain.value_objects import Email, Phone, Name


@dataclass(kw_only=True)
class Employee:
    employee_id: int
    first_name: Name|None
    last_name: Name|None
    email: Email|None
    phone: Phone|None
    account:Account|NoAccount
    date_created: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    version: int = 0
    _is_empty: bool = field(default=False, init=False, repr=False)
    is_deleted: bool = False
    _role_ids: set[int] = field(default_factory=set, repr=False)

    @classmethod
    def create_empty(cls) -> Self:
        admin = cls(employee_id=0, first_name=None, last_name=None, email=None,phone=None, account=NoAccount())
        admin._is_empty = True
        return admin



    def role_ids(self) -> FrozenSet[int]:
        return frozenset(self._role_ids)

    def grant_role(self, role_id: int) -> None:
        self._role_ids.add(role_id)

    def revoke_role(self, role_id: int) -> None:
        self._role_ids.discard(role_id)


@dataclass
class Admin(Employee):
    job_title:str=""


class User(Employee):
    client_id: int
