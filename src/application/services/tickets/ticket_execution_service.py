# src/application/services/ticket_execution_service.py



from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import TicketDTO, TicketResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.policies.ticket import TicketPolicy
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_execution_service import (
    TicketExecutionService as TicketExecutionDomainService,
)
from src.domain.ticket import Ticket
from src.domain.uow.unit_of_work import UnitOfWork


class TicketExecutionApplicationService:
    """
    Application service for Ticket execution actions.

    Domain workflow rules belong to TicketExecutionService.
    This class is responsible for:
        - UnitOfWork;
        - RBAC;
        - aggregate loading;
        - cross-aggregate executor checks;
        - persistence and DTO mapping.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    # --------------------------------
    # Helpers
    # --------------------------------

    def _save_and_to_dto(
        self,
        ticket: Ticket,
    ) -> TicketResponseDTO:
        saved_ticket = self.uow.tickets.save(ticket)
        return TicketAssembler.to_dto(saved_ticket)

    def _get_executor_for_ticket(
        self,
        *,
        ticket: Ticket,
        executor_id: int,
    ) -> Admin:
        if executor_id <= 0:
            raise DomainOperationError("Executor id is required")

        executor = self.uow.admins.get(
            admin_id=executor_id,
        )
        TicketPolicy.ensure_admin_enabled(executor)

        if ticket.department_id <= 0:
            raise DomainOperationError(
                "Cannot register work: Ticket has no department"
            )

        if executor.department_id <= 0:
            raise DomainOperationError(
                f"Cannot register work: "
                f"Admin {executor.employee_id} has no department"
            )

        department = self.uow.departments.get(
            department_id=ticket.department_id,
        )
        if not department.enabled:
            raise DomainOperationError(
                f"Cannot register work: "
                f"Department {department.department_id} is disabled"
            )

        if executor.department_id != ticket.department_id:
            raise DomainOperationError(
                f"Cannot register work: "
                f"Admin {executor.employee_id} belongs to department "
                f"{executor.department_id}, expected "
                f"{ticket.department_id}"
            )

        return executor

    # --------------------------------
    # Execution workflow
    # --------------------------------

    def take_to_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )

            TicketExecutionDomainService.take_to_work(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def pause_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )

            TicketExecutionDomainService.pause_work(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def resume_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )

            TicketExecutionDomainService.resume_work(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def submit_for_review(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )

            TicketExecutionDomainService.submit_for_review(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def record_completed_work_for_review(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self.uow.tickets.get(
                ticket_id=ticket_dto.ticket_id,
            )

            if ticket_dto.actual_started_at is None:
                raise DomainOperationError(
                    "actual_started_at is required"
                )

            if ticket_dto.actual_finished_at is None:
                raise DomainOperationError(
                    "actual_finished_at is required"
                )

            executor = self._get_executor_for_ticket(
                ticket=ticket,
                executor_id=ticket_dto.executor_id,
            )

            TicketExecutionDomainService.record_completed_work_for_review(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                executor_id=executor.employee_id,
                actual_started_at=ticket_dto.actual_started_at,
                actual_finished_at=ticket_dto.actual_finished_at,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)
