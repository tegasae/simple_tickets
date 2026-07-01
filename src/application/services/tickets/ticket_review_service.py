

from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import TicketDTO, TicketResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.policy.ticket import TicketPolicy
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_review_service import (
    TicketReviewService as TicketReviewDomainService,
)
from src.domain.ticket import Ticket
from src.domain.uow.unit_of_work import UnitOfWork


class TicketReviewApplicationService:
    """
    Application service for Ticket review actions.

    Domain workflow rules belong to TicketReviewService.

    This class is responsible for:
        - UnitOfWork;
        - RBAC;
        - loading Ticket and referenced executor;
        - cross-aggregate checks for a new executor assignment;
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
    # Review workflow
    # --------------------------------

    def confirm_execution(
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

            TicketReviewDomainService.confirm_execution(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def return_to_work(
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

            TicketReviewDomainService.return_to_work(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def return_to_assigned(
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
            executor = self._get_assignable_executor(
                ticket=ticket,
                executor_id=ticket_dto.executor_id,
            )

            TicketReviewDomainService.return_to_assigned(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                executor_id=executor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def return_to_scheduled(
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

            if ticket_dto.planned_start_at is None:
                raise DomainOperationError(
                    "planned_start_at is required"
                )

            TicketReviewDomainService.return_to_scheduled(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                planned_start_at=ticket_dto.planned_start_at,
                planned_finish_at=ticket_dto.planned_finish_at,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def return_to_ready_to_work(
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

            if ticket_dto.planned_start_at is None:
                raise DomainOperationError(
                    "planned_start_at is required"
                )

            executor = self._get_assignable_executor(
                ticket=ticket,
                executor_id=ticket_dto.executor_id,
            )

            TicketReviewDomainService.return_to_ready_to_work(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                executor_id=executor.employee_id,
                planned_start_at=ticket_dto.planned_start_at,
                planned_finish_at=ticket_dto.planned_finish_at,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def return_to_deferred(
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

            TicketReviewDomainService.return_to_deferred(
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)
