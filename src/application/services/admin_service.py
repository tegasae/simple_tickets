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
                admin.account=self._create_account(admin_dto.login, admin_dto.password)

            admin=self.uow.admins.save(admin)
            if admin_dto.roles:
                self._add_roles(actor, admin, admin_dto.roles)
                admin = self.uow.admins.save(admin)


            return  AdminAssembler.to_dto(self.uow.admins.save(admin))

    def _add_roles(self,actor_admin:Admin,admin:Admin,roles:frozenset[int])->Admin:
        rbac = self._rbac()
        for role in roles:
            rbac.grant_role(
                actor_admin,
                admin,
                role,
                required_permission=AdminPermission.ASSIGN_ROLE,
            )
        return admin
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

    def _create_account(self,login:str,password:str) -> Account:
        if self.uow.admins.exist_login(login):
            raise DomainOperationError(f"Login {login} already exists")
        return Account.create(
            account_id=0,
            login=login,
            plain_password=password,
        )


    def attach_account(
        self,
        *,
        admin_dto: AdminDTO
    ) -> AdminResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(admin_id=admin_dto.actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)
            admin = self.uow.admins.get(admin_dto.admin_id)
            if isinstance(admin.account, NoAccount):
                account=self._create_account(admin_dto.login, admin_dto.password)
                admin.account = account
            return AdminAssembler.to_dto(self.uow.admins.save(admin))

    def detach_account(self, *, admin_dto:AdminDTO) -> AdminResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(admin_id=admin_dto.actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)
            admin = self.uow.admins.get(admin_id=admin_dto.admin_id)
            admin.account = NoAccount()
            return AdminAssembler.to_dto(self.uow.admins.save(admin))

    def change_password(self, *, admin_dto:AdminDTO) -> bool:
        with self.uow:
            actor = self.uow.admins.get(admin_id=admin_dto.actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)
            admin = self.uow.admins.get(admin_dto.admin_id)
            if isinstance(admin.account,Account):
                admin.account.change_password(plain_password=admin_dto.password)
                self.uow.admins.save(admin)
                return True
            return False

    # --------------------------------
    # Role operations (IMPORTANT)
    # --------------------------------

    def grant_role(
        self,
        *,
        admin_dto: AdminDTO
    ) -> AdminResponseDTO:

        with self.uow:

            actor = self.uow.admins.get(admin_id=admin_dto.actor_admin_id)
            target = self.uow.admins.get(admin_id=admin_dto.admin_id)
            if admin_dto.roles:
                self._add_roles(actor, target, admin_dto.roles)

            return AdminAssembler.to_dto(self.uow.admins.save(target))

    def revoke_role(
        self,
        *,
        admin_dto: AdminDTO
    ) -> AdminResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(admin_id=admin_dto.actor_admin_id)
            target = self.uow.admins.get(admin_id=admin_dto.admin_id)
            rbac = self._rbac()
            if admin_dto.roles:
                for role in admin_dto.roles:
                    rbac.revoke_role(
                        actor,
                        target,
                        role,
                        required_permission=AdminPermission.REVOKE_ROLE,
                    )

            return AdminAssembler.to_dto(self.uow.admins.save(target))


    # --------------------------------
    # Enable / disable
    # --------------------------------

    def disable(self, *, actor_admin_id: int, admin_id: int) -> AdminResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)
            admin = self.uow.admins.get(admin_id)
            admin.disable()

            if not isinstance(admin.account, NoAccount):
                admin.account.disable()

            return AdminAssembler.to_dto(self.uow.admins.save(admin))

    def enable(self, *, actor_admin_id: int, admin_id: int) -> AdminResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)
            admin = self.uow.admins.get(admin_id)
            admin.enable()

            return AdminAssembler.to_dto(self.uow.admins.save(admin))

    def delete(self, *, admin_dto: AdminDTO) -> None:
        with self.uow:
            actor = self.uow.admins.get(admin_id=admin_dto.admin_id)
            self._require(actor, AdminPermission.UPDATE_ADMIN)
            admin = self.uow.admins.get(admin_id=admin_dto.admin_id)

            clients=self.uow.clients.get_all()
            for client in clients:
                if client.created_by_admin_id==admin.employee_id:
                    raise Exception("You can't delete this admin because it has clients")

            tickets=self.uow.tickets.get_all()
            for ticket in tickets:
                if ticket.belong(employee_id=admin.employee_id):
                    raise Exception("You can't delete this admin because it has tickets")

            user_tickets = self.uow.user_tickets.get_all()
            for user_ticket in user_tickets:
                if user_ticket.belong(employee_id=admin.employee_id):
                    raise Exception("You can't delete this admin because it has user tickets")
            self.uow.admins.delete(admin_id=admin.employee_id)







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