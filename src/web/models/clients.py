from pydantic import BaseModel, ConfigDict, field_validator


class ClientCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    email: str = ""
    address: str = ""
    phone: str = ""
    description:str=""

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Client name must not be empty")

        return value


class ClientUpdateContactRequest(BaseModel):
    name:str=""
    email: str = ""
    address: str = ""
    phone: str = ""
    description:str=""


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    client_id: int
    name: str
    email: str =""
    address: str =""
    phone: str =""
    description:str=""
    enabled: bool
    date_created: str
    created_by_admin: int

    @field_validator("email", "address", "phone", "description",mode="before")
    @classmethod
    def none_to_empty_string(cls, value):
        return "" if value is None else value
