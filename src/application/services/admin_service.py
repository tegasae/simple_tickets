# src/application/services/admin_service.py
from src.application.assemblers.assembler import AdminAssembler
from src.application.dto.employee_dto import AdminDTO, AdminResponseDTO
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.employee_protocol import HasRoleIds
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role import Authorizer, RoleManager
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

    # --------------------------------
    # Helpers
    # --------------------------------

    def _rbac(self):
        roles_repo = self.uow.roles_admin
        authorizer = Authorizer(roles_repo)
        return RoleManager(authorizer, roles_repo)

    def _require(self, actor, permission):
        Authorizer(self.uow.roles_admin).require(actor, permission)


    def _require_actor(
        self,
        *,
        actor_admin_id: int,
        permission: AdminPermission,
    ) -> Admin:
        actor = self.uow.admins.get(admin_id=actor_admin_id)
        self._require(actor, permission)
        return actor


    def _ensure_login_is_free(self, login: str | None) -> None:
        if login and self.uow.admins.exist_login(login):
            raise DomainOperationError(f"Login {login} already exists")


    def _add_roles(
        self,
        *,
        actor: HasRoleIds,
        employee: HasRoleIds,
        roles: frozenset[int],
    ) -> None:
        rbac = self._rbac()
        for role_id in roles:
            rbac.grant_role(
                actor,
                employee,
                role_id,
                required_permission=AdminPermission.ASSIGN_ROLE,
            )

    def _get_admin(self, *, admin_id: int) -> Admin:
        return self.uow.admins.get(admin_id=admin_id)

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


            actor = self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.UPDATE_ADMIN
            )
            self._ensure_login_is_free(admin_dto.login)

            admin = Admin.create(
                employee_id=0,
                job_title=admin_dto.job_title,
                first_name=admin_dto.first_name,
                last_name=admin_dto.last_name,
                email=admin_dto.email,
                phone=admin_dto.phone,
                login=admin_dto.login,
                password=admin_dto.password,
                enabled_account=admin_dto.enable_account)

            admin=self.uow.admins.save(admin)
            if admin_dto.roles:
                self._add_roles(actor=actor, employee=admin, roles=admin_dto.roles)
                admin = self.uow.admins.save(admin)

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
            self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.UPDATE_ADMIN,
            )
            admin=self._get_admin(admin_id=admin_dto.employee_id)
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
            self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.UPDATE_ADMIN,
            )

            if not admin_dto.login:
                raise DomainOperationError("Login is required")

            if not admin_dto.password:
                raise DomainOperationError("Password is required")

            self._ensure_login_is_free(admin_dto.login)

            admin = self._get_admin(admin_id=admin_dto.employee_id)
            admin.add_account(
                login=admin_dto.login,
                password=admin_dto.password,
                enabled_account=admin_dto.enable_account,
            )

            return self._save_and_to_dto(admin)

    def detach_account(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.UPDATE_ADMIN,
            )

            admin = self._get_admin(admin_id=admin_dto.employee_id)
            admin.remove_account()

            return self._save_and_to_dto(admin)



    def change_password(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.UPDATE_ADMIN,
            )

            if not admin_dto.password:
                raise DomainOperationError("Password is required")

            admin = self._get_admin(admin_id=admin_dto.employee_id)
            admin.change_password(password=admin_dto.password)

            return self._save_and_to_dto(admin)

    # --------------------------------
    # Role operations (IMPORTANT)
    # --------------------------------


    def grant_role(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:
            actor = self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.ASSIGN_ROLE,
            )

            admin = self._get_admin(admin_id=admin_dto.employee_id)

            if admin_dto.roles:
                self._add_roles(
                    actor=actor,
                    employee=admin,
                    roles=admin_dto.roles,
                )

            return self._save_and_to_dto(admin)

    def revoke_role(self, *, admin_dto: AdminDTO) -> AdminResponseDTO:
        with self.uow:
            actor = self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.REVOKE_ROLE,
            )

            admin = self._get_admin(admin_id=admin_dto.employee_id)
            rbac = self._rbac()

            if admin_dto.roles:
                for role_id in admin_dto.roles:
                    rbac.revoke_role(
                        actor,
                        admin,
                        role_id,
                        required_permission=AdminPermission.REVOKE_ROLE,
                    )
            return self._save_and_to_dto(admin)



    # --------------------------------
    # Enable / disable
    # --------------------------------

    def disable(self, *, admin_dto:AdminDTO) -> AdminResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.UPDATE_ADMIN,
            )

            admin = self._get_admin(admin_id=admin_dto.employee_id)
            admin.disable()

            return self._save_and_to_dto(admin)

    def enable(self, *, admin_dto:AdminDTO) -> AdminResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.UPDATE_ADMIN,
            )

            admin = self._get_admin(admin_id=admin_dto.employee_id)
            admin.enable()

            return self._save_and_to_dto(admin)

    def delete(self, *, admin_dto: AdminDTO) -> None:
        with self.uow:
            self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.UPDATE_ADMIN,
            )
            admin = self._get_admin(admin_id=admin_dto.employee_id)

            clients=self.uow.clients.get_all()
            for client in clients:
                if client.created_by_admin_id==admin.employee_id:
                    raise DomainOperationError("You can't delete this admin because it has clients")

            tickets=self.uow.tickets.get_all()
            for ticket in tickets:
                if ticket.belong(employee_id=admin.employee_id):
                    raise DomainOperationError("You can't delete this admin because it has tickets")

            user_tickets = self.uow.user_tickets.get_all()
            for user_ticket in user_tickets:
                if user_ticket.belong(employee_id=admin.employee_id):
                    raise DomainOperationError("You can't delete this admin because it has user tickets")
            self.uow.admins.delete(admin_id=admin.employee_id)







    # --------------------------------
    # Queries
    # --------------------------------
    def find_by_login(self,admin_dto:AdminDTO)->AdminResponseDTO:
        with self.uow:
            if not admin_dto.login:
                raise DomainOperationError("Login is required")
            self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.VIEW_ADMIN,
            )
            admin=self.uow.admins.find_by_login(login=admin_dto.login)
            return AdminAssembler.to_dto(admin)

    def get_by_id(self, *, admin_dto:AdminDTO) -> AdminResponseDTO:

        with self.uow:
            self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.VIEW_ADMIN,
            )
            return AdminAssembler.to_dto(self.uow.admins.get(admin_id=admin_dto.employee_id))

    def get_all(self, *, admin_dto:AdminDTO) -> list[AdminResponseDTO]:

        with self.uow:
            self._require_actor(
                actor_admin_id=admin_dto.actor_admin_id,
                permission=AdminPermission.VIEW_ADMIN,
            )
            return [AdminAssembler.to_dto(admin) for admin in self.uow.admins.get_all()]


