from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import TicketDTO, TicketResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper

from src.domain.policy.ticket import TicketPolicy

from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment, ExecutorAssignment
from src.domain.rbac.permissions import AdminPermission

from src.services.uow.uow import UnitOfWork


class TicketApplicationService:
    """
    Application service for Ticket.

    Responsibilities:
        - permission checks
        - cross-aggregate validation
        - orchestration with UnitOfWork
        - persistence through repositories
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    # --------------------------------
    # Helpers
    # --------------------------------

    def _save_and_to_dto(self, ticket: Ticket) -> TicketResponseDTO:
        saved_ticket = self.uow.tickets.save(ticket=ticket)
        return TicketAssembler.to_dto(saved_ticket)

    def _require_actor_for_create(self, ticket_dto: TicketDTO):
        actor = self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                               permission=AdminPermission.CREATE_TICKET)
        return actor






    def _validate_references(self, ticket_dto: TicketDTO):
        """
        Validates referenced entities and returns the effective admin_id.
        """

        admin_id = ticket_dto.admin_id

        admin = self.uow.admins.get(admin_id)
        client = self.uow.clients.get(ticket_dto.client_id)

        TicketPolicy.ensure_admin_enabled(admin)
        TicketPolicy.ensure_client_enabled(client)

        if ticket_dto.user_id:
            user = self.uow.users.get(ticket_dto.user_id)
            TicketPolicy.ensure_user_enabled(user)
            TicketPolicy.ensure_user_belongs_to_client(user, client)

        if ticket_dto.contact_user_id:
            contact_user = self.uow.users.get(ticket_dto.contact_user_id)
            TicketPolicy.ensure_user_enabled(contact_user)
            TicketPolicy.ensure_user_belongs_to_client(contact_user, client)

        if ticket_dto.executor_id:
            executor = self.uow.admins.get(ticket_dto.executor_id)
            TicketPolicy.ensure_admin_enabled(executor)

        if ticket_dto.user_ticket_id:
            user_ticket = self.uow.user_tickets.get(ticket_dto.user_ticket_id)
            TicketPolicy.ensure_ticket_user_belongs_to_client(user_ticket, client)




    # --------------------------------
    # Create
    # --------------------------------

    def create_ticket(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.CREATE_TICKET)

            self._validate_references(ticket_dto)
            user_description=""
            if ticket_dto.user_ticket_id:
                user_ticket=self.uow.user_tickets.get(ticket_id=ticket_dto.user_ticket_id)
                user_description=user_ticket.description

            ticket = Ticket.create(
                ticket_id=0,
                client_id=ticket_dto.client_id,
                admin_id=ticket_dto.admin_id,
                description=ticket_dto.description,
                user_description=user_description,
                text_of_ticket=ticket_dto.text_of_ticket,
                user_id=ticket_dto.user_id,
                contact_user_id=ticket_dto.contact_user_id,
                is_remote=ticket_dto.is_remote,
                urgency_level=ticket_dto.urgency_level,
                user_ticket_id=ticket_dto.user_ticket_id,
                executor_id=ticket_dto.executor_id,
                comment=ticket_dto.comment,
            )
            if user_ticket.ticket_id:
                user_ticket.confirm(actor_employee_id=ticket.admin_id)
                self.uow.user_tickets.save(user_ticket)
            return self._save_and_to_dto(ticket)




    # --------------------------------
    # Status operations
    # --------------------------------

    def change_status(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:


            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.UPDATE_TICKET)
            self._validate_references(ticket_dto)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            ticket.change_status(
                new_status=ticket_dto.status,
                actor_employee_id=ticket_dto.admin_id,
            )

            return self._save_and_to_dto(ticket)

    def defer(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:


        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.UPDATE_TICKET)

            self._validate_references(ticket_dto)
            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            ticket.defer(actor_employee_id=ticket_dto.admin_id)

            return self._save_and_to_dto(ticket)

    def at_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.UPDATE_TICKET)

            self._validate_references(ticket_dto)
            if ticket_dto.executor_id:
                executor = self.uow.admins.get(ticket_dto.executor_id)
                TicketPolicy.ensure_admin_enabled(executor)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)

            ticket.at_work(
                actor_employee_id=ticket_dto.admin_id,
                executor_id=ticket_dto.executor_id,
            )

            if ticket.user_ticket_id:
                user_ticket=self.uow.user_tickets.get(ticket_id=ticket_dto.user_ticket_id)
                user_ticket.start_work(actor_employee_id=ticket_dto.executor_id)
                self.uow.user_tickets.save(user_ticket)

            return self._save_and_to_dto(ticket)

    def execute(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.UPDATE_TICKET)

            self._validate_references(ticket_dto)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            ticket.execute(actor_employee_id=ticket_dto.admin_id)

            if ticket.user_ticket_id:
                user_ticket=self.uow.user_tickets.get(ticket_id=ticket_dto.user_ticket_id)
                user_ticket.execute(actor_employee_id=ticket_dto.admin_id)
                self.uow.user_tickets.save(user_ticket)

            return self._save_and_to_dto(ticket)

    def cancel(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.UPDATE_TICKET)

            self._validate_references(ticket_dto)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            ticket.cancel(
                actor_employee_id=ticket_dto.admin_id,
                comment=ticket_dto.comment,
            )

            if ticket.user_ticket_id:
                user_ticket=self.uow.user_tickets.get(ticket_id=ticket_dto.user_ticket_id)
                user_ticket.cancel_by_admin(actor_employee_id=ticket_dto.admin_id)
                self.uow.user_tickets.save(user_ticket)


            return self._save_and_to_dto(ticket)

    # --------------------------------
    # Comments
    # --------------------------------

    def add_comment(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.UPDATE_TICKET)

            self._validate_references(ticket_dto)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            ticket.add_comment(
                Comment(
                    employee_id=ticket_dto.admin_id,
                    comment=ticket_dto.comment,
                )
            )

            return self._save_and_to_dto(ticket)

    # --------------------------------
    # Executors
    # --------------------------------

    def assign_executor(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.UPDATE_TICKET)

            self._validate_references(ticket_dto)
            executor = self.uow.admins.get(ticket_dto.executor_id)
            TicketPolicy.ensure_admin_enabled(executor)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            ticket.add_executor(
                ExecutorAssignment(
                    admin_id=ticket_dto.admin_id,
                    executor_id=ticket_dto.executor_id,
                )
            )

            return self._save_and_to_dto(ticket)

    # --------------------------------
    # Delete
    # --------------------------------

    def delete(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> None:

        with self.uow:


            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.DELETE_TICKET)

            self._validate_references(ticket_dto)
            ticket=self.uow.tickets.get(ticket_dto.ticket_id)


            if ticket.user_ticket_id:
                self.uow.user_tickets.get(ticket_id=ticket_dto.user_ticket_id)
                self.uow.user_tickets.delete(ticket.user_ticket_id)


            self.uow.tickets.delete(ticket_dto.ticket_id)

    # --------------------------------
    # Queries
    # --------------------------------

    def get_by_id(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.VIEW_TICKET)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            return TicketAssembler.to_dto(ticket)

    def get_all(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.UPDATE_TICKET)



            tickets = self.uow.tickets.get_all()
            return [TicketAssembler.to_dto(ticket) for ticket in tickets]
