# src/domain/policy/ticket_workflow_policy.py

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import TicketStatus, TERMINAL_TICKET_STATUSES, ALLOWED_TICKET_STATUS_TRANSITIONS


class TicketWorkflowPolicy:
    """
    Проверяет допустимость переходов между статусами Ticket.

    Граф переходов хранится рядом с TicketStatus,
    потому что это часть описания workflow-статусов.

    Эта policy не проверяет:
    - роли actor-а;
    - department;
    - executor;
    - плановые и фактические даты.

    Она проверяет только сам переход:
    current_status -> new_status.
    """

    @staticmethod
    def ensure_can_change_status(
        *,
        current_status: TicketStatus,
        new_status: TicketStatus,
    ) -> None:
        current_status = TicketStatus(current_status)
        new_status = TicketStatus(new_status)

        TicketWorkflowPolicy._ensure_not_terminal(current_status)
        TicketWorkflowPolicy._ensure_transition_allowed(
            current_status=current_status,
            new_status=new_status,
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

    @staticmethod
    def _ensure_not_terminal(current_status: TicketStatus) -> None:
        if current_status in TERMINAL_TICKET_STATUSES:
            raise DomainOperationError(
                f"Ticket in terminal status {current_status} cannot be changed"
            )

    @staticmethod
    def _ensure_transition_allowed(
        *,
        current_status: TicketStatus,
        new_status: TicketStatus,
    ) -> None:
        allowed_statuses = ALLOWED_TICKET_STATUS_TRANSITIONS.get(
            current_status,
            frozenset(),
        )

        if new_status not in allowed_statuses:
            raise DomainOperationError(
                f"Transition {current_status} -> {new_status} is not allowed"
            )