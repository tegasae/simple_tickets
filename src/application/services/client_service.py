# src/application/services/client_service.py


from src.application.assemblers.assembler import ClientAssembler
from src.application.dto.client_dto import ClientDTO, ClientResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.client import Client
from src.domain.policy.client import ClientPolicy
from src.domain.policy.ticket import TicketPolicy
from src.domain.policy.ticket_workflow_policy import TicketWorkflowPolicy
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.statuses.ticket_status import TicketStatus

from src.domain.uow.unit_of_work import UnitOfWork


class ClientApplicationService:
    """
    Application services using UoW + DTO.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)
        self.ticket_management = TicketManagementService()

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

    def disable(self, dto_client: ClientDTO) -> ClientResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_OPERATION,
            )

            client = self.uow.clients.get(dto_client.client_id)
            client.disable()

            self._defer_tickets_due_to_client_disabled(
                client_id=client.client_id,
                actor_admin_id=actor.employee_id,
            )

            users = self.uow.users.get_all_by_client_id(
                client_id=client.client_id,
            )

            for user in users:
                user.disable()
                self.uow.users.save(user)

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

    def _defer_tickets_due_to_client_disabled(
            self,
            *,
            client_id: int,
            actor_admin_id: int,
    ) -> None:
        for tickets_batch in self.uow.tickets.iter_active_by_client_id(
                client_id=client_id,
                batch_size=500,
        ):
            for ticket in tickets_batch:
                if not TicketWorkflowPolicy.can_change_status(
                        current_status=ticket.current_status(),
                        new_status=TicketStatus.DEFERRED,
                ):
                    continue

                self.ticket_management.defer(
                    ticket=ticket,
                    actor_employee_id=actor_admin_id,
                    comment="Client disabled",
                )

                self.uow.tickets.save(ticket)