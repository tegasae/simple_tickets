from pydantic import BaseModel, ConfigDict, field_validator


class ClientCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    email: str = ""
    address: str = ""
    phone: str = ""


class ClientUpdateContactRequest(BaseModel):
    email: str = ""
    address: str = ""
    phone: str = ""



class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    client_id: int
    name: str
    email: str =""
    address: str =""
    phone: str =""
    enabled: bool
    date_created: str
    created_by_admin: int

    @field_validator("email", "address", "phone", mode="before")
    @classmethod
    def none_to_empty_string(cls, value):
        return "" if value is None else value
