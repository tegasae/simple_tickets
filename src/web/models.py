#web/models.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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
