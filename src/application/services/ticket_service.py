from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import TicketDTO, TicketResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper

from src.domain.policy.ticket import TicketPolicy


from src.domain.ticket import Ticket
from src.domain.rbac.permissions import AdminPermission

from src.services.uow.uow import UnitOfWork


class TicketApplicationService:
    """
    Application services for Ticket.

    Responsibilities:
        - permission checks
        - cross-aggregate validation
        - orchestration with UnitOfWork
        - persistence through repositories
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)
        self.workflow = TicketWorkflowService()
    # --------------------------------
    # Helpers
    # --------------------------------

    def _save_and_to_dto(self, ticket: Ticket) -> TicketResponseDTO:
        saved_ticket = self.uow.tickets.save(ticket=ticket)
        return TicketAssembler.to_dto(saved_ticket)

    def _require_actor_for_create(self, ticket_dto: TicketDTO):
        actor = self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                               permission=AdminPermission.TICKET_OPERATION)
        return actor






    def _validate_references(self, ticket_dto: TicketDTO):
        """
        Validates referenced entities and returns the effective admin_id.
        """

        admin_id = ticket_dto.admin_id

        admin = self.uow.admins.get(admin_id)
        TicketPolicy.ensure_admin_enabled(admin)
        client=None
        if ticket_dto.client_id:
            client = self.uow.clients.get(ticket_dto.client_id)
            TicketPolicy.ensure_client_enabled(client)



        if ticket_dto.user_id and ticket_dto.client_id:
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
                                           permission=AdminPermission.TICKET_OPERATION)

            self._validate_references(ticket_dto)

            user_ticket = None
            if ticket_dto.user_ticket_id:
                user_ticket = self.uow.user_tickets.get(ticket_dto.user_ticket_id)
            ticket = TicketWorkflowService.create_from_admin(
                ticket_id=0,
                client_id=ticket_dto.client_id,
                admin_id=ticket_dto.admin_id,
                text_of_ticket=ticket_dto.text_of_ticket,
                user_id=ticket_dto.user_id,
                contact_user_id=ticket_dto.contact_user_id,
                is_remote=ticket_dto.is_remote,
                urgency_level=ticket_dto.urgency_level,
                user_ticket=user_ticket,
                executor_id=ticket_dto.executor_id,
                comment=ticket_dto.comment,
            )


            if user_ticket is not None:
                self.uow.user_tickets.save(user_ticket)

            return self._save_and_to_dto(ticket)




    # --------------------------------
    # Status operations
    # --------------------------------


    def defer(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:


        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.TICKET_OPERATION)

            self._validate_references(ticket_dto)
            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            self.workflow.defer_admin(ticket=ticket,actor_admin_id=ticket_dto.actor_admin_id)

            return self._save_and_to_dto(ticket)

    def at_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.TICKET_OPERATION)

            self._validate_references(ticket_dto)
            ticket = self.uow.tickets.get(ticket_dto.ticket_id)

            user_ticket = None
            if ticket.user_ticket_id:
                user_ticket = self.uow.user_tickets.get(ticket.user_ticket_id)

            self.workflow.start_work(
                ticket=ticket,
                user_ticket=user_ticket,
                actor_admin_id=ticket_dto.admin_id,
                executor_id=ticket_dto.executor_id,
            )

            if user_ticket is not None:
                self.uow.user_tickets.save(user_ticket)
            return self._save_and_to_dto(ticket)

    def execute(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.TICKET_OPERATION)

            self._validate_references(ticket_dto)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)

            user_ticket = None
            if ticket.user_ticket_id:
                user_ticket = self.uow.user_tickets.get(ticket.user_ticket_id)

            self.workflow.execute(
                ticket=ticket,
                user_ticket=user_ticket,
                actor_admin_id=ticket_dto.admin_id,
                comment=ticket_dto.comment,
            )
            if user_ticket is not None:
                self.uow.user_tickets.save(user_ticket)
            return self._save_and_to_dto(ticket)

    def cancel(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.TICKET_OPERATION)

            self._validate_references(ticket_dto)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            user_ticket = None
            if ticket.user_ticket_id:
                user_ticket = self.uow.user_tickets.get(ticket.user_ticket_id)



            self.workflow.cancel_by_admin(ticket=ticket,user_ticket=user_ticket,actor_admin_id=ticket_dto.actor_admin_id,comment=ticket_dto.comment)

            if user_ticket is not None:
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
                                           permission=AdminPermission.TICKET_OPERATION)

            self._validate_references(ticket_dto)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)


            self.workflow.add_comment_from_admin(ticket=ticket,actor_admin_id=ticket_dto.actor_admin_id,comment=ticket_dto.comment)

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
                                           permission=AdminPermission.TICKET_OPERATION)

            self._validate_references(ticket_dto)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            self.workflow.assign_executor(ticket=ticket,actor_admin_id=ticket_dto.actor_admin_id,executor_id=ticket_dto.executor_id)

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
                                           permission=AdminPermission.TICKET_OPERATION)

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
                                           permission=AdminPermission.TICKET_VIEW)

            ticket = self.uow.tickets.get(ticket_dto.ticket_id)
            return TicketAssembler.to_dto(ticket)

    def get_all(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.TICKET_VIEW)



            tickets = self.uow.tickets.get_all()
            return [TicketAssembler.to_dto(ticket) for ticket in tickets]


