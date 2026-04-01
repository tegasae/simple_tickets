# src/application/services/user_service.py
from src.application.assemblers.assembler import UserAssembler
from src.application.dto.user_dto import UserDTO, UserResponseDTO
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
        roles_repo = self.uow.roles_user
        authorizer = Authorizer(self.uow.roles_admin)
        return RoleManager(authorizer, roles_repo)

    def _require_actor(self, actor_admin_id: int, permission: AdminPermission) -> Admin:
        actor = self.uow.admins.get(admin_id=actor_admin_id)
        Authorizer(self.uow.roles_admin).require(actor, permission)
        return actor

    def create_user(
            self,
            *,
            user_dto: UserDTO

    ) -> UserResponseDTO:

        with self.uow:
            actor=self._require_actor(actor_admin_id=user_dto.actor_admin_id,permission=AdminPermission.CREATE_USER)
            if user_dto.login and self.uow.users.exist_login(user_dto.login):
                    raise DomainOperationError(f"Login {user_dto.login} already exists")

            user = User.create(
                employee_id=0,
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
                email=user_dto.email,
                phone=user_dto.phone,
                client_id=user_dto.client_id,
                roles=user_dto.roles,
                login=user_dto.login,
                password=user_dto.password,
                enabled=user_dto.enabled,
                enabled_account=user_dto.enabled_account
            )

            user = self.uow.users.save(user)
            self._add_roles(actor, user, user.role_ids())

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



    def update_user(
        self,
        *,
        user_dto: UserDTO
    ) -> UserResponseDTO:

        with self.uow:
            self._require_actor(actor_admin_id=user_dto.actor_admin_id,permission=AdminPermission.CREATE_USER)
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
            self._require_actor(actor_admin_id=user_dto.actor_admin_id,permission=AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_dto.user_id)
            user.add_account(login=user_dto.login, password=user_dto.password,enabled_account=user_dto.enabled_account)
            return UserAssembler.to_dto(self.uow.users.save(user))

    def detach_account(self, *, user_dto: UserDTO) -> UserResponseDTO:

        with self.uow:
            self._require_actor(actor_admin_id=user_dto.actor_admin_id,permission=AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_id=user_dto.user_id)
            user.remove_account()
            return UserAssembler.to_dto(self.uow.users.save(user))

    def change_password(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            if not user_dto.password:
                raise DomainOperationError("Password is required")

            user = self.uow.users.get(user_dto.user_id)
            user.change_password(password=user_dto.password)
            user = self.uow.users.save(user)

            return UserAssembler.to_dto(user)

    def grant_role(
        self,
        *,
        user_dto: UserDTO
    ) -> UserResponseDTO:

        with self.uow:
            self._require_actor(actor_admin_id=user_dto.actor_admin_id,permission=AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_id=user_dto.user_id)
            user.change_password(password=user_dto.password)
            return UserAssembler.to_dto(self.uow.users.save(user))

    def revoke_role(
        self,
        *,
        user_dto: UserDTO
    ) -> UserResponseDTO:

        with self.uow:
            actor=self._require_actor(actor_admin_id=user_dto.actor_admin_id,permission=AdminPermission.CREATE_USER)
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



    def disable(self, *, user_dto:UserDTO) -> UserResponseDTO:

        with self.uow:
            self._require_actor(actor_admin_id=user_dto.actor_admin_id,permission=AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_dto.user_id)
            user.disable()

            return UserAssembler.to_dto(self.uow.users.save(user))

    def enable(self, *, user_dto:UserDTO) -> UserResponseDTO:

        with self.uow:
            self._require_actor(actor_admin_id=user_dto.actor_admin_id,permission=AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_dto.user_id)
            user.enable()

            return UserAssembler.to_dto(self.uow.users.save(user))

    def delete(self, *, user_dto: UserDTO) -> None:
        with self.uow:
            self._require_actor(actor_admin_id=user_dto.actor_admin_id, permission=AdminPermission.CREATE_USER)
            user = self.uow.users.get(user_id=user_dto.user_id)


            user_tickets=self.uow.user_tickets.get_all()
            for user_ticket in user_tickets:
                if user_ticket.belong(employee_id=user.employee_id):
                    raise Exception("You can't delete this admin because it has tickets")


            self.uow.users.delete(user_id=user.employee_id)

    def find_by_login(self,user_dto:UserDTO)->UserResponseDTO:
        with self.uow:
            user=self.uow.users.find_by_login(login=user_dto.login)
            return UserAssembler.to_dto(user)

    def get_by_id(self, *, user_dto:UserDTO) -> UserResponseDTO:

        with self.uow:
            self._require_actor(actor_admin_id=user_dto.actor_admin_id, permission=AdminPermission.CREATE_USER)
            return UserAssembler.to_dto(self.uow.users.get(user_id=user_dto.user_id))

    def get_all(self, *, user_dto:UserDTO) -> list[UserResponseDTO]:

        with self.uow:
            self._require_actor(actor_admin_id=user_dto.actor_admin_id, permission=AdminPermission.CREATE_USER)
            return [UserAssembler.to_dto(admin) for admin in self.uow.users.get_all()]
