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





@dataclass(kw_only=True,frozen=True)
class UserDTO(EmployeeDTO):
    client_id: int




@dataclass(kw_only=True,frozen=True)
class EmployeeResponseDTO:
    employee_id: int
    first_name: str
    last_name: str
    enabled: bool
    email: str
    phone: str
    login: str
    enabled_login: bool
    date_created: str
    roles: frozenset[int] = field(default_factory=frozenset)


@dataclass(kw_only=True,frozen=True)
class AdminResponseDTO(EmployeeResponseDTO):
    job_title: str


@dataclass(kw_only=True,frozen=True)
class UserResponseDTO(EmployeeResponseDTO):
    client_id: int
