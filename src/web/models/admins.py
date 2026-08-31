# src/web/models/admins.py

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdminCreateRequest(BaseModel):
    """
    Request body for creating a new admin.

    actor_admin_id is NOT here.
    It comes from JWT / request context.
    """

    model_config = ConfigDict(extra="forbid")

    first_name: str
    last_name: str = ""
    email: str = ""
    phone: str = ""
    job_title: str = ""

    login: str = ""
    password: str = ""
    enable_account: bool = True
    department_id: int=0
    roles: set[int] = Field(default_factory=set,examples=[[]])


class AdminUpdateRequest(BaseModel):
    """
    Request body for updating admin personal/contact data.
    """

    model_config = ConfigDict(extra="forbid")

    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    job_title: str = ""
    department_id: int=0

class AdminAttachAccountRequest(BaseModel):
    """
    Request body for attaching account to admin.
    """

    model_config = ConfigDict(extra="forbid")

    login: str
    password: str
    enable_account: bool = True


class AdminChangePasswordRequest(BaseModel):
    """
    Request body for password change.
    """

    model_config = ConfigDict(extra="forbid")

    password: str


class AdminRolesRequest(BaseModel):
    """
    Request body for grant/revoke roles.
    """

    model_config = ConfigDict(extra="forbid")

    roles: set[int] = Field(default_factory=set)


class AdminChangeDepartmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    department_id: int = 0

class AdminResponse(BaseModel):
    """
    Web response model.

    It can be created from AdminResponseDTO dataclass using:

        AdminResponse.model_validate(dto)

    because from_attributes=True.
    """

    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    first_name: str = ""
    last_name: str = ""
    enabled: bool = True

    email: str = ""
    phone: str = ""

    login: str = ""
    enabled_login: bool = False

    date_created: str = ""
    roles: set[int] = Field(default_factory=set)

    job_title: str = ""
    department_id: int=0
    @field_validator(
        "first_name",
        "last_name",
        "email",
        "phone",
        "login",
        "date_created",
        "job_title",
        mode="before",
    )
    @classmethod
    def none_to_empty_string(cls, value):
        return "" if value is None else value

    @field_validator("roles", mode="before")
    @classmethod
    def none_to_empty_roles(cls, value):
        if value is None:
            return set()
        return value


class PermissionsResponse(BaseModel):
    """
    Request body for password change.
    """

    model_config = ConfigDict(from_attributes=True)

    permissions:tuple[str,...]=Field(default_factory=tuple)
