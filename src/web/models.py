from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class AdminBase(BaseModel):
    name: str
    email: EmailStr


class AdminView(BaseModel):
    admin_id:int
    name: str
    email: str
    enabled: bool
    date_created: datetime


class AdminCreate(AdminBase):
    password: str
    enabled: bool = True


class AdminUpdate(BaseModel):
    email: Optional[EmailStr] = None
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

