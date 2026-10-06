# src/application/dto/client_dto.py

from dataclasses import dataclass

from src.application.exceptions import ApplicationValidateError


@dataclass(kw_only=True)
class ClientDTO:
    actor_admin_id:int
    admin_id: int = 0
    client_id:int=0
    name: str=""
    email: str = ""
    address: str = ""
    phone: str = ""
    description:str=""
    enable: bool = True

    def __post_init__(self):
        if self.actor_admin_id < 0:
            raise ApplicationValidateError("The actor admin ID is invalid")
        if self.admin_id < 0:
            raise ApplicationValidateError("The actor admin ID is invalid")
        if self.client_id < 0:
            raise ApplicationValidateError("The client ID is invalid")

        self.name=self.name.strip()
        if not self.name:
            raise ApplicationValidateError("The client name cannot be empty")

        self.admin_id = self.admin_id or self.actor_admin_id




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