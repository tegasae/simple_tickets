# src/web/models/roles.py

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from src.domain.rbac.permissions import AdminPermission, UserPermission


# ---------------------------------------------------------------------
# Admin role models
# ---------------------------------------------------------------------

class AdminRoleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    permissions: list[AdminPermission]
    description: str = ""
    is_system_role: bool = False

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Role name must not be empty")

        return value

    @field_validator("permissions")
    @classmethod
    def permissions_not_empty(
        cls,
        value: list[AdminPermission],
    ) -> list[AdminPermission]:
        if not value:
            raise ValueError("Role must have at least one permission")

        return list(dict.fromkeys(value))

    @field_validator("description", mode="before")
    @classmethod
    def none_to_empty_string(cls, value):
        return "" if value is None else value


class AdminRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    role_id: int
    name: str
    permissions: list[AdminPermission]
    description: str = ""
    is_system_role: bool

    @field_validator("description", mode="before")
    @classmethod
    def none_to_empty_string(cls, value):
        return "" if value is None else value


# ---------------------------------------------------------------------
# User role models
# ---------------------------------------------------------------------

class UserRoleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    permissions: list[UserPermission]
    description: str = ""
    is_system_role: bool = False

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Role name must not be empty")

        return value

    @field_validator("permissions")
    @classmethod
    def permissions_not_empty(
        cls,
        value: list[UserPermission],
    ) -> list[UserPermission]:
        if not value:
            raise ValueError("Role must have at least one permission")

        return list(dict.fromkeys(value))

    @field_validator("description", mode="before")
    @classmethod
    def none_to_empty_string(cls, value):
        return "" if value is None else value


class UserRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    role_id: int
    name: str
    permissions: list[UserPermission]
    description: str = ""
    is_system_role: bool

    @field_validator("description", mode="before")
    @classmethod
    def none_to_empty_string(cls, value):
        return "" if value is None else value