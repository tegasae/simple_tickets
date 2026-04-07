#src/application/dto/employee_dto.py
from dataclasses import dataclass, field

@dataclass(kw_only=True,frozen=True)
class EmployeeDTO:
    employee_id:int
    actor_admin_id: int
    first_name: str | None = None
    last_name: str | None = None
    enable:bool=True
    email: str | None = None
    phone: str | None = None
    login: str | None = None
    password: str | None = None
    enable_account: bool=True
    roles: frozenset[int] = field(default_factory=frozenset)

@dataclass(kw_only=True,frozen=True)
class AdminDTO(EmployeeDTO):
    job_title: str|None =None

@dataclass
class AdminResponseDTO:
    employee_id: int
    first_name: str
    job_title: str
    last_name: str
    enabled: bool
    email: str
    phone: str
    login: str
    enabled_login: bool
    roles: frozenset[int]= field(default_factory=frozenset)


@dataclass(kw_only=True,frozen=True)
class UserDTO(EmployeeDTO):
    client_id: int


@dataclass
class UserResponseDTO:
    employee_id: int
    client_id: int
    first_name: str
    last_name: str
    enable: bool
    email: str
    phone: str
    login: str
    enable_login: bool
    roles: frozenset[int]= field(default_factory=frozenset)
