from src.application.assemblers.assembler import TicketUserAssembler
from src.application.dto.ticket_dto import TicketUserResponseDTO, TicketDTO, TicketUserDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.ticket_user import TicketUser
from src.services.uow.uow import UnitOfWork


class TicketUserApplicationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    def _save_and_to_dto(self, ticket_user: TicketUser) -> TicketUserResponseDTO:
        saved_ticket = self.uow.user_tickets.save(ticket=ticket_user)
        return TicketUserAssembler.to_dto(saved_ticket)

    def _require_user_actor_for_create(self, ticket_user_dto: TicketUserDTO):
        user_actor = self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                               permission=UserPermission.CREATE_TICKET)
        return user_actor


    def create_ticket(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                           permission=AdminPermission.CREATE_TICKET)

            self._validate_references(ticket_dto)

            ticket = Ticket.create(
                ticket_id=0,
                client_id=ticket_dto.client_id,
                admin_id=ticket_dto.admin_id,
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
