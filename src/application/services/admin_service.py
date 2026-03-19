# src/application/services/admin_application_service.py
from src.application.assemblers.assembler import AdminAssembler
from src.application.dto.admin_dto import CreateAdminDTO, AdminResponseDTO
from src.domain.employee import Admin
from src.domain.account import Account, NoAccount
from src.domain.exceptions import DomainOperationError
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

    # --------------------------------
    # Create
    # --------------------------------

    def create_admin(
        self,
        *,
        create_admin_dto:CreateAdminDTO

    ) -> AdminResponseDTO:

        with self.uow:

            actor = self.uow.admins.get(create_admin_dto.actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)

            admin = Admin.create(
                employee_id=0,
                job_title=create_admin_dto.job_title,
                first_name=create_admin_dto.first_name,
                last_name=create_admin_dto.last_name,
                email=create_admin_dto.email,
                phone=create_admin_dto.phone,
            )

            if create_admin_dto.login and create_admin_dto.password:

                if self.uow.admins.exist_login(create_admin_dto.login):
                    raise DomainOperationError(f"Login {create_admin_dto.login} already exists")

                admin.account = Account.create(
                    account_id=0,
                    login=create_admin_dto.login,
                    plain_password=create_admin_dto.password,
                )

            return  AdminAssembler.to_dto(self.uow.admins.save(admin))

    # --------------------------------
    # Update
    # --------------------------------

    def update_admin(
        self,
        *,
        actor_admin_id: int,
        admin_id: int,
        job_title: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> Admin:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)

            self._require(actor, AdminPermission.UPDATE_ADMIN)

            admin = self.uow.admins.get(admin_id)

            admin.update(
                job_title,
                first_name,
                last_name,
                email,
                phone,
            )

            return self.uow.admins.save(admin)

    # --------------------------------
    # Account management
    # --------------------------------

    def attach_account(
        self,
        *,
        actor_admin_id: int,
        admin_id: int,
        login: str,
        password: str,
    ) -> Admin:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)

            self._require(actor, AdminPermission.UPDATE_ADMIN)

            if self.uow.admins.exist_login(login):
                raise DomainOperationError(f"Login {login} already exists")

            admin = self.uow.admins.get(admin_id)

            admin.account = Account.create(
                account_id=0,
                login=login,
                plain_password=password,
            )

            return self.uow.admins.save(admin)

    def detach_account(self, *, actor_admin_id: int, admin_id: int) -> Admin:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)

            self._require(actor, AdminPermission.UPDATE_ADMIN)

            admin = self.uow.admins.get(admin_id)

            admin.account = NoAccount()

            return self.uow.admins.save(admin)

    # --------------------------------
    # Role operations (IMPORTANT)
    # --------------------------------

    def grant_role(
        self,
        *,
        actor_admin_id: int,
        target_admin_id: int,
        role_id: int,
    ) -> Admin:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)
            target = self.uow.admins.get(target_admin_id)

            rbac = self._rbac()

            rbac.grant_role(
                actor,
                target,
                role_id,
                required_permission=AdminPermission.ASSIGN_ROLE,
            )

            return self.uow.admins.save(target)

    def revoke_role(
        self,
        *,
        actor_admin_id: int,
        target_admin_id: int,
        role_id: int,
    ) -> Admin:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)
            target = self.uow.admins.get(target_admin_id)

            rbac = self._rbac()

            rbac.revoke_role(
                actor,
                target,
                role_id,
                required_permission=AdminPermission.REVOKE_ROLE,
            )

            return self.uow.admins.save(target)

    # --------------------------------
    # Enable / disable
    # --------------------------------

    def disable_admin(self, *, actor_admin_id: int, admin_id: int) -> Admin:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)

            self._require(actor, AdminPermission.UPDATE_ADMIN)

            admin = self.uow.admins.get(admin_id)

            admin.disable()

            if not isinstance(admin.account, NoAccount):
                admin.account.disable()

            return self.uow.admins.save(admin)

    def enable_admin(self, *, actor_admin_id: int, admin_id: int) -> Admin:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)

            self._require(actor, AdminPermission.UPDATE_ADMIN)

            admin = self.uow.admins.get(admin_id)

            admin.enable()

            return self.uow.admins.save(admin)

    # --------------------------------
    # Queries
    # --------------------------------

    def get_by_id(self, *, actor_admin_id: int, admin_id: int) -> Admin:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)

            self._require(actor, AdminPermission.VIEW_ADMIN)

            return self.uow.admins.get(admin_id)

    def get_all(self, *, actor_admin_id: int) -> list[Admin]:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)

            self._require(actor, AdminPermission.VIEW_ADMIN)

            return self.uow.admins.get_all()