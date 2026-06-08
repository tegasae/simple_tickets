#src/application/dto/employee_dto.py
from dataclasses import dataclass, field

@dataclass(kw_only=True)
class EmployeeDTO:
    employee_id:int=0
    actor_admin_id: int=0
    first_name: str=""
    last_name: str =""
    enable:bool=True
    email: str =""
    phone: str =""
    login: str =""
    password: str =""
    enable_account: bool=True
    roles: set[int] = field(default_factory=set)



@dataclass(kw_only=True)
class AdminDTO(EmployeeDTO):
    job_title: str=""





@dataclass(kw_only=True)
class UserDTO(EmployeeDTO):
    client_id: int =0




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
