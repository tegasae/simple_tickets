# src/application/services/user_service.py
from src.application.assemblers.assembler import UserAssembler
from src.application.dto.user_dto import UserDTO, UserResponseDTO
from src.domain.account import Account, NoAccount
from src.domain.employee import User, Admin
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role import Authorizer, RoleManager
from src.services.uow.uow import UnitOfWork


class UserApplicationService:
    """
    Application service for User.

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

    def create_user(
            self,
            *,
            user_dto: UserDTO

    ) -> UserResponseDTO:

        with self.uow:

            actor = self.uow.admins.get(user_dto.actor_admin_id)
            self._require(actor, AdminPermission.CREATE_USER)

            user = User.create(
                employee_id=0,
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
                email=user_dto.email,
                phone=user_dto.phone,
                client_id=user_dto.client_id
            )

            if user_dto.login and user_dto.password:
                user.account = self._create_account(user_dto.login, user_dto.password)

            user = self.uow.users.save(user)
            #if user_dto.roles:
                #self._add_roles(actor, user, user_dto.roles)

                #for r in user_dto.roles:
                #    self.uow.roles_user.get(r)
                #    user.grant_role(role_id=r)


            return UserAssembler.to_dto(self.uow.users.save(user))

    def _add_roles(self, actor_admin: Admin, user: User, roles: frozenset[int]) -> User:
        rbac = self._rbac()
        for role in roles:
            rbac.grant_role(
                actor_admin,
                user,
                role,
                required_permission=AdminPermission.ASSIGN_ROLE,
            )
        return user

    def _create_account(self,login:str,password:str) -> Account:
        if self.uow.users.exist_login(login):
            raise DomainOperationError(f"Login {login} already exists")
        return Account.create(
            account_id=0,
            login=login,
            plain_password=password,
        )


    def update_user(
        self,
        *,
        user_dto: UserDTO
    ) -> UserResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(user_dto.actor_admin_id)
            self._require(actor, AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_dto.user_id)

            user.update(
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
                email=user_dto.email,
                phone=user_dto.phone
            )

            #return self.uow.admins.save(admin)
            return UserAssembler.to_dto(self.uow.users.save(user))

    def attach_account(
            self,
            *,
            user_dto: UserDTO
    ) -> UserResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(admin_id=user_dto.actor_admin_id)
            self._require(actor, AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_dto.user_id)
            if isinstance(user.account, NoAccount):
                account = self._create_account(user_dto.login, user_dto.password)
                user.account = account
            return UserAssembler.to_dto(self.uow.users.save(user))

    def detach_account(self, *, user_dto: UserDTO) -> UserResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(admin_id=user_dto.actor_admin_id)
            self._require(actor, AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_id=user_dto.user_id)
            user.account = NoAccount()
            return UserAssembler.to_dto(self.uow.users.save(user))

    def change_password(self, *, user_dto: UserDTO) -> bool:
        with self.uow:
            actor = self.uow.admins.get(admin_id=user_dto.actor_admin_id)
            self._require(actor, AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_dto.user_id)
            if isinstance(user.account, Account):
                user.account.change_password(plain_password=user_dto.password)
                self.uow.users.save(user)
                return True
            return False

    def grant_role(
        self,
        *,
        user_dto: UserDTO
    ) -> UserResponseDTO:

        with self.uow:

            actor = self.uow.admins.get(admin_id=user_dto.actor_admin_id)
            user = self.uow.users.get(user_id=user_dto.user_id)
            if user_dto.roles:
                self._add_roles(actor, user, user_dto.roles)

            return UserAssembler.to_dto(self.uow.users.save(user))

    def revoke_role(
        self,
        *,
        user_dto: UserDTO
    ) -> UserResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(admin_id=user_dto.actor_admin_id)
            user = self.uow.users.get(user_id=user_dto.user_id)
            rbac = self._rbac()
            if user_dto.roles:
                for role in user_dto.roles:
                    rbac.revoke_role(
                        actor,
                        user,
                        role,
                        required_permission=AdminPermission.REVOKE_ROLE,
                    )

            return UserAssembler.to_dto(self.uow.users.save(user))



    def disable(self, *, actor_admin_id: int, user_id: int) -> UserResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_id)
            user.disable()

            if not isinstance(user.account, NoAccount):
                user.account.disable()

            return UserAssembler.to_dto(self.uow.users.save(user))

    def enable(self, *, actor_admin_id: int, user_id: int) -> UserResponseDTO:

        with self.uow:
            actor = self.uow.admins.get(actor_admin_id)
            self._require(actor, AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_id)
            user.enable()

            return UserAssembler.to_dto(self.uow.users.save(user))

    def delete(self, *, user_dto: UserDTO) -> None:
        with self.uow:
            admin = self.uow.admins.get(admin_id=user_dto.actor_admin_id)
            self._require(admin, AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_id=user_dto.user_id)


            user_tickets=self.uow.user_tickets.get_all()
            for user_ticket in user_tickets:
                if user_ticket.belong(employee_id=user.employee_id):
                    raise Exception("You can't delete this admin because it has tickets")


            self.uow.users.delete(user_id=user.employee_id)

    def find_by_login(self,login:str)->UserResponseDTO:
        with self.uow:
            user=self.uow.users.find_by_login(login=login)
            return UserAssembler.to_dto(user)

    def get_by_id(self, *, actor_admin_id: int, user_id: int) -> UserResponseDTO:

        with self.uow:
            admin = self.uow.admins.get(admin_id=actor_admin_id)
            self._require(admin, AdminPermission.CREATE_USER)
            return UserAssembler.to_dto(self.uow.users.get(user_id))

    def get_all(self, *, admin_id: int) -> list[UserResponseDTO]:

        with self.uow:
            actor = self.uow.admins.get(admin_id=admin_id)
            self._require(actor, AdminPermission.CREATE_USER)

            return [UserAssembler.to_dto(admin) for admin in self.uow.users.get_all()]
