# src/domain/policy/ticket_workflow_policy.py

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import TicketStatus, TERMINAL_TICKET_STATUSES, ALLOWED_TICKET_STATUS_TRANSITIONS


class TicketWorkflowPolicy:
    """
    Проверяет допустимость переходов между статусами Ticket.

    Граф переходов хранится в ticket_status.py рядом с TicketStatus,
    потому что это часть описания workflow-статусов.

    Эта policy проверяет только общий граф:

        current_status -> new_status

    Она НЕ проверяет:
    - роли actor-а;
    - permissions;
    - является ли actor текущим executor;
    - department;
    - executor.department_id == ticket.department_id;
    - enabled/disabled admin;
    - enabled/disabled department;
    - наличие planned_start_at;
    - наличие executor_id;
    - наличие actual_started_at / actual_finished_at.

    Валидность payload-а проверяет TicketStatusRecord.
    Создание корректных записей выполняет TicketStatusRecordFactory.
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
                f"Ticket in terminal status {current_status.value} cannot be changed"
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
                f"Transition {current_status.value} -> {new_status.value} is not allowed"
            )