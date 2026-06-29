# src/application/services/tickets/ticket_management_service.py

from __future__ import annotations

from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import (
    TicketDTO,
    TicketResponseDTO,
)
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.policy.ticket import TicketPolicy
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_management_service import (
    TicketManagementService as TicketManagementDomainService,
)
from src.domain.ticket import Ticket
from src.domain.uow.unit_of_work import UnitOfWork


class TicketManagementApplicationService:
    """
    Application service for management workflow actions.

    Responsibilities:
        - opens UnitOfWork;
        - checks Admin permission;
        - validates Client and executor references;
        - invokes TicketManagementService;
        - saves Ticket aggregate;
        - returns TicketResponseDTO.

    Does not decide whether a status transition is valid.
    That invariant belongs to Ticket.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    # --------------------------------
    # Internal helpers
    # --------------------------------

    def _require_ticket_operation(
        self,
        *,
        actor_admin_id: int,
    ) -> Admin:
        return self.actor.require_actor_admin(
            actor_admin_id=actor_admin_id,
            permission=AdminPermission.TICKET_OPERATION,
        )

    def _save_and_to_dto(
        self,
        ticket: Ticket,
    ) -> TicketResponseDTO:
        saved_ticket = self.uow.tickets.save(ticket)
        return TicketAssembler.to_dto(saved_ticket)

    def _get_manageable_ticket(
        self,
        *,
        ticket_id: int,
    ) -> Ticket:
        ticket = self.uow.tickets.get(ticket_id=ticket_id)

        client = self.uow.clients.get(
            client_id=ticket.client_id,
        )
        TicketPolicy.ensure_client_enabled(client)

        return ticket

    def _get_assignable_executor(
        self,
        *,
        ticket: Ticket,
        executor_id: int,
    ) -> Admin:
        if executor_id <= 0:
            raise DomainOperationError(
                "Executor id is required"
            )

        executor = self.uow.admins.get(
            admin_id=executor_id,
        )
        TicketPolicy.ensure_admin_enabled(executor)

        if ticket.department_id <= 0:
            raise DomainOperationError(
                "Cannot assign executor: Ticket has no department"
            )

        if executor.department_id <= 0:
            raise DomainOperationError(
                f"Cannot assign executor: "
                f"Admin {executor.employee_id} has no department"
            )

        department = self.uow.departments.get(
            department_id=ticket.department_id,
        )
        if not department.enabled:
            raise DomainOperationError(
                f"Cannot assign executor: "
                f"Department {department.department_id} is disabled"
            )

        if executor.department_id != ticket.department_id:
            raise DomainOperationError(
                f"Cannot assign executor: "
                f"Admin {executor.employee_id} belongs to department "
                f"{executor.department_id}, expected "
                f"{ticket.department_id}"
            )

        return executor

    # --------------------------------
    # Management workflow commands
    # --------------------------------

    def accept_ticket(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            ticket = self._get_manageable_ticket(
                ticket_id=ticket_dto.ticket_id,
            )

            TicketManagementDomainService.accept(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def reject_ticket(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            ticket = self._get_manageable_ticket(
                ticket_id=ticket_dto.ticket_id,
            )

            TicketManagementDomainService.reject(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def defer_ticket(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            ticket = self._get_manageable_ticket(
                ticket_id=ticket_dto.ticket_id,
            )

            TicketManagementDomainService.defer(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def schedule_ticket(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            ticket = self._get_manageable_ticket(
                ticket_id=ticket_dto.ticket_id,
            )

            if ticket_dto.planned_start_at is None:
                raise DomainOperationError(
                    "planned_start_at is required"
                )

            TicketManagementDomainService.schedule(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                planned_start_at=ticket_dto.planned_start_at,
                planned_finish_at=ticket_dto.planned_finish_at,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def assign_executor(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            ticket = self._get_manageable_ticket(
                ticket_id=ticket_dto.ticket_id,
            )
            executor = self._get_assignable_executor(
                ticket=ticket,
                executor_id=ticket_dto.executor_id,
            )

            TicketManagementDomainService.assign(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                executor_id=executor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def ready_to_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            ticket = self._get_manageable_ticket(
                ticket_id=ticket_dto.ticket_id,
            )
            executor = self._get_assignable_executor(
                ticket=ticket,
                executor_id=ticket_dto.executor_id,
            )

            if ticket_dto.planned_start_at is None:
                raise DomainOperationError(
                    "planned_start_at is required"
                )

            TicketManagementDomainService.ready_to_work(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                executor_id=executor.employee_id,
                planned_start_at=ticket_dto.planned_start_at,
                planned_finish_at=ticket_dto.planned_finish_at,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def cancel_ticket(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self._require_ticket_operation(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            ticket = self._get_manageable_ticket(
                ticket_id=ticket_dto.ticket_id,
            )

            TicketManagementDomainService.cancel(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)
