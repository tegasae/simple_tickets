# src/application/services/ticket_command_service.py



from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import (
    TicketDTO,
    TicketResponseDTO,
)
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.exceptions import DomainOperationError
from src.domain.policy.ticket import TicketPolicy
from src.domain.rbac.permissions import AdminPermission
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment
from src.domain.uow.unit_of_work import UnitOfWork


class TicketCommandApplicationService:
    """
    Application service for non-workflow Ticket commands.

    Responsibilities:
        - opens UnitOfWork;
        - checks Admin permission;
        - validates cross-aggregate references;
        - invokes Ticket aggregate commands;
        - saves Ticket aggregate;
        - maps result to TicketResponseDTO.

    Workflow transitions belong to:
        - TicketManagementApplicationService;
        - TicketExecutionApplicationService;
        - TicketReviewApplicationService.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    # --------------------------------
    # Internal helpers
    # --------------------------------

    def _save_and_to_dto(
        self,
        ticket: Ticket,
    ) -> TicketResponseDTO:
        saved_ticket = self.uow.tickets.save(ticket)
        return TicketAssembler.to_dto(saved_ticket)

    def _require_ticket_operation(
        self,
        *,
        actor_admin_id: int,
    ):
        return self.actor.require_actor_admin(
            actor_admin_id=actor_admin_id,
            permission=AdminPermission.TICKET_OPERATION,
        )

    def _get_enabled_department(
        self,
        *,
        department_id: int,
    ):
        department = self.uow.departments.get(
            department_id=department_id,
        )

        if not department.enabled:
            raise DomainOperationError(
                f"Department {department.department_id} is disabled"
            )

        return department

    def _validate_user_reference(
        self,
        *,
        user_id: int,
        client,
    ) -> None:
        if user_id <= 0:
            return

        user = self.uow.users.get(user_id=user_id)

        TicketPolicy.ensure_user_enabled(user)
        TicketPolicy.ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

    def _validate_create_references(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> None:
        client = self.uow.clients.get(
            client_id=ticket_dto.client_id,
        )
        TicketPolicy.ensure_client_enabled(client)

        self._validate_user_reference(
            user_id=ticket_dto.user_id,
            client=client,
        )
        self._validate_user_reference(
            user_id=ticket_dto.contact_user_id,
            client=client,
        )

        if ticket_dto.department_id > 0:
            self._get_enabled_department(
                department_id=ticket_dto.department_id,
            )

        if ticket_dto.user_ticket_id > 0:
            user_ticket = self.uow.user_tickets.get(
                ticket_id=ticket_dto.user_ticket_id,
            )
            TicketPolicy.ensure_ticket_user_belongs_to_client(
                ticket_user=user_ticket,
                client=client,
            )

    # --------------------------------
    # Commands
    # --------------------------------

    def create_ticket(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            if ticket_dto.admin_id != actor.employee_id:
                raise DomainOperationError(
                    "Ticket admin_id must match actor_admin_id"
                )

            self._validate_create_references(
                ticket_dto=ticket_dto,
            )

            ticket = Ticket.create(
                ticket_id=0,
                client_id=ticket_dto.client_id,
                admin_id=actor.employee_id,
                text_of_ticket=ticket_dto.text_of_ticket,
                user_id=ticket_dto.user_id,
                contact_user_id=ticket_dto.contact_user_id,
                user_ticket_id=ticket_dto.user_ticket_id,
                department_id=ticket_dto.department_id,
                description=ticket_dto.description,
                is_remote=ticket_dto.is_remote,
                urgency_level=ticket_dto.urgency_level,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def update_ticket_text(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )
            ticket.update_ticket_text(
                text_of_ticket=ticket_dto.text_of_ticket,
            )

            return self._save_and_to_dto(ticket)

    def update_description(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )
            ticket.update_description(
                description=ticket_dto.description,
            )

            return self._save_and_to_dto(ticket)

    def add_comment(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )
            ticket.add_comment(
                Comment(
                    employee_id=actor.employee_id,
                    comment=ticket_dto.comment,
                )
            )

            return self._save_and_to_dto(ticket)

    def change_department(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )

            if ticket_dto.department_id > 0:
                self._get_enabled_department(
                    department_id=ticket_dto.department_id,
                )

            ticket.change_department(
                department_id=ticket_dto.department_id,
            )

            return self._save_and_to_dto(ticket)

    def delete_ticket(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> None:
        with self.uow:
            self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            # Ensures Ticket exists before DELETE.
            self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )

            self.uow.tickets.delete(
                ticket_id=ticket_dto.ticket_id,
            )

