# src/application/services/admin_service.py
from src.application.assemblers.assembler import AdminAssembler
from src.application.dto.employee_dto import AdminDTO, AdminResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.application.helper.employee_helper import EmployeeHelper
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.policy.admin import AdminPolicy
from src.domain.rbac.permissions import AdminPermission
from src.services.uow.uow import UnitOfWork

class AdminApplicationService:
    """
    Application service for Admin.

    Uses:
        - UnitOfWork
        - RoleManager (RBAC)
        - Authorizer (permissions)
    """



    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.helper = EmployeeHelper(self.uow)
        self.actor=EmployeeActorHelper(self.uow)
        self.role_manager = self.helper.get_role_manager_admin()

    # --------------------------------
    # Helpers
    # --------------------------------




    def _save_and_to_dto(self, admin: Admin) -> AdminResponseDTO:
        saved_admin = self.uow.admins.save(admin)
        return AdminAssembler.to_dto(saved_admin)



    # --------------------------------
    # Create
    # --------------------------------

    def create_admin(
        self,
        *,
        admin_dto:AdminDTO

    ) -> AdminResponseDTO:

        with self.uow:
            actor=self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id, permission=AdminPermission.ADMIN_OPERATION)

            self.helper.ensure_login_is_free(login=admin_dto.login)

            admin = Admin.create(
                employee_id=0,
                job_title=admin_dto.job_title,
                first_name=admin_dto.first_name,
                last_name=admin_dto.last_name,
                email=admin_dto.email,
                phone=admin_dto.phone,
                login=admin_dto.login,
                password=admin_dto.password,
                enable_account=admin_dto.enable_account)

            if admin_dto.roles:
                admin = self.uow.admins.save(admin)
                self.role_manager.grant_roles(actor=actor, target=admin, role_ids=frozenset(admin_dto.roles),
                                              required_permission=AdminPermission.ROLE_ASSIGN)


            return  self._save_and_to_dto(admin)


    # --------------------------------
    # Update
    # --------------------------------

    def update_admin(
        self,
        *,
        admin_dto: AdminDTO
    ) -> AdminResponseDTO:

        with self.uow:


            self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                                   permission=AdminPermission.ADMIN_OPERATION)
            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)

            admin.update(
                admin_dto.job_title,
                admin_dto.first_name,
                admin_dto.last_name,
                admin_dto.email,
                admin_dto.phone,
            )


            return self._save_and_to_dto(admin)

    # --------------------------------
    # Account management
    # --------------------------------

    def attach_account(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:

            self.helper.ensure_login_is_free(login=admin_dto.login)
            self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ADMIN_OPERATION)


            admin=self.uow.admins.get(admin_id=admin_dto.employee_id)
            admin.add_account(
                login=admin_dto.login,
                password=admin_dto.password,
                enabled_account=admin_dto.enable_account,
            )

            return self._save_and_to_dto(admin)

    def detach_account(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ADMIN_OPERATION)
            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)
            admin.remove_account()

            return self._save_and_to_dto(admin)



    def change_password(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:
            if not admin_dto.password:
                raise DomainOperationError("Password is required")

            self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ADMIN_OPERATION)
            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)
            admin.change_password(password=admin_dto.password)

            return self._save_and_to_dto(admin)

    # --------------------------------
    # Role operations (IMPORTANT)
    # --------------------------------


    def grant_role(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:
            actor=self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ROLE_ASSIGN)
            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)


            self.role_manager.grant_roles(actor=actor, target=admin, role_ids=frozenset(admin_dto.roles),
                                          required_permission=AdminPermission.ROLE_ASSIGN)


            return self._save_and_to_dto(admin)

    def revoke_role(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:
            actor=self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ROLE_REVOKE)
            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)
            self.role_manager.revoke_roles(actor=actor, target=admin, role_ids=frozenset(admin_dto.roles),
                                           required_permission=AdminPermission.ROLE_REVOKE)

            return self._save_and_to_dto(admin)



    # --------------------------------
    # Enable / disable
    # --------------------------------

    def disable(self, *, admin_dto:AdminDTO) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ADMIN_OPERATION)
            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)
            admin.disable()

            return self._save_and_to_dto(admin)

    def enable(self, *, admin_dto:AdminDTO) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ADMIN_OPERATION)
            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)
            admin.enable()

            return self._save_and_to_dto(admin)

    def change_department(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)
            if admin_dto.department_id:
                department = self.uow.departments.get(
                    department_id=admin_dto.department_id,
                )
                # todo нельзя поменять department, если admin назначен исполнителем. Потом ставить значение has_at_work_ticket
                AdminPolicy.ensure_can_change_department(admin=admin, department=department,has_at_work_tickets=False)



            return self._save_and_to_dto(admin)


    def remove_department(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ADMIN_OPERATION,
            )

            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)
            admin.remove_department()

            return self._save_and_to_dto(admin)


    def delete(self, *, admin_dto: AdminDTO) -> None:
        with self.uow:

            self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ADMIN_OPERATION)
            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)


            if self.uow.clients.has_created_by_admin(admin_id=admin_dto.employee_id):
                    raise DomainOperationError("You can't delete this admin because it has clients")

            if self.uow.tickets.has_admin_reference(admin.employee_id):
                raise DomainOperationError(
                    "You can't delete this admin because it has tickets"
                )

            if self.uow.user_tickets.has_admin_reference(admin.employee_id):
                raise DomainOperationError(
                    "You can't delete this admin because it has user tickets"
                )

            self.uow.admins.delete(admin_id=admin.employee_id)





    # --------------------------------
    # Queries
    # --------------------------------
    def find_by_login(self,admin_dto:AdminDTO)->AdminResponseDTO:
        with self.uow:
            if not admin_dto.login:
                raise DomainOperationError("Login is required")
            self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ADMIN_VIEW)


            admin=self.uow.admins.find_by_login(login=admin_dto.login)
            return AdminAssembler.to_dto(admin)



    def get_by_id(self, *, admin_dto:AdminDTO) -> AdminResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ADMIN_VIEW)
            admin = self.uow.admins.get(admin_id=admin_dto.employee_id)
            return AdminAssembler.to_dto(admin)

    def get_all(self, *, admin_dto:AdminDTO) -> list[AdminResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(actor_admin_id=admin_dto.actor_admin_id,
                                           permission=AdminPermission.ADMIN_VIEW)

            return [AdminAssembler.to_dto(admin) for admin in self.uow.admins.get_all()]



