#src/services/ticket_service.py
from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import TicketDTO, TicketResponseDTO
from src.application.helper.empoyee_helper import EmployeeHelper
from src.domain.ticket import Ticket, TicketStatus

from src.domain.ticket_components import Comment, ExecutorAssignment
from src.domain.rbac.permissions import AdminPermission

from src.services.uow.uow import UnitOfWork


class TicketApplicationService:
    """
    Application service for Ticket.

    Uses:
        - UnitOfWork
        - Authorizer
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.helper = EmployeeHelper(self.uow)
    # --------------------------------
    # Helpers
    # --------------------------------

    def _save_and_to_dto(self, ticket: Ticket) -> TicketResponseDTO:
        saved_ticket = self.uow.tickets.save(ticket=ticket)
        return TicketAssembler.to_dto(saved_ticket)

    # --------------------------------
    # Create
    # --------------------------------

    def create_ticket(
        self,
        *,
        ticket_dto: TicketDTO
    ) -> TicketResponseDTO:

        with self.uow:
            actor = self.helper.require_actor(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.CREATE_TICKET,
            )

            ticket = Ticket.create(
                ticket_id=0,
                client_id=ticket_dto.client_id,
                admin_id=ticket_dto.admin_id if ticket_dto.admin_id else actor.employee_id,
                description=ticket_dto.description,
                text_of_ticket=ticket_dto.text_of_ticket,
                user_id=ticket_dto.user_id,
                contact_user_id=ticket_dto.contact_user_id,
                is_remote=ticket_dto.is_remote,
                urgency_level=ticket_dto.urgency_level,
                user_ticket_id=ticket_dto.user_ticket_id,
                executor_id=ticket_dto.executor_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    # --------------------------------
    # Status operations
    # --------------------------------

    def change_status(
        self,
        *,
        actor_admin_id: int,
        ticket_id: int,
        new_status: TicketStatus,
    ) -> Ticket:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)

            ticket = self.uow.tickets.get(ticket_id)
            ticket.change_status(new_status, actor_admin_id)

            return self.uow.tickets.save(ticket)

    def defer(
        self,
        *,
        actor_admin_id: int,
        ticket_id: int,
    ) -> Ticket:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)

            ticket = self.uow.tickets.get(ticket_id)
            ticket.defer(actor_admin_id)

            return self.uow.tickets.save(ticket)

    def at_work(
        self,
        *,
        actor_admin_id: int,
        ticket_id: int,
        executor_id: int = 0,
    ) -> Ticket:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)

            ticket = self.uow.tickets.get(ticket_id)
            ticket.at_work(actor_admin_id, executor_id)

            return self.uow.tickets.save(ticket)

    def execute(
        self,
        *,
        actor_admin_id: int,
        ticket_id: int,
    ) -> Ticket:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)

            ticket = self.uow.tickets.get(ticket_id)
            ticket.execute(actor_admin_id)

            return self.uow.tickets.save(ticket)

    def cancel(
        self,
        *,
        actor_admin_id: int,
        ticket_id: int,
        comment: str,
    ) -> Ticket:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)

            ticket = self.uow.tickets.get(ticket_id)
            ticket.cancel(actor_admin_id, comment)

            return self.uow.tickets.save(ticket)

    # --------------------------------
    # Comments
    # --------------------------------

    def add_comment(
        self,
        *,
        actor_admin_id: int,
        ticket_id: int,
        comment: str,
    ) -> Ticket:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)

            ticket = self.uow.tickets.get(ticket_id)
            ticket.add_comment(
                Comment(
                    employee_id=actor_admin_id,
                    comment=comment,
                )
            )

            return self.uow.tickets.save(ticket)

    # --------------------------------
    # Executors
    # --------------------------------

    def assign_executor(
        self,
        *,
        actor_admin_id: int,
        ticket_id: int,
        executor_id: int,
    ) -> Ticket:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)

            ticket = self.uow.tickets.get(ticket_id)
            ticket.add_executor(
                ExecutorAssignment(
                    admin_id=actor_admin_id,
                    executor_id=executor_id,
                )
            )

            return self.uow.tickets.save(ticket)

    # --------------------------------
    # Delete
    # --------------------------------

    def delete(
        self,
        *,
        actor_admin_id: int,
        ticket_id: int,
    ) -> None:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)

            self.uow.tickets.delete(ticket_id)

    # --------------------------------
    # Queries
    # --------------------------------

    def get_by_id(
        self,
        *,
        actor_admin_id: int,
        ticket_id: int,
    ) -> Ticket:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.VIEW_ADMIN)

            return self.uow.tickets.get(ticket_id)

    def get_all(
        self,
        *,
        actor_admin_id: int,
    ) -> list[Ticket]:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.VIEW_ADMIN)

            return self.uow.tickets.get_all()