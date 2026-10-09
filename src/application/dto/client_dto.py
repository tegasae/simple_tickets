# src/application/dto/client_dto.py

from dataclasses import dataclass

from src.application.exceptions import ApplicationValidateError


@dataclass(frozen=True, kw_only=True)
class ClientDTO:
    actor_admin_id:int
    client_id:int=0
    name: str=""
    email: str = ""
    address: str = ""
    phone: str = ""
    description:str=""
    enable: bool = True

    def __post_init__(self):
        if self.actor_admin_id <= 0:
            raise ApplicationValidateError("The actor admin ID is invalid")
        if self.client_id < 0:
            raise ApplicationValidateError("The client ID is invalid")







@dataclass(kw_only=True,frozen=True)
class ClientResponseDTO:
    client_id: int
    name: str
    email: str =""
    address: str =""
    phone: str=""
    description:str=""
    enabled: bool
    date_created: str
    created_by_admin:int