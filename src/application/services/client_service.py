# src/application/services/client_service.py

from src.application.assemblers.assembler import ClientAssembler
from src.application.dto.client_dto import (
    ClientDTO,
    ClientResponseDTO,
)
from src.application.exceptions import ApplicationValidateError
from src.application.helper.actor_helper import EmployeeActorHelper

from src.domain.client import Client
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.client_service import ClientService
from src.domain.services.ticket_sync_service import TicketSyncService
from src.domain.uow.unit_of_work import UnitOfWork


class ClientApplicationService:
    """
    Application service for Client.

    Responsibilities:
    - opens UnitOfWork;
    - validates actor and permissions;
    - loads required aggregates;
    - obtains external domain facts from repositories;
    - calls ClientService;
    - persists changed aggregates;
    - converts results to DTO.

    Does not contain:
    - RBAC business logic;
    - SQL;
    - Client business rules;
    - Ticket workflow rules;
    - Client disable cascade rules;
    - cross-aggregate business decisions.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

        self.ticket_sync_service = TicketSyncService()

        self.client_service = ClientService(
            ticket_sync_service=self.ticket_sync_service,
        )


    # ==================================================================
    # Create
    # ==================================================================

    def create_client(
        self,
        dto_client: ClientDTO,
    ) -> ClientResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin_any(
                actor_admin_id=dto_client.actor_admin_id,
                permissions=(AdminPermission.CLIENT_OPERATION,AdminPermission.CLIENT_CREATE,AdminPermission.CLIENT_DECISION),
            )

            client = self.client_service.create(
                name=dto_client.name,
                email=dto_client.email,
                address=dto_client.address,
                phone=dto_client.phone,
                description=dto_client.description,
                created_by_admin_id=actor.employee_id,
            )

            return self._save_and_to_dto(
                client
            )

    # ==================================================================
    # Update
    # ==================================================================

    def update_contact(
        self,
        dto_client: ClientDTO,
    ) -> ClientResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_OPERATION,
            )

            client = self.uow.clients.get(
                client_id=dto_client.client_id,
            )

            self.client_service.update(
                client=client,
                name=dto_client.name,
                email=dto_client.email,
                address=dto_client.address,
                phone=dto_client.phone,
                description=dto_client.description,
            )

            return self._save_and_to_dto(
                client
            )

    # ==================================================================
    # Enable / disable
    # ==================================================================

    def enable(
        self,
        dto_client: ClientDTO,
    ) -> ClientResponseDTO:
        """
        Enable Client.

        Enabling Client does not automatically:
        - enable Users;
        - change Ticket statuses;
        - change TicketUser statuses.
        """

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_DECISION,
            )

            client = self.uow.clients.get(
                client_id=dto_client.client_id,
            )

            self.client_service.enable(
                client=client,
            )

            return self._save_and_to_dto(
                client
            )

    def disable(
        self,
        dto_client: ClientDTO,
    ) -> ClientResponseDTO:
        """
        Disable Client.

        Application layer:
        - loads Client;
        - loads related Users;
        - loads related Tickets;
        - loads related TicketUser aggregates;
        - calls ClientService;
        - persists aggregates changed by ClientService.

        All cascade rules belong to ClientService.
        """

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_DECISION,
            )

            client = self.uow.clients.get(
                client_id=dto_client.client_id,
            )

            users = self.uow.users.get_all_by_client_id(
                client_id=client.client_id,
            )
            # TODO Использовать метода get_open, когда там будет возможность использовать client_id
            tickets = self.uow.tickets.get_by_client_id(
                client_id=client.client_id,
            )

            # Mapping:
            #
            #     TicketUser.user_ticket_id -> TicketUser
            #
            # ClientService itself decides which TicketUser
            # aggregates must actually be changed.
            # TODO Использовать метода get_open, когда там будет возможность использовать client_id
            ticket_users = self.uow.user_tickets.get_by_client_id(client_id=client.client_id)


            result = self.client_service.disable(
                client=client,
                users=users,
                tickets=tickets,
                ticket_users=ticket_users,
                actor_employee_id=actor.employee_id,
            )

            # Save only dependent aggregates that were actually changed.

            for user in result.users:
                self.uow.users.save(
                    user
                )

            for ticket in result.tickets:
                self.uow.tickets.save(
                    ticket
                )

            for ticket_user in result.ticket_users:
                self.uow.user_tickets.save(
                    ticket_user
                )

            # Client itself is always changed by disable().
            #
            # save(client) also performs optimistic version check
            # for the Client aggregate.
            return self._save_and_to_dto(
                client
            )

    # ==================================================================
    # Delete
    # ==================================================================

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

            client = self.uow.clients.get(
                client_id=dto_client.client_id,
            )

            self.client_service.ensure_can_delete(
                client=client,
                has_users=(
                    self.uow.users.does_client_exist(
                        client.client_id,
                    )
                ),
                has_tickets=(
                    self.uow.tickets.does_client_exist(
                        client.client_id,
                    )
                ),
                has_user_tickets=(
                    self.uow.user_tickets.does_client_exist(
                        client.client_id,
                    )
                ),
            )

            self.uow.clients.delete(
                client.client_id,
            )

            return ClientAssembler.to_dto(
                client
            )

    # ==================================================================
    # Queries
    # ==================================================================

    def get_by_id(
        self,
        dto_client: ClientDTO,
    ) -> ClientResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_VIEW,
            )

            client = self.uow.clients.get(
                client_id=dto_client.client_id,
            )

            return ClientAssembler.to_dto(
                client
            )

    def get_all(
        self,
        dto_client: ClientDTO,
    ) -> list[ClientResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=dto_client.actor_admin_id,
                permission=AdminPermission.CLIENT_VIEW,
            )

            clients = self.uow.clients.get_all()

            return [
                ClientAssembler.to_dto(client)
                for client in clients
            ]

    # ==================================================================
    # Helpers
    # ==================================================================

    def _save_and_to_dto(
        self,
        client: Client,
    ) -> ClientResponseDTO:
        saved_client = self.uow.clients.save(
            client
        )
        if not saved_client:
            raise ApplicationValidateError(f"The client {client.client_id} cannot be saved")
        return ClientAssembler.to_dto(
            saved_client
        )
