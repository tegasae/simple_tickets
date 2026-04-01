#src/domain/employee.py
from dataclasses import field, dataclass
from datetime import datetime
from typing import FrozenSet, Self, Any

from src.domain.account import NoAccount, Account
from src.domain.rbac.employee_protocol import HasRoleIds
from src.domain.value_objects import Email, Phone, Name, Empty

@dataclass(kw_only=True,eq=False)
class _Employee(HasRoleIds):
    employee_id: int
    first_name: Name
    last_name: Name|Empty=field(default_factory=Empty)
    email: Email|Empty=field(default_factory=Empty)
    phone: Phone|Empty=field(default_factory=Empty)
    account:Account|NoAccount=field(default_factory=NoAccount)
    date_created: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    version: int = 0
    _is_empty: bool = field(default=False, init=False, repr=False)
    _role_ids: set[int] = field(default_factory=set, repr=False)



    @classmethod
    def create_empty(cls) -> Self:
        admin = cls(employee_id=0, first_name=Name("--"), last_name=Empty(), email=Empty(),phone=Empty(), account=NoAccount())
        admin._is_empty = True
        return admin



    @classmethod
    def create_base(
            cls,
            *,
            employee_id: int,
            first_name: str,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None,
            enabled: bool = True,
            login:str | None = None,
            password: str | None = None,
            enabled_account: bool =True,
            version: int = 0,
            roles:set[int] = ()
    ) -> dict[str, Any]:
        """
        Common base creation logic.

        - Converts raw strings to value objects.
        - Treats empty/whitespace-only strings as "not provided" (None).
        - Does not set account here (let the caller decide: account_id / Account / None, etc).
        """

        if login and password:
            account=Account.create(account_id=0,login=login,plain_password=password,enabled=enabled_account)
        else:
            account=NoAccount()
        #employee=_Employee(employee_id=employee_id,first_name=Name(first_name),
        #             last_name=Name(last_name) if last_name else Empty(),email=Email(email) if email else Empty(),
        #             phone=Phone(phone) if phone else Empty(), enabled=enabled,
        #             date_created=datetime.now(),
        #             account=account,
        #             version=version
        #)
        if roles:
            roles=set(roles)
        else:
            roles=set()
        return {
            "employee_id":employee_id,
            "first_name": Name(first_name),
            "last_name" : Name(last_name) if last_name else Empty(),
             "email" : Email(email) if email else Empty(),
             "phone": Phone(phone) if phone else Empty(),
             "enabled": enabled,
             "date_created": datetime.now(),
            "account": account,
            "version":version,
            "_role_ids": roles
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


        return self

    def enable(self):
        self.enabled = True
        if isinstance(self.account,Account):
            self.account.enable()



    def disable(self):
        self.enabled = False
        if isinstance(self.account,Account):
            self.account.disable()

    def is_empty(self) -> bool:
        return self._is_empty

    def add_account(self, login:str,password:str,enabled_account) -> Self:
        if login and password:
            account=Account.create(account_id=0,login=login,plain_password=password,enabled=enabled_account)
        else:
            account=NoAccount()
        self.account=account
        return self

    def remove_account(self) -> Self:
        if isinstance(self.account,Account):
            self.account=NoAccount()
        return self

    def change_password(self, password:str) -> Self:
        if isinstance(self.account,Account):
            self.account.change_password(plain_password=password)

    def role_ids(self) -> FrozenSet[int]:
        return frozenset(self._role_ids)

    def grant_role(self, role_id: int) -> None:
        self._role_ids.add(role_id)


    def revoke_role(self, role_id: int) -> None:
        self._role_ids.discard(role_id)

    def __eq__(self, other) -> bool:
        return isinstance(other, _Employee) and self.employee_id == other.employee_id

@dataclass(kw_only=True,eq=False)
class User(_Employee):
    client_id: int

    @classmethod
    def create(
            cls,
            *,
            employee_id: int,
            first_name: str,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None,
            enabled: bool = True,
            login: str | None = None,
            password: str | None = None,
            enabled_account: bool = True,
            version: int = 0,
            client_id:int,
            roles: frozenset[int] | None = None
    ) -> Self:
        """Create a new User with client association."""
        base_data = cls.create_base(employee_id=employee_id, first_name=first_name, last_name=last_name, email=email,
                                     phone=phone, enabled=enabled, login=login,password=password,enabled_account=enabled_account,version=version,roles=roles)

        return cls(**base_data, client_id=client_id)


    def update(
            self,
            *,
            first_name: str | None = None,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None,
    ) -> Self:

        self.update_base(first_name, last_name, email, phone)
        return self


@dataclass(kw_only=True,eq=False)
class Admin(_Employee):
    job_title: str=""

    @classmethod
    def create(
            cls,
            employee_id: int,
            first_name: str,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None,
            enabled: bool = True,
            login:str | None = None,
            password: str | None = None,
            enabled_account: bool = True,
            version: int = 0,
            roles: frozenset[int] | None = None,
            job_title:str=""
    ) -> Self:
        """Create a new Admin."""

        base_data = cls.create_base(employee_id=employee_id, first_name=first_name, last_name=last_name, email=email,
                                    phone=phone, enabled=enabled, login=login, password=password,
                                    enabled_account=enabled_account, version=version, roles=roles)

        return cls(**base_data, job_title=job_title)


    def update(self, job_title:str|None, first_name: str|None, last_name: str|None, email: str|None=None, phone: str|None=None)->Self:
        self.update_base(first_name, last_name, email, phone)
        self.job_title = job_title
        return self
