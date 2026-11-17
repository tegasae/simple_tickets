#src/domain/employee.py
from dataclasses import field, dataclass, InitVar
from datetime import datetime
from typing import Self, Any


from src.domain.account import NoAccount, Account
from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.rbac.employee_protocol import HasRoleIds
from src.domain.value_objects import Email, Phone, Name, Empty


_EMPTY_EMPLOYEE_TOKEN = object()

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
    _is_empty: bool = field(default=False, init=False, repr=False,compare=False)
    _role_ids: set[int] = field(default_factory=set, repr=False)
    _empty_token: InitVar[object | None] = None

    def __post_init__(self, _empty_token: object | None) -> None:

        if _empty_token is _EMPTY_EMPLOYEE_TOKEN:
            if self.employee_id != 0:
                raise ItemValidationError(
                    "Invalid empty employee"
                )

            self._is_empty = True

        elif _empty_token is not None:
            raise ItemValidationError(
                "Invalid empty employee token"
            )

        elif self.employee_id < 0:
            raise ItemValidationError(
                "Invalid employee ID"
            )

        if self.version < 0:
            raise ItemValidationError(
                "Invalid employee version"
            )

    @classmethod
    def create_empty(cls) -> Self:
        employee = cls(employee_id=0, first_name=Name("--"), last_name=Empty(), email=Empty(),phone=Empty(), account=NoAccount())
        employee._is_empty = True
        return employee

    @classmethod
    def create_base(
            cls,
            *,
            employee_id: int,
            first_name: str,
            last_name: str = "",
            email: str = "",
            phone: str = "",
            enabled: bool = True,
            login: str = "",
            password: str = "",
            enabled_account: bool = True,
            version: int = 0,
            date_created: datetime|None = None,
            roles: set[int] | list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Common base creation logic.

        - Converts raw strings to value objects.
        - Creates Account only if both login and password are provided.
        - Uses NoAccount if account data is not provided.
        - Normalizes roles to set[int].
        """


        role_ids = set(roles or [])
        try:
            c= {
                "employee_id": employee_id,
                "first_name": Name(first_name),
                "last_name": Name(last_name) if last_name else Empty(),
                "email": Email(email) if email else Empty(),
                "phone": Phone(phone) if phone else Empty(),
                "enabled": enabled,
                "date_created": date_created if date_created else datetime.now(),
                "account": _Employee._create_account(login=login,password=password,enabled_account=enabled_account),
                "version": version,
                "_role_ids": role_ids,
            }
        except ValueError as e:
            raise ItemValidationError(str(e))
        return c

    def update_base(
            self,
            *,
            first_name: str | None = None,
            last_name: str | None = None,
            email: str | None = None,
            phone: str | None = None
    ) -> Self:



        try:
            new_first_name = (
                Name(first_name)
                if first_name is not None
                else self.first_name
            )

            new_last_name = (
                Name(last_name) if last_name else Empty()
            ) if last_name is not None else self.last_name

            new_email = (
                Email(email) if email else Empty()
            ) if email is not None else self.email

            new_phone = (
                Phone(phone) if phone else Empty()
            ) if phone is not None else self.phone

        except ValueError as e:
            raise ItemValidationError(
                f"Employee update failed: {e}"
            ) from e

        self.first_name = new_first_name
        self.last_name = new_last_name
        self.email = new_email
        self.phone = new_phone

        return self

    def can_do_operation(self):
        if not self.enabled:
            raise DomainOperationError("The inactive employee can't do any operations")

    def enable(self):
        self.enabled = True
        self.account.enable()



    def disable(self):
        self.enabled = False
        self.account.disable()

    def is_empty(self) -> bool:
        return self._is_empty

    @staticmethod
    def _create_account(login:str,password:str,enabled_account)->Account|NoAccount:
        if (login and not password) or (not login and password):
            raise DomainOperationError(
                "Both the login and the password must be filled in"
            )
        if login and password:
            account=Account.create(account_id=0,login=login,plain_password=password,enabled=enabled_account)
        else:
            account = NoAccount()
        return account

    def add_account(self, login:str,password:str,enabled_account):
        if self.enabled:
            self.account=_Employee._create_account(login=login,password=password,enabled_account=enabled_account)
        else:
            raise DomainOperationError(f"The employee {self.employee_id} is disabled")


    def remove_account(self):
        self.account = NoAccount()

    def enable_account(self)->Self:
        if self.enabled:
            self.account.enable()
        else:
            raise DomainOperationError(f"The employee id {self.employee_id} is disabled")
        return self

    def disable_account(self)->Self:
        self.account.disable()
        return self


    def change_password(self, password:str):
        if isinstance(self.account,Account):
            self.account.change_password(plain_password=password)

    def role_ids(self) -> frozenset[int]:
        return frozenset(self._role_ids)

    def grant_role(self, role_id: int) -> None:
        if not self.enabled:
            raise DomainOperationError(f"The disabled {self.employee_id} can't be granted roles")
        self._role_ids.add(role_id)


    def revoke_role(self, role_id: int) -> None:
        self._role_ids.discard(role_id)

    def __eq__(self, other: object) -> bool:

        if not isinstance(other, _Employee):
            return NotImplemented

        if type(self) is not type(other):
            return False

        if self._is_empty or other._is_empty:
            return self._is_empty and other._is_empty

        if self.employee_id == 0 or other.employee_id == 0:
            return self is other

        return self.employee_id == other.employee_id
@dataclass(kw_only=True,eq=False)
class User(_Employee):
    client_id: int

    def __post_init__(
            self,
            _empty_token: object | None
    ) -> None:

        super().__post_init__(_empty_token)

        if self.client_id < 0:
            raise ItemValidationError(
                "Client ID cannot be negative"
            )

        if self._is_empty and self.client_id != 0:
            raise ItemValidationError(
                "Empty user cannot have a client"
            )

    @classmethod
    def create(
            cls,
            *,
            first_name: str,
            last_name: str ="",
            email: str ="",
            phone: str ="",
            enabled: bool = True,
            login: str ="",
            password: str ="",
            enabled_account: bool = True,
            client_id:int,
            roles: set[int] | list[int] | None = None
    ) -> Self:
        """Create a new User with client association."""



        base_data = cls.create_base(employee_id=0, first_name=first_name, last_name=last_name, email=email,
                                     phone=phone, enabled=enabled, login=login,password=password,enabled_account=enabled_account,version=0,roles=roles)

        return cls(**base_data, client_id=client_id)

    @classmethod
    def rehydrate(
            cls,
            *,
            employee_id: int,
            first_name: str,
            last_name: str = "",
            email: str = "",
            phone: str = "",
            enabled: bool = True,
            login: str = "",
            password: str = "",
            enabled_account: bool = True,
            version: int,
            client_id: int,
            roles: set[int] | list[int] | None = None,
            date_created: datetime|None,
    ) -> Self:
        """Create the User with client association."""


        base_data = cls.create_base(employee_id=employee_id, first_name=first_name, last_name=last_name, email=email,
                                    phone=phone, enabled=enabled, login=login, password=password,
                                    enabled_account=enabled_account, version=version, roles=roles,date_created=date_created)

        return cls(**base_data, client_id=client_id)

    @classmethod
    def create_empty(cls) -> Self:
        return cls(
            employee_id=0,
            first_name=Name("--"),
            client_id=0,
            _empty_token=_EMPTY_EMPLOYEE_TOKEN
        )


    def update(
            self,
            *,
            first_name: str="",
            last_name: str ="",
            email: str="",
            phone: str="",
    ) -> Self:

        self.update_base(first_name=first_name, last_name=last_name, email=email, phone=phone)
        return self


@dataclass(kw_only=True,eq=False)
class Admin(_Employee):
    job_title: str=""
    department_id: int =0

    def __post_init__(
            self,
            _empty_token: object | None
    ) -> None:

        super().__post_init__(_empty_token)

        if self.department_id < 0:
            raise ItemValidationError(
                "Department ID cannot be negative"
            )

        if self._is_empty and self.department_id != 0:
            raise ItemValidationError(
                "Empty admin cannot have a department"
            )

    @classmethod
    def create_empty(cls) -> Self:
        return cls(
            employee_id=0,
            first_name=Name("--"),
            department_id=0,
            _empty_token=_EMPTY_EMPLOYEE_TOKEN
        )


    @classmethod
    def create(
            cls,
            first_name: str,
            last_name: str ="",
            email: str ="",
            phone: str ="",
            enabled: bool = True,
            login:str ="",
            password: str ="",
            enable_account: bool = True,
            roles: set[int] | list[int] | None = None,
            job_title:str="",
            department_id:int=0
    ) -> Self:
        """Create a new Admin."""

        base_data = cls.create_base(employee_id=0, first_name=first_name, last_name=last_name, email=email,
                                    phone=phone, enabled=enabled, login=login, password=password,
                                    enabled_account=enable_account, version=0, roles=roles)



        return cls(**base_data, job_title=job_title,department_id=department_id)


    @classmethod
    def rehydrate(
            cls,
            employee_id: int,
            first_name: str,
            version: int,
            date_created: datetime|None,
            last_name: str = "",
            email: str = "",
            phone: str = "",
            enabled: bool = True,
            enabled_account: bool = True,
            login: str = "",
            password: str = "",
            roles: set[int] | list[int] | None = None,
            job_title: str = "",
            department_id: int = 0,

    ) -> Self:
        """Create the Admin."""

        base_data = cls.create_base(employee_id=employee_id, first_name=first_name, last_name=last_name,
                                    email=email,
                                    phone=phone, enabled=enabled, login=login, password=password,
                                    version=version, roles=roles,date_created=date_created,enabled_account=enabled_account)




        admin=cls(**base_data, job_title=job_title, department_id=department_id)

        return admin

    def update(self, job_title:str="", first_name: str="", last_name: str="", email: str="", phone: str="",department_id:int=0)->Self:
        self.update_base(first_name=first_name, last_name=last_name, email=email, phone=phone)
        self.job_title = job_title
        self.department_id=department_id
        return self

    def change_department(self, department_id: int ) -> None:
        """
        Change Admin department.

        Business rule about AT_WORK tickets is checked in application services,
        because Admin does not know all tickets.
        """
        if department_id < 0:
            raise ItemValidationError(
                "Department ID cannot be negative"
            )

        self.department_id = department_id

    def remove_department(self) -> None:
        self.department_id = 0

    def has_department(self) -> bool:
        return bool(self.department_id)