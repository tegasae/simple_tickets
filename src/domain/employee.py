#src/domain/employee.py
from dataclasses import field, dataclass
from datetime import datetime
from typing import FrozenSet, Self

from src.domain.account import AccountType, NoAccount
from src.domain.rbac.employee_protocol import HasRoleIds
from src.domain.value_objects import Email, Phone, Name


@dataclass(kw_only=True,eq=False)
class Employee(HasRoleIds):
    employee_id: int
    first_name: Name|None
    last_name: Name|None
    email: Email|None=None
    phone: Phone|None=None
    account:AccountType=field(default_factory=NoAccount)
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

    @classmethod
    def _create_base(
            cls,
            employee_id: int,
            first_name: str | None = None,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None
    ) -> dict:
        """Common base creation logic."""
        # Convert strings to value objects
        first_name_obj = Name(first_name) if first_name else None
        last_name_obj = Name(last_name) if last_name else None
        email_obj = Email(email) if email else None
        phone_obj = Phone(phone) if phone else None

        return {
            "employee_id": employee_id,
            "first_name": first_name_obj,
            "last_name": last_name_obj,
            "email": email_obj,
            "phone": phone_obj,
            "account": NoAccount(),
            "enabled": True,
            "version": 0,
            "is_deleted": False,
        }

    def is_empty(self) -> bool:
        return self._is_empty

    def role_ids(self) -> FrozenSet[int]:
        return frozenset(self._role_ids)

    def grant_role(self, role_id: int) -> None:
        self._role_ids.add(role_id)
        self.version += 1

    def revoke_role(self, role_id: int) -> None:
        self._role_ids.discard(role_id)
        self.version -= 1

    def __eq__(self, other) -> bool:
        return isinstance(other, Employee) and self.employee_id == other.employee_id

@dataclass(kw_only=True,eq=False)
class User(Employee):
    client_id: int

    @classmethod
    def create(
            cls,
            employee_id: int,
            client_id: int,
            first_name: str | None = None,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None
    ) -> Self:
        """Create a new User with client association."""
        base_data = cls._create_base(employee_id, first_name, last_name, email, phone)
        return cls(**base_data, client_id=client_id)


@dataclass(kw_only=True,eq=False)
class Admin(Employee):
    job_title: str=""

    @classmethod
    def create(
            cls,
            employee_id: int,
            job_title: str = "",
            first_name: str | None = None,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None
    ) -> Self:
        """Create a new Admin."""
        base_data = cls._create_base(employee_id, first_name, last_name, email, phone)
        return cls(**base_data, job_title=job_title)