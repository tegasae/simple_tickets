# src/application/services/client_service.py
from src.application.assemblers.assembler import ClientAssembler
from src.application.dto.client_dto import CreateClientDTO, ClientResponseDTO, UpdateClientDTO
from src.domain.client import Client
from src.domain.exceptions import DomainOperationError
from src.services.uow.uow import UnitOfWork


class ClientApplicationService:
    """
    Application service using UoW + DTO.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # --------------------------------
    # Create
    # --------------------------------

    def create_client(self, dto: CreateClientDTO) -> ClientResponseDTO:

        with self.uow:

            client = Client.create(
                client_id=0,
                name=dto.name,
                email=dto.email,
                address=dto.address,
                phone=dto.phone,
                created_by_admin_id=dto.created_by_admin_id,
            )

            client = self.uow.clients.save(client)

            return ClientAssembler.to_dto(client)

    # --------------------------------
    # Update
    # --------------------------------

    def update_contact(self, dto: UpdateClientDTO) -> ClientResponseDTO:

        with self.uow:

            client = self.uow.clients.get(dto.client_id)

            client.update_contact_info(
                email=dto.email,
                address=dto.address,
                phone=dto.phone,
            )

            client = self.uow.clients.save(client)

            return ClientAssembler.to_dto(client)

    # --------------------------------
    # Enable / disable
    # --------------------------------

    def disable(self, client_id: int) -> ClientResponseDTO:

        with self.uow:

            client = self.uow.clients.get(client_id)

            client.disable()

            client = self.uow.clients.save(client)

            return ClientAssembler.to_dto(client)

    def enable(self, client_id: int) -> ClientResponseDTO:

        with self.uow:

            client = self.uow.clients.get(client_id)

            client.enable()

            client = self.uow.clients.save(client)

            return ClientAssembler.to_dto(client)

    # --------------------------------
    # Delete
    # --------------------------------

    def delete(
        self,
        *,
        client_id: int,
        number_of_users: int,
        number_of_tickets: int,
    ) -> None:

        with self.uow:

            if number_of_users != 0 or number_of_tickets != 0:
                raise DomainOperationError(
                    f"Client {client_id} cannot be deleted"
                )

            self.uow.clients.delete(client_id)

    # --------------------------------
    # Queries
    # --------------------------------

    def get_by_id(self, client_id: int) -> ClientResponseDTO:

        with self.uow:

            client = self.uow.clients.get(client_id)

            return ClientAssembler.to_dto(client)

    def get_all(self) -> list[ClientResponseDTO]:

        with self.uow:

            clients = self.uow.clients.get_all()

            return [ClientAssembler.to_dto(c) for c in clients]