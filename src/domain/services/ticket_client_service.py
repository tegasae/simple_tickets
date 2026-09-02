# src/domain/services/ticket_client_service.py

from datetime import datetime

from src.domain.services.ticket_management_service import (
    TicketManagementService,
)
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket


class TicketClientService:

    @staticmethod
    def handle_client_disabled(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str,
        date_created: datetime | None = None,
    ) -> bool:
        current_status = ticket.current_status_record().status

        if current_status in {
            TicketStatus.CREATED,
            TicketStatus.CREATED_FROM_TICKET_USER,
        }:
            TicketManagementService.reject(
                ticket=ticket,
                actor_employee_id=actor_employee_id,
                comment=comment,
                date_created=date_created,
            )
            return True

        if current_status in {
            TicketStatus.ACCEPTED,
            TicketStatus.SCHEDULED,
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
        }:
            TicketManagementService.defer(
                ticket=ticket,
                actor_employee_id=actor_employee_id,
                comment=comment,
                date_created=date_created,
            )
            return True

        return False