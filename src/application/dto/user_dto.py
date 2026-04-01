#src/application/services/user_dto.py
from dataclasses import dataclass, field


@dataclass(kw_only=True,frozen=True)
class UserDTO:
    user_id:int=0
    actor_admin_id: int
    client_id: int
    first_name: str|None=None
    last_name: str|None =None
    email: str |None =None
    phone: str |None =None
    login: str|None =None
    password: str |None =None
    enabled:bool =True
    enabled_account: bool =True
    roles:frozenset[int]= field(default_factory=frozenset)

@dataclass
class UserResponseDTO:
    user_id: int
    client_id: int
    first_name: str
    last_name: str
    enable: bool
    email: str
    phone: str
    login: str
    enable_login: bool
    roles: frozenset[int]= field(default_factory=frozenset)

