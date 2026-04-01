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

    Responsibilities:
        - open UnitOfWork
        - load actor and target entities
        - check permissions
        - orchestrate domain operations
        - persist changes
        - convert domain entities to DTOs
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # --------------------------------
    # Helpers
    # --------------------------------

    def _rbac(self) -> RoleManager:
        roles_repo = self.uow.roles_user
        authorizer = Authorizer(self.uow.roles_admin)
        return RoleManager(authorizer, roles_repo)

    def _require(self, actor: Admin, permission: AdminPermission) -> None:
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

    def _get_user(self, *, user_id: int) -> User:
        return self.uow.users.get(user_id=user_id)

    def _save_and_to_dto(self, user: User) -> UserResponseDTO:
        saved_user = self.uow.users.save(user)
        return UserAssembler.to_dto(saved_user)

    def _ensure_login_is_free(self, login: str | None) -> None:
        if login and self.uow.users.exist_login(login):
            raise DomainOperationError(f"Login {login} already exists")

    def _add_roles(
        self,
        *,
        actor_admin: Admin,
        user: User,
        roles: frozenset[int],
    ) -> None:
        rbac = self._rbac()
        for role_id in roles:
            rbac.grant_role(
                actor_admin,
                user,
                role_id,
                required_permission=AdminPermission.ASSIGN_ROLE,
            )

    # --------------------------------
    # Commands
    # --------------------------------

    def create_user(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:
            actor = self._require_actor(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            self._ensure_login_is_free(user_dto.login)

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
                enabled_account=user_dto.enabled_account,
            )

            user = self.uow.users.save(user)

            if user_dto.roles:
                self._add_roles(
                    actor_admin=actor,
                    user=user,
                    roles=user_dto.roles,
                )

            return self._save_and_to_dto(user)

    def update_user(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            user = self._get_user(user_id=user_dto.user_id)

            user.update(
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
                email=user_dto.email,
                phone=user_dto.phone,
            )

            return self._save_and_to_dto(user)

    def attach_account(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            if not user_dto.login:
                raise DomainOperationError("Login is required")

            if not user_dto.password:
                raise DomainOperationError("Password is required")

            self._ensure_login_is_free(user_dto.login)

            user = self._get_user(user_id=user_dto.user_id)
            user.add_account(
                login=user_dto.login,
                password=user_dto.password,
                enabled_account=user_dto.enabled_account,
            )

            return self._save_and_to_dto(user)

    def detach_account(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            user = self._get_user(user_id=user_dto.user_id)
            user.remove_account()

            return self._save_and_to_dto(user)

    def change_password(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            if not user_dto.password:
                raise DomainOperationError("Password is required")

            user = self._get_user(user_id=user_dto.user_id)
            user.change_password(password=user_dto.password)

            return self._save_and_to_dto(user)

    def grant_role(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:
            actor = self._require_actor(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.ASSIGN_ROLE,
            )

            user = self._get_user(user_id=user_dto.user_id)

            if user_dto.roles:
                self._add_roles(
                    actor_admin=actor,
                    user=user,
                    roles=user_dto.roles,
                )

            return self._save_and_to_dto(user)

    def revoke_role(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:
            actor = self._require_actor(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.REVOKE_ROLE,
            )

            user = self._get_user(user_id=user_dto.user_id)
            rbac = self._rbac()

            if user_dto.roles:
                for role_id in user_dto.roles:
                    rbac.revoke_role(
                        actor,
                        user,
                        role_id,
                        required_permission=AdminPermission.REVOKE_ROLE,
                    )

            return self._save_and_to_dto(user)

    def disable(self, *, actor_admin_id: int, user_id: int) -> UserResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            user = self._get_user(user_id=user_id)
            user.disable()

            return self._save_and_to_dto(user)

    def enable(self, *, actor_admin_id: int, user_id: int) -> UserResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            user = self._get_user(user_id=user_id)
            user.enable()

            return self._save_and_to_dto(user)

    def delete(self, *, user_dto: UserDTO) -> None:
        with self.uow:
            self._require_actor(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            user = self._get_user(user_id=user_dto.user_id)

            user_tickets = self.uow.user_tickets.get_all()
            for user_ticket in user_tickets:
                if user_ticket.belong(employee_id=user.employee_id):
                    raise DomainOperationError(
                        "You can't delete this user because it has tickets"
                    )

            self.uow.users.delete(user_id=user.employee_id)

    # --------------------------------
    # Queries
    # --------------------------------

    def find_by_login(self, *, login: str) -> UserResponseDTO:
        with self.uow:
            user = self.uow.users.find_by_login(login=login)
            return UserAssembler.to_dto(user)

    def get_by_id(self, *, actor_admin_id: int, user_id: int) -> UserResponseDTO:
        with self.uow:
            self._require_actor(
                actor_admin_id=actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            user = self._get_user(user_id=user_id)
            return UserAssembler.to_dto(user)

    def get_all(self, *, actor_admin_id: int) -> list[UserResponseDTO]:
        with self.uow:
            self._require_actor(
                actor_admin_id=actor_admin_id,
                permission=AdminPermission.CREATE_USER,
            )

            return [
                UserAssembler.to_dto(user)
                for user in self.uow.users.get_all()
            ]