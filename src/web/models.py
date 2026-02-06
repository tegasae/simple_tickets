#web/models.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from src.domain.client import Client
from src.domain.model import Admin



class AdminBase(BaseModel):
    name: str
    email: str


class AdminView(BaseModel):
    admin_id: int
    name: str
    email: str
    enabled: bool
    date_created: datetime

    @classmethod
    def from_admin(cls, admin: Admin):
        """Simple conversion with configurable date format"""

        return cls(
            admin_id=admin.admin_id,
            name=admin.name,
            email=admin.email,
            enabled=admin.enabled,
            date_created=admin.date_created
        )





class AdminCreate(AdminBase):
    password: str
    enabled: bool = True
    roles: set[int] = Field(default_factory=set)  # ✅ CORRECT


class AdminUpdate(BaseModel):
    email: Optional[str] = None
    enabled: Optional[bool] = None
    password: Optional[str] = None


class AdminResponse(AdminBase):
    admin_id: int
    enabled: bool
    date_created: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ClientBase(BaseModel):
    name: str
    email: str
    address: Optional[str] = ""
    phones: Optional[str] = ""


class ClientCreate(ClientBase):
    enabled: bool = True
    admin_id: Optional[int] = None  # 0 or None = use current admin


class ClientUpdate(BaseModel):
    email: Optional[str] = None
    address: Optional[str] = None
    phones: Optional[str] = None
    enabled: Optional[bool] = None
    admin_id: Optional[int] = None


class ClientView(ClientBase):
    client_id: int
    admin_id: int
    enabled: bool
    is_deleted: bool
    date_created: datetime

    @classmethod
    def from_client(cls, client: Client) -> "ClientView":
        return cls(
            client_id=client.client_id,
            name=client.name.value,
            email=client.email.value,
            address=client.address.value,
            phones=client.phone.value,
            admin_id=client.admin_id,
            enabled=client.enabled,
            is_deleted=client.is_deleted,
            date_created=client.date_created
        )