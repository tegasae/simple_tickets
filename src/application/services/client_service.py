# src/application/services/client_service.py


from src.application.assemblers.assembler import ClientAssembler
from src.application.dto.client_dto import ClientDTO, ClientResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.client import Client
from src.domain.policy.client import ClientPolicy
from src.domain.policy.ticket import TicketPolicy
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_workflow_service import TicketWorkflowService
from src.services.uow.uow import UnitOfWork




class ClientApplicationService:
    """
    Application services using UoW + DTO.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)
        self.workflow = TicketWorkflowService()

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
                permission=AdminPermission.CLIENT_OPERATION,
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
                permission=AdminPermission.CLIENT_OPERATION,
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
            actor=self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_OPERATION,
            )
            client = self.uow.clients.get(dto_client.client_id)
            client.disable()
            for tickets_batch in self.uow.tickets.iter_active_by_client_id(
                    client_id=client.client_id,
                    batch_size=500,
            ):
                for ticket in tickets_batch:
                    changed = self.workflow.defer_ticket_due_to_client_disabled(
                        ticket=ticket,
                        actor_admin_id=actor.employee_id,
                    )

                    if changed:
                        self.uow.tickets.save(ticket=ticket)
            users=self.uow.users.get_all_by_client_id(client_id=client.client_id)
            for u in users:
                self.workflow.disable_user_due_to_client_disabled(user=u)
                self.uow.users.save(u)
            return self._save_and_to_dto(client)

    def enable(self, dto_client:ClientDTO) -> ClientResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_OPERATION,
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
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_OPERATION,
            )

            client = self.uow.clients.get(dto_client.client_id)

            ClientPolicy.ensure_can_delete(
                client=client,
                has_users=self.uow.users.does_client_exist(client.client_id),
                has_tickets=self.uow.tickets.does_client_exist(client.client_id),
                has_user_tickets=self.uow.user_tickets.does_client_exist(client.client_id)
            )
            self.uow.clients.delete(client.client_id)

            return ClientAssembler.to_dto(client)
    # --------------------------------
    # Queries
    # --------------------------------

    def get_by_id(self, dto_client:ClientDTO) -> ClientResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_VIEW,
            )
            client = self.uow.clients.get(dto_client.client_id)
            return ClientAssembler.to_dto(client)

    def get_all(self,dto_client:ClientDTO) -> list[ClientResponseDTO]:

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_VIEW,
            )
            clients = self.uow.clients.get_all()
            return [ClientAssembler.to_dto(c) for c in clients]
