# src/application/services/department_service.py
from src.application.assemblers.assembler import DepartmentAssembler
from src.application.dto.department_dto import DepartmentDTO, DepartmentResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.department import Department
from src.domain.exceptions import DomainOperationError
from src.domain.policy.department import DepartmentPolicy
from src.domain.rbac.permissions import AdminPermission
from src.domain.uow.unit_of_work import UnitOfWork


class DepartmentApplicationService:
    """
    Application services for Department use cases.

    Department rules:
    - Only Admin with required permission can manage departments.
    - Disabled department cannot be assigned to Admin/Ticket later.
    - Department cannot be deleted if Admins or Tickets still reference it.
    """

    def __init__(self, uow:UnitOfWork):
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

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

            department = Department.create(
                department_id=department_dto.department_id,
                name=department_dto.name,
                enabled=department_dto.enabled,
            )

            saved_department = self.uow.departments.save(department)

            return DepartmentAssembler.to_dto(saved_department)

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

            department.rename(department_dto.name)

            saved_department = self.uow.departments.save(department)

            return DepartmentAssembler.to_dto(saved_department)

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

            department.enable()

            saved_department = self.uow.departments.save(department)

            return DepartmentAssembler.to_dto(saved_department)

    def disable_department(
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
            admins = self.uow.admins.get_all_by_department_id(
                department_id=department.department_id,
            )
            DepartmentPolicy.ensure_can_disable(
                department=department,
                admins=admins,
            )
            saved_department = self.uow.departments.save(department)

            return DepartmentAssembler.to_dto(saved_department)

    def delete_department(
        self,
        *,
        department_dto: DepartmentDTO,
    ) -> None:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=department_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            department = self.uow.departments.get(
                department_id=department_dto.department_id,
            )

            if self.uow.admins.has_department_reference(department.department_id):
                raise DomainOperationError(
                    "You can't delete this department because it has admins"
                )

            if self.uow.tickets.has_department_reference(department.department_id):
                raise DomainOperationError(
                    "You can't delete this department because it has tickets"
                )

            self.uow.departments.delete(
                department_id=department.department_id,
            )

    def get_by_id(
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

            return DepartmentAssembler.to_dto(department)

    def get_all(
        self,
        *,
        department_dto: DepartmentDTO,
    ) -> list[DepartmentResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=department_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            departments = self.uow.departments.get_all()

            return [
                DepartmentAssembler.to_dto(department)
                for department in departments
            ]