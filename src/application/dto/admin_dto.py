from dataclasses import dataclass, field


@dataclass(kw_only=True,frozen=True)
class AdminDTO:
    admin_id:int=0
    actor_admin_id: int
    first_name: str|None=None
    job_title: str|None =None
    last_name: str|None =None
    email: str |None =None
    phone: str |None =None
    login: str|None =None
    password: str |None =None
    roles:frozenset[int]= field(default_factory=frozenset)

@dataclass
class AdminResponseDTO:
    admin_id: int
    first_name: str
    job_title: str
    last_name: str
    enable: bool
    email: str
    phone: str
    login: str
    enable_login: bool
    roles: frozenset[int]= field(default_factory=frozenset)

