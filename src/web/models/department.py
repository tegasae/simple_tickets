# src/web/models/departments.py

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class DepartmentCreateRequest(BaseModel):
    """
    Request body for creating Department.

    actor_admin_id is NOT here.
    It comes from JWT / request context.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    enabled: bool = True


class DepartmentUpdateRequest(BaseModel):
    """
    Request body for updating Department.
    """

    model_config = ConfigDict(extra="forbid")

    name: str


class DepartmentResponse(BaseModel):
    """
    Response model for Department.
    """

    model_config = ConfigDict(from_attributes=True)

    department_id: int
    name: str
    enabled: bool
    date_created: datetime


    @field_validator("name", mode="before")
    @classmethod
    def empty_if_none(cls, value):
        if value is None:
            return ""
        return value