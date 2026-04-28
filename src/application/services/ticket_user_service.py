from src.application.dto.ticket_dto import TicketUserResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.ticket_user import TicketUser
from src.services.uow.uow import UnitOfWork


class TicketUserApplicationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    def _save_and_to_dto(self, ticket_user: TicketUser) -> TicketUserResponseDTO:
        saved_ticket = self.uow.user_tickets.save(ticket=ticket_user)
        return TicketAssembler.to_dto(saved_ticket)

    def _require_actor_for_create(self, ticket_dto: TicketDTO):
        actor = self.actor.require_actor_admin(actor_admin_id=ticket_dto.actor_admin_id,
                                               permission=AdminPermission.CREATE_TICKET)
        return actor

