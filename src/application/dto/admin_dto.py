from dataclasses import dataclass, field


@dataclass(kw_only=True,frozen=True)
class AdminDTO:
    admin_id:int=0
    actor_admin_id: int
    first_name: str=""
    job_title: str =""
    last_name: str =""
    email: str =""
    phone: str =""
    login: str =""
    password: str =""
    roles:frozenset= field(default_factory=frozenset)

@dataclass
class AdminResponseDTO:
    admin_id: int
    first_name: str
    job_title: str
    last_name: str
    email: str
    phone: str
    login: str
    roles: frozenset = field(default_factory=frozenset)
