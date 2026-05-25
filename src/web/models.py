from datetime import datetime

from pydantic import BaseModel

from src.application.dto.client_dto import ClientResponseDTO



class ClientView(BaseModel):
    admin_id: int
    name: str
    email: str
    enabled: bool
    date_created: datetime

    @classmethod
    def from_client(cls, client: ClientResponseDTO):
        """Simple conversion with configurable date format"""

        return cls(
            client_id=admin.admin_id,
            name=admin.name,
            email=admin.email,
            enabled=admin.enabled,
            date_created=admin.date_created
        )
