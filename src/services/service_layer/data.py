from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class CreateAdminData:
    name: str
    password:str
    email:str
    enabled: bool=True
