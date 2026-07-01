
from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import TicketDTO, TicketResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.rbac.permissions import AdminPermission
from src.domain.uow.unit_of_work import UnitOfWork


class TicketQueryApplicationService:
    """
    Application service for Ticket queries.

    Does not modify Ticket aggregates.
    Does not call domain workflow services.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    # --------------------------------
    # Queries
    # --------------------------------

    def get_by_id(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            ticket = self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )

            return TicketAssembler.to_dto(ticket)

    def get_all(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            return [
                TicketAssembler.to_dto(ticket)
                for ticket in self.uow.tickets.get_all()
            ]

    def get_by_user_ticket_id(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            ticket = self.uow.tickets.get_by_user_ticket_id(
                user_ticket_id=ticket_dto.user_ticket_id,
            )

            return TicketAssembler.to_dto(ticket)
