# src/application/services/admin_application_service.py
from src.application.assemblers.assembler import AdminAssembler
from src.application.dto.admin_dto import AdminDTO, AdminResponseDTO
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
        admin_dto:AdminDTO

    ) -> AdminResponseDTO:

        with self.uow:

            actor = self.uow.admins.get(admin_dto.actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)

            admin = Admin.create(
                employee_id=0,
                job_title=admin_dto.job_title,
                first_name=admin_dto.first_name,
                last_name=admin_dto.last_name,
                email=admin_dto.email,
                phone=admin_dto.phone,
            )

            if admin_dto.login and admin_dto.password:

                if self.uow.admins.exist_login(admin_dto.login):
                    raise DomainOperationError(f"Login {admin_dto.login} already exists")

                admin.account = Account.create(
                    account_id=0,
                    login=admin_dto.login,
                    plain_password=admin_dto.password,
                )

            return  AdminAssembler.to_dto(self.uow.admins.save(admin))

    # --------------------------------
    # Update
    # --------------------------------

    def update_admin(
        self,
        *,
        admin_dto: AdminDTO
    ) -> AdminResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(admin_dto.actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)
            admin = self.uow.admins.get(admin_dto.admin_id)

            admin.update(
                admin_dto.job_title,
                admin_dto.first_name,
                admin_dto.last_name,
                admin_dto.email,
                admin_dto.phone,
            )

            #return self.uow.admins.save(admin)
            return AdminAssembler.to_dto(self.uow.admins.save(admin))

    # --------------------------------
    # Account management
    # --------------------------------

    def attach_account(
        self,
        *,
        admin_dto: AdminDTO
    ) -> AdminResponseDTO:

        with self.uow:

            actor = self.uow.admins.get(admin_id=admin_dto.actor_admin_id)

            self._require(actor, AdminPermission.UPDATE_ADMIN)

            if self.uow.admins.exist_login(admin_dto.login):
                raise DomainOperationError(f"Login {admin_dto.login} already exists")

            admin = self.uow.admins.get(admin_dto.admin_id)

            admin.account = Account.create(
                account_id=0,
                login=admin_dto.login,
                plain_password=admin_dto.password,
            )

            return AdminAssembler.to_dto(self.uow.admins.save(admin))

    def detach_account(self, *, admin_dto:AdminDTO) -> AdminResponseDTO:

        with self.uow:

            actor = self.uow.admins.get(admin_id=admin_dto.actor_admin_id)

            self._require(actor, AdminPermission.UPDATE_ADMIN)

            admin = self.uow.admins.get(admin_id=admin_dto.admin_id)

            admin.account = NoAccount()

            return AdminAssembler.to_dto(self.uow.admins.save(admin))

    # --------------------------------
    # Role operations (IMPORTANT)
    # --------------------------------

    def grant_role(
        self,
        *,
        actor_admin_id: int,
        target_admin_id: int,
        role_id: int,
    ) -> AdminResponseDTO:

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

        return AdminAssembler.to_dto(self.uow.admins.save(target))

    def revoke_role(
        self,
        *,
        actor_admin_id: int,
        target_admin_id: int,
        role_id: int,
    ) -> AdminResponseDTO:

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

        return AdminAssembler.to_dto(self.uow.admins.save(target))


    # --------------------------------
    # Enable / disable
    # --------------------------------

    def disable_admin(self, *, actor_admin_id: int, admin_id: int) -> AdminResponseDTO:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)

            self._require(actor, AdminPermission.UPDATE_ADMIN)

            admin = self.uow.admins.get(admin_id)

            admin.disable()

            if not isinstance(admin.account, NoAccount):
                admin.account.disable()

            return AdminAssembler.to_dto(self.uow.admins.save(admin))

    def enable_admin(self, *, actor_admin_id: int, admin_id: int) -> AdminResponseDTO:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)

            self._require(actor, AdminPermission.UPDATE_ADMIN)

            admin = self.uow.admins.get(admin_id)

            admin.enable()

            return AdminAssembler.to_dto(self.uow.admins.save(admin))

    # --------------------------------
    # Queries
    # --------------------------------
    def find_by_login(self,login:str)->AdminResponseDTO:
        with self.uow:
            admin=self.uow.admins.find_by_login(login=login)
            return AdminAssembler.to_dto(admin)

    def get_by_id(self, *, actor_admin_id: int, admin_id: int) -> AdminResponseDTO:

        with self.uow:

            actor = self.uow.admins.get(actor_admin_id)

            self._require(actor, AdminPermission.VIEW_ADMIN)


            return AdminAssembler.to_dto(self.uow.admins.get(admin_id))

    def get_all(self, *, actor_admin_id: int) -> list[AdminResponseDTO]:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.VIEW_ADMIN)

            return [AdminAssembler.to_dto(admin) for admin in self.uow.admins.get_all()]