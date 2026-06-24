# src/domain/policy/ticket_workflow_policy.py

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import (
    TicketStatus,
    get_ticket_state,
)


class TicketWorkflowPolicy:
    @staticmethod
    def ensure_can_change_status(
        *,
        current_status: TicketStatus,
        new_status: TicketStatus,
    ) -> None:
        current_status = TicketStatus(current_status)
        new_status = TicketStatus(new_status)

        current_state = get_ticket_state(current_status)

        if current_state.terminal:
            raise DomainOperationError(
                f"Ticket is terminal: {current_status.value}"
            )

        if not current_state.allows_transition_to(new_status):
            raise DomainOperationError(
                "Ticket status transition is not allowed: "
                f"{current_status.value} -> {new_status.value}"
            )

    @staticmethod
    def can_change_status(
        *,
        current_status: TicketStatus,
        new_status: TicketStatus,
    ) -> bool:
        try:
            TicketWorkflowPolicy.ensure_can_change_status(
                current_status=current_status,
                new_status=new_status,
            )
            return True
        except DomainOperationError:
            return False