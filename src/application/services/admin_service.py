# src/application/services/admin_service.py

from src.application.assemblers.assembler import (
    AdminAssembler,
    PermissionAssembler,
)
from src.application.dto.employee_dto import (
    AdminDTO,
    AdminResponseDTO,
    PermissionsResponseDTO,
)
from src.application.helper.actor_helper import EmployeeActorHelper
from src.application.helper.employee_helper import EmployeeHelper

from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.admin_service import AdminService
from src.domain.uow.unit_of_work import UnitOfWork


class AdminApplicationService:
    """
    Application service for Admin.

    Responsibilities:
    - opens UnitOfWork;
    - validates actor and permissions;
    - loads required aggregates;
    - obtains external domain facts from repositories;
    - calls AdminService;
    - applies optimistic concurrency guards;
    - persists changes;
    - converts results to DTO.

    Does not contain:
    - Admin business rules;
    - cross-aggregate business decisions;
    - SQL;
    - Ticket workflow logic;
    - persistence logic.

    RBAC role operations remain delegated to RoleManager.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

        self.helper = EmployeeHelper(self.uow)
        self.actor = EmployeeActorHelper(self.uow)

        self.role_manager = self.helper.get_role_manager_admin()


    # ==================================================================
    # Helpers
    # ==================================================================

    def _save_and_to_dto(
        self,
        admin: Admin,
    ) -> AdminResponseDTO:
        saved_admin = self.uow.admins.save(
            admin
        )

        return AdminAssembler.to_dto(
            saved_admin
        )

    def _has_current_executor_tickets(
        self,
        *,
        admin_id: int,
    ) -> bool:
        """
        Return True when Admin is the current executor
        of at least one Ticket.

        Application layer obtains the fact.
        AdminService interprets it.
        """

        return bool(
            self.uow.tickets.get_by_current_executor(
                executor_id=admin_id,
            )
        )

    # ==================================================================
    # Create
    # ==================================================================

    def create_admin(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            self.helper.ensure_login_is_free(
                login=admin_dto.login,
            )

            if admin_dto.department_id <= 0:
                raise DomainOperationError(
                    "Department id must be positive"
                )

            department = self.uow.departments.get(
                department_id=admin_dto.department_id,
            )

            admin = AdminService.create(
                department=department,
                employee_id=0,
                job_title=admin_dto.job_title,
                first_name=admin_dto.first_name,
                last_name=admin_dto.last_name,
                email=admin_dto.email,
                phone=admin_dto.phone,
                login=admin_dto.login,
                password=admin_dto.password,
                enable_account=admin_dto.enable_account,
            )

            if admin_dto.roles:
                # Admin must receive a real employee_id
                # before roles can be assigned.
                admin = self.uow.admins.save(
                    admin
                )

                self.role_manager.grant_roles(
                    actor=actor,
                    target=admin,
                    role_ids=frozenset(
                        admin_dto.roles
                    ),
                    required_permission=(
                        AdminPermission.ROLE_ASSIGN
                    ),
                )

            # AdminService.create() relied on Department.enabled.
            self.uow.departments.touch(
                department
            )

            return self._save_and_to_dto(
                admin
            )

    # ==================================================================
    # Update
    # ==================================================================

    def update_admin(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            if admin_dto.department_id < 0:
                raise DomainOperationError(
                    "Department id must be positive"
                )

            department_changed = (
                admin.department_id
                != admin_dto.department_id
            )

            if admin_dto.department_id:
                department = self.uow.departments.get(
                    department_id=admin_dto.department_id,
                )
            else:
                department=None

            has_current_executor_tickets = False

            if department_changed:
                has_current_executor_tickets = (
                    self._has_current_executor_tickets(
                        admin_id=admin.employee_id,
                    )
                )

            AdminService.update(
                admin=admin,
                department=department,
                has_current_executor_tickets=(
                    has_current_executor_tickets
                ),
                job_title=admin_dto.job_title,
                first_name=admin_dto.first_name,
                last_name=admin_dto.last_name,
                email=admin_dto.email,
                phone=admin_dto.phone,
            )

            if department_changed and department:
                # AdminService.update() relied on
                # target Department.enabled.
                self.uow.departments.touch(
                    department
                )

            return self._save_and_to_dto(
                admin
            )

    # ==================================================================
    # Account management
    # ==================================================================

    def attach_account(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            self.helper.ensure_login_is_free(
                login=admin_dto.login,
            )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            AdminService.attach_account(
                admin=admin,
                login=admin_dto.login,
                password=admin_dto.password,
                enabled_account=admin_dto.enable_account,
            )

            return self._save_and_to_dto(
                admin
            )

    def detach_account(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            AdminService.detach_account(
                admin=admin,
            )

            return self._save_and_to_dto(
                admin
            )

    def change_password(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            if not admin_dto.password:
                raise DomainOperationError(
                    "Password is required"
                )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            AdminService.change_password(
                admin=admin,
                password=admin_dto.password,
            )

            return self._save_and_to_dto(
                admin
            )

    # ==================================================================
    # Role operations
    # ==================================================================

    def grant_role(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ROLE_ASSIGN,
            )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            self.role_manager.grant_roles(
                actor=actor,
                target=admin,
                role_ids=frozenset(
                    admin_dto.roles
                ),
                required_permission=(
                    AdminPermission.ROLE_ASSIGN
                ),
            )

            return self._save_and_to_dto(
                admin
            )

    def revoke_role(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ROLE_ASSIGN,
            )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            self.role_manager.revoke_roles(
                actor=actor,
                target=admin,
                role_ids=frozenset(
                    admin_dto.roles
                ),
                required_permission=(
                    AdminPermission.ROLE_ASSIGN
                ),
            )

            return self._save_and_to_dto(
                admin
            )

    def get_permissions(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> PermissionsResponseDTO:
        with self.uow:
            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            permissions = (
                self.role_manager.auth.permissions_of(
                    subject=admin,
                )
            )

            return PermissionAssembler.to_admin_dto(
                permissions=frozenset(
                    permissions
                ),
            )

    # ==================================================================
    # Enable / disable
    # ==================================================================

    def enable(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            AdminService.enable(
                admin=admin,
            )

            return self._save_and_to_dto(
                admin
            )

    def disable(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            AdminService.disable(
                admin=admin,
                has_current_executor_tickets=(
                    self._has_current_executor_tickets(
                        admin_id=admin.employee_id,
                    )
                ),
            )

            return self._save_and_to_dto(
                admin
            )

    # ==================================================================
    # Department
    # ==================================================================

    def change_department(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        """
        Move Admin to another Department.

        Application layer:
        - loads Admin and Department;
        - obtains current-executor fact;
        - applies optimistic concurrency guard.

        AdminService:
        - validates business rules;
        - changes Admin.
        """

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            if admin_dto.department_id <= 0:
                raise DomainOperationError(
                    "Department id must be positive"
                )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            department = self.uow.departments.get(
                department_id=admin_dto.department_id,
            )

            AdminService.change_department(
                admin=admin,
                department=department,
                has_current_executor_tickets=(
                    self._has_current_executor_tickets(
                        admin_id=admin.employee_id,
                    )
                ),
            )

            # Operation relied on Department.enabled.
            self.uow.departments.touch(
                department
            )

            return self._save_and_to_dto(
                admin
            )

    def remove_department(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        """
        Remove Admin from Department.

        Admin cannot lose Department while being
        current executor of a Ticket.
        """

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            AdminService.remove_department(
                admin=admin,
                has_current_executor_tickets=(
                    self._has_current_executor_tickets(
                        admin_id=admin.employee_id,
                    )
                ),
            )

            return self._save_and_to_dto(
                admin
            )

    # ==================================================================
    # Delete
    # ==================================================================

    def delete(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> None:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            AdminService.ensure_can_delete(
                admin=admin,
                has_clients=(
                    self.uow.clients.has_created_by_admin(
                        admin_id=admin.employee_id,
                    )
                ),
                has_ticket_references=(
                    self.uow.tickets.has_admin_reference(
                        admin.employee_id,
                    )
                ),
                has_ticket_user_references=(
                    self.uow.user_tickets.has_admin_reference(
                        admin.employee_id,
                    )
                ),
            )

            self.uow.admins.delete(
                admin_id=admin.employee_id,
            )

    # ==================================================================
    # Queries
    # ==================================================================

    def find_by_login(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_VIEW,
            )

            if not admin_dto.login:
                raise DomainOperationError(
                    "Login is required"
                )

            admin = self.uow.admins.find_by_login(
                login=admin_dto.login,
            )

            return AdminAssembler.to_dto(
                admin
            )

    def get_by_id(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_VIEW,
            )

            admin = self.uow.admins.get(
                admin_id=admin_dto.employee_id,
            )

            return AdminAssembler.to_dto(
                admin
            )

    def get_all(
        self,
        *,
        admin_dto: AdminDTO,
    ) -> list[AdminResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_VIEW,
            )

            return [
                AdminAssembler.to_dto(admin)
                for admin in self.uow.admins.get_all()
            ]