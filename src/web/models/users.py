# src/web/models/users.py

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreateRequest(BaseModel):
    """
    Request body for creating a new user.

    actor_admin_id is NOT here.
    It comes from JWT / request context.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int

    first_name: str
    last_name: str = ""
    email: str = ""
    phone: str = ""

    login: str = ""
    password: str = ""

    enable: bool = True
    enable_account: bool = True

    roles: set[int] = Field(default_factory=set)


class UserUpdateRequest(BaseModel):
    """
    Request body for updating user personal/contact data.
    """

    model_config = ConfigDict(extra="forbid")

    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""


class UserAttachAccountRequest(BaseModel):
    """
    Request body for attaching account to user.
    """

    model_config = ConfigDict(extra="forbid")

    login: str
    password: str
    enable_account: bool = True


class UserChangePasswordRequest(BaseModel):
    """
    Request body for changing user password.
    """

    model_config = ConfigDict(extra="forbid")

    password: str


class UserRolesRequest(BaseModel):
    """
    Request body for grant/revoke user roles.
    """

    model_config = ConfigDict(extra="forbid")

    roles: set[int] = Field(default_factory=set)


class UserResponse(BaseModel):
    """
    Web response model.

    It can be created from UserResponseDTO dataclass using:

        UserResponse.model_validate(dto)

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

    client_id: int

    @field_validator(
        "first_name",
        "last_name",
        "email",
        "phone",
        "login",
        "date_created",
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