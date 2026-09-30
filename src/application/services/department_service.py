# src/application/services/department_service.py

from __future__ import annotations

from src.application.assemblers.assembler import DepartmentAssembler
from src.application.dto.department_dto import (
    DepartmentDTO,
    DepartmentResponseDTO,
)
from src.application.helper.actor_helper import EmployeeActorHelper

from src.domain.department import Department
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.department_service import DepartmentService
from src.domain.uow.unit_of_work import UnitOfWork


class DepartmentApplicationService:
    """
    Application service for Department.

    Responsibilities:
    - RBAC / permissions;
    - UnitOfWork and transaction;
    - aggregate loading;
    - collection of cross-aggregate facts;
    - optimistic concurrency;
    - calling DepartmentService;
    - persistence;
    - DTO assembly.

    Does not contain:
    - Department business rules;
    - SQL;
    - repository business logic.

    DepartmentService is responsible for Department domain operations
    and cross-aggregate business decisions based on facts supplied
    by the application layer.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

        self.actor = EmployeeActorHelper(
            self.uow
        )

        self.department_service = DepartmentService()

    # ==================================================================
    # Commands
    # ==================================================================

    def create_department(
        self,
        *,
        department_dto: DepartmentDTO,
    ) -> DepartmentResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=department_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            department = self.department_service.create(
                department_id=0,
                name=department_dto.name,
                enabled=True,
            )

            return self._save_and_to_dto(
                department=department,
            )

    def update_department(
        self,
        *,
        department_dto: DepartmentDTO,
    ) -> DepartmentResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=department_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            department = self.uow.departments.get(
                department_id=department_dto.department_id,
            )

            self.department_service.rename(
                department=department,
                name=department_dto.name,
            )

            return self._save_and_to_dto(
                department=department,
            )

    def enable_department(
        self,
        *,
        department_dto: DepartmentDTO,
    ) -> DepartmentResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=department_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            department = self.uow.departments.get(
                department_id=department_dto.department_id,
            )

            self.department_service.enable(
                department=department,
            )

            return self._save_and_to_dto(
                department=department,
            )

    def disable_department(
        self,
        *,
        department_dto: DepartmentDTO,
    ) -> DepartmentResponseDTO:
        """
        Department cannot be disabled while it has:

        - enabled Admins;
        - open Tickets.

        Application layer collects these facts.

        DepartmentService decides whether disabling is allowed.
        """

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=department_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            department = self.uow.departments.get(
                department_id=department_dto.department_id,
            )

            admins = self.uow.admins.get_all_by_department_id(
                department_id=department.department_id,
            )

            tickets = self.uow.tickets.get_by_department_id(
                department.department_id,
            )

            self.department_service.disable(
                department=department,
                has_enabled_admins=any(
                    admin.enabled
                    for admin in admins
                ),
                has_open_tickets=any(
                    not ticket.is_closed
                    for ticket in tickets
                ),
            )

            # Admins and Tickets participate in the business decision
            # only as read-only aggregates.
            for admin in admins:
                self.uow.admins.touch(
                    admin
                )

            for ticket in tickets:
                self.uow.tickets.touch(
                    ticket
                )

            return self._save_and_to_dto(
                department=department,
            )

    def delete_department(
        self,
        *,
        department_dto: DepartmentDTO,
    ) -> None:
        """
        Department cannot be deleted while any Admin or Ticket
        references it.

        Unlike disable(), references matter regardless of their
        enabled / closed state.
        """

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=department_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            department = self.uow.departments.get(
                department_id=department_dto.department_id,
            )

            admins = self.uow.admins.get_all_by_department_id(
                department_id=department.department_id,
            )

            tickets = self.uow.tickets.get_by_department_id(
                department.department_id,
            )

            self.department_service.ensure_can_delete(
                department=department,
                has_admin_references=bool(admins),
                has_ticket_references=bool(tickets),
            )

            self.uow.departments.delete(
                department_id=department.department_id,
            )

            self.uow.commit()

    # ==================================================================
    # Queries
    # ==================================================================

    def get_by_id(
        self,
        *,
        department_dto: DepartmentDTO,
    ) -> DepartmentResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=department_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_VIEW,
            )

            department = self.uow.departments.get(
                department_id=department_dto.department_id,
            )

            return DepartmentAssembler.to_dto(
                department
            )

    def get_all(
        self,
        *,
        department_dto: DepartmentDTO,
    ) -> list[DepartmentResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=department_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_VIEW,
            )

            departments = self.uow.departments.get_all()

            return [
                DepartmentAssembler.to_dto(
                    department
                )
                for department in departments
            ]

    # ==================================================================
    # Persistence
    # ==================================================================

    def _save_and_to_dto(
        self,
        *,
        department: Department,
    ) -> DepartmentResponseDTO:
        saved_department = self.uow.departments.save(
            department
        )

        self.uow.commit()

        if saved_department is None:
            saved_department = department

        return DepartmentAssembler.to_dto(
            saved_department
        )