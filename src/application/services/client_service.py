# src/application/services/client_service.py


from src.application.assemblers.assembler import ClientAssembler
from src.application.dto.client_dto import ClientDTO, ClientResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.client import Client
from src.domain.exceptions import DomainOperationError
from src.domain.policy.ticket import TicketPolicy
from src.domain.rbac.permissions import AdminPermission
from src.services.uow.uow import UnitOfWork




class ClientApplicationService:
    """
    Application service using UoW + DTO.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    def _save_and_to_dto(self, client: Client) -> ClientResponseDTO:
        saved_client = self.uow.clients.save(client)
        return ClientAssembler.to_dto(saved_client)


    def _validate_references(self, client_dto: ClientDTO):
        """
        Validates referenced entities and returns the effective admin_id.
        """

        actor_admin=self.uow.admins.get(admin_id=client_dto.actor_admin_id)
        TicketPolicy.ensure_admin_enabled(actor_admin)
        if client_dto.admin_id:
            admin = self.uow.admins.get(client_dto.admin_id)
            TicketPolicy.ensure_admin_enabled(admin)
        if client_dto.client_id:
            client = self.uow.clients.get(client_dto.client_id)
            TicketPolicy.ensure_client_enabled(client)







    # --------------------------------
    # Create
    # --------------------------------

    def create_client(self, dto_client: ClientDTO) -> ClientResponseDTO:

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.OPERATION_CLIENT,
            )
            client = Client.create(
                client_id=0,
                name=dto_client.name,
                email=dto_client.email,
                address=dto_client.address,
                phone=dto_client.phone,
                created_by_admin_id=actor.employee_id
            )

            client = self.uow.clients.save(client)

            return self._save_and_to_dto(client)

    # --------------------------------
    # Update
    # --------------------------------

    def update_contact(self, dto_client: ClientDTO) -> ClientResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.OPERATION_CLIENT,
            )
            client = self.uow.clients.get(dto_client.client_id)

            client.update_contact_info(
                email=dto_client.email,
                address=dto_client.address,
                phone=dto_client.phone,
            )

            return self._save_and_to_dto(client)

    # --------------------------------
    # Enable / disable
    # --------------------------------

    def disable(self, dto_client:ClientDTO) -> ClientResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.OPERATION_CLIENT,
            )
            client = self.uow.clients.get(dto_client.client_id)
            client.disable()



            return self._save_and_to_dto(client)

    def enable(self, dto_client:ClientDTO) -> ClientResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.OPERATION_CLIENT,
            )
            client = self.uow.clients.get(dto_client.client_id)
            client.enable()



            return self._save_and_to_dto(client)

    # --------------------------------
    # Delete
    # --------------------------------

    def delete(
        self,
        *,
        dto_client: ClientDTO,
    ) -> ClientResponseDTO:

        with (self.uow):
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.OPERATION_CLIENT,
            )
            # todo сделать доменную политику, которая учитывает что нельзя удалить клиента у которого есть user и заявки
            if (self.uow.users.does_client_exist(dto_client.client_id) or
                self.uow.tickets.does_client_exist(dto_client.client_id) or
                self.uow.user_tickets.does_client_exist(dto_client.client_id)):
                raise DomainOperationError(
                    f"Client {dto_client.name} cannot be deleted"
                )
            client=self.uow.clients.get(dto_client.client_id)
            self.uow.clients.delete(dto_client.client_id)
            return ClientAssembler.to_dto(client)
    # --------------------------------
    # Queries
    # --------------------------------

    def get_by_id(self, dto_client:ClientDTO) -> ClientResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.OPERATION_CLIENT,
            )
            client = self.uow.clients.get(dto_client.client_id)
            return ClientAssembler.to_dto(client)

    def get_all(self,dto_client:ClientDTO) -> list[ClientResponseDTO]:

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.OPERATION_CLIENT,
            )
            clients = self.uow.clients.get_all()

            return [ClientAssembler.to_dto(c) for c in clients]
