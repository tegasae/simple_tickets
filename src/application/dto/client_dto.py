# src/application/dto/client_dto.py

from dataclasses import dataclass


@dataclass(kw_only=True,frozen=True)
class ClientDTO:
    actor_admin_id:int
    client_id:int=0
    name: str
    email: str = ""
    address: str = ""
    phone: str = ""
    enable: bool = True




@dataclass(kw_only=True,frozen=True)
class ClientResponseDTO:
    client_id: int
    name: str
    email: str | None
    address: str | None
    phone: str | None
    enabled: bool
    date_created: str
    created_by_admin:int