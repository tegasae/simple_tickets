# src/application/dto/client_dto.py

from dataclasses import dataclass


@dataclass
class CreateClientDTO:
    name: str
    email: str = ""
    address: str = ""
    phone: str = ""
    created_by_admin_id: int = 0


@dataclass
class UpdateClientDTO:
    client_id: int
    email: str | None = None
    address: str | None = None
    phone: str | None = None


@dataclass
class ClientResponseDTO:
    client_id: int
    name: str
    email: str | None
    address: str | None
    phone: str | None
    enabled: bool