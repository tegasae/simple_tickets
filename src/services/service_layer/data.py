from dataclasses import dataclass, field


@dataclass(kw_only=True, frozen=True)
class CreateAdminData:
    name: str
    password:str
    email:str
    enabled: bool=True
    roles: set=field(default_factory=set)
