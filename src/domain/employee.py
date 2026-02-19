#src/domain/employee.py
from abc import ABC
from dataclasses import field, dataclass
from datetime import datetime
from typing import FrozenSet, Self, Any

from src.domain.account import AccountType, NoAccount
from src.domain.rbac.employee_protocol import HasRoleIds
from src.domain.value_objects import Email, Phone, Name, Empty


@dataclass(kw_only=True,eq=False)
class Employee(ABC, HasRoleIds):
    employee_id: int
    first_name: Name|Empty
    last_name: Name|Empty
    email: Email|Empty=Empty
    phone: Phone|Empty=Empty
    account:AccountType=field(default_factory=NoAccount)
    date_created: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    version: int = 0
    _is_empty: bool = field(default=False, init=False, repr=False)
    _role_ids: set[int] = field(default_factory=set, repr=False)



    @classmethod
    def create_empty(cls) -> Self:
        admin = cls(employee_id=0, first_name=None, last_name=None, email=None,phone=None, account=NoAccount())
        admin._is_empty = True
        return admin



    @classmethod
    def _create_base(
            cls,
            *,
            employee_id: int,
            first_name: str | None = None,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None,
            enabled: bool = True,
            date_created: datetime | None = None,
            account: AccountType | NoAccount=NoAccount,
            version: int = 0,
    ) -> dict[str, Any]:
        """
        Common base creation logic.

        - Converts raw strings to value objects.
        - Treats empty/whitespace-only strings as "not provided" (None).
        - Does not set account here (let the caller decide: account_id / Account / None, etc).
        """

        return {
            "employee_id": employee_id,
            "first_name": Name(first_name) if first_name else Empty(),
            "last_name": Name(last_name) if last_name else Empty(),
            "email": Email(email) if email else Empty(),
            "phone": Phone(phone) if phone else Empty(),
            "enabled": enabled,
            "date_created": date_created or datetime.now(),
            "version": version,
            "account": account,

            # "_role_ids": set(),  # not needed; dataclass default_factory will handle it
        }

    def update_base(self, first_name: str|None, last_name: str|None, email: str|None=None, phone: str|None=None)->Self:
        if first_name is not None:
            self.first_name = Name(first_name)
        if last_name is not None:
            self.last_name = Name(last_name)
        if email is not None:
            self.email = Email(email)
        if phone is not None:
            self.phone = Phone(phone)

        self.version+=1
        return self

    def enable(self):
        self.enabled = True
        self.version+=1

    def disable(self):
        self.enabled = False
        self.version+=1

    def is_empty(self) -> bool:
        return self._is_empty

    def role_ids(self) -> FrozenSet[int]:
        return frozenset(self._role_ids)

    def grant_role(self, role_id: int) -> None:
        self._role_ids.add(role_id)


    def revoke_role(self, role_id: int) -> None:
        self._role_ids.discard(role_id)


    def __eq__(self, other) -> bool:
        return isinstance(other, Employee) and self.employee_id == other.employee_id

@dataclass(kw_only=True,eq=False)
class User(Employee):
    client_id: int

    @classmethod
    def create(
            cls,
            *,
            employee_id: int,
            first_name: str | None = None,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None,
            enabled: bool = True,
            date_created: datetime | None = None,
            account: AccountType | NoAccount = NoAccount,
            version: int = 0,
            client_id:int
    ) -> Self:
        """Create a new User with client association."""
        base_data = cls._create_base(employee_id=employee_id, first_name=first_name, last_name=last_name, email=email,
                                     phone=phone, enabled=enabled, date_created=date_created,account=account,version=version)
        return cls(**base_data, client_id=client_id)


@dataclass(kw_only=True,eq=False)
class Admin(Employee):
    job_title: str=""

    @classmethod
    def create(
            cls,
            employee_id: int,
            first_name: str | None = None,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None,
            enabled: bool = True,
            date_created: datetime | None = None,
            account: AccountType | NoAccount = NoAccount,
            version: int = 0,
            job_title:str=""
    ) -> Self:
        """Create a new Admin."""
        base_data = cls._create_base(employee_id=employee_id, first_name=first_name, last_name=last_name, email=email,
                                     phone=phone, enabled=enabled, date_created=date_created, account=account,version=version)
        return cls(**base_data, job_title=job_title)

    def update(self, job_title:str|None, first_name: str|None, last_name: str|None, email: str|None=None, phone: str|None=None)->Self:
        self.update_base(first_name, last_name, email, phone)
        self.job_title = job_title
        return self
