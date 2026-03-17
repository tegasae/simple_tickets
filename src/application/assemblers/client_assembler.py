# src/application/assemblers/client_assembler.py

from src.domain.client import Client
from src.domain.value_objects import Empty
from src.application.dto.client_dto import ClientResponseDTO


class ClientAssembler:

    @staticmethod
    def to_dto(client: Client) -> ClientResponseDTO:

        def unwrap(value):
            return None if isinstance(value, Empty) else str(value)

        return ClientResponseDTO(
            client_id=client.client_id,
            name=str(client.name),
            email=unwrap(client.email),
            address=unwrap(client.address),
            phone=unwrap(client.phone),
            enabled=client.enabled,
        )