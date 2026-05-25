# src/application/dto/client_dto.py

from dataclasses import dataclass

@dataclass(kw_only=True)
class ClientDTO:
    actor_admin_id:int
    admin_id: int = 0
    client_id:int=0
    name: str=""
    email: str = ""
    address: str = ""
    phone: str = ""
    enable: bool = True

    def __post_init__(self):
        self.admin_id = self.admin_id or self.actor_admin_id




@dataclass(kw_only=True,frozen=True)
class ClientResponseDTO:
    client_id: int
    name: str
    email: str =""
    address: str =""
    phone: str=""
    enabled: bool
    date_created: str
    created_by_admin:int