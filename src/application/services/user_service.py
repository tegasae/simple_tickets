# src/application/services/user_service.py

from src.application.assemblers.assembler import UserAssembler
from src.application.dto.employee_dto import UserDTO, UserResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.application.helper.employee_helper import EmployeeHelper
from src.domain.employee import User
from src.domain.exceptions import DomainOperationError
from src.domain.policies.ticket import TicketPolicy
from src.domain.rbac.permissions import AdminPermission
from src.domain.uow.unit_of_work import UnitOfWork


class UserApplicationService:
    """
    Application services for User.

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



        self.helper = EmployeeHelper(self.uow)
        self.actor = EmployeeActorHelper(self.uow)

        self.role_manager=self.helper.get_role_manager_user()

    # --------------------------------
    # Helpers
    # --------------------------------



    def _save_and_to_dto(self, user: User) -> UserResponseDTO:
        saved_user = self.uow.users.save(user)
        return UserAssembler.to_dto(saved_user)





    # --------------------------------
    # Commands
    # --------------------------------

    def create_user(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            self.helper.ensure_login_is_free(login=user_dto.login)
            client=self.uow.clients.get(client_id=user_dto.client_id)
            TicketPolicy.ensure_client_enabled(client)
            user = User.create(
                employee_id=0,
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
                email=user_dto.email,
                phone=user_dto.phone,
                client_id=user_dto.client_id,
                login=user_dto.login,
                password=user_dto.password,
                enabled=user_dto.enable,
                enabled_account=user_dto.enable_account,
            )

            if user_dto.roles:
                user = self.uow.users.save(user)
                self.role_manager.grant_roles(actor=actor, target=user, role_ids=frozenset(user_dto.roles), required_permission=AdminPermission.USER_OPERATION)


            return self._save_and_to_dto(user)

    def update_user(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with (self.uow):

            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )
            user=self.uow.users.get(user_id=user_dto.employee_id)

            client = self.uow.clients.get(client_id=user.client_id)
            TicketPolicy.ensure_client_enabled(client)
            TicketPolicy.ensure_user_enabled(user)
            user.update(
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
                email=user_dto.email,
                phone=user_dto.phone,
            )

            return self._save_and_to_dto(user)

    def attach_account(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:

            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )
            user = self.uow.users.get(user_id=user_dto.employee_id)
            client = self.uow.clients.get(client_id=user.client_id)

            TicketPolicy.ensure_client_enabled(client)
            TicketPolicy.ensure_user_enabled(user)
            self.helper.ensure_login_is_free(login=user_dto.login)
            user.add_account(
                login=user_dto.login,
                password=user_dto.password,
                enabled_account=user_dto.enable_account,
            )

            return self._save_and_to_dto(user)

    def detach_account(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )
            client = self.uow.clients.get(client_id=user_dto.client_id)
            TicketPolicy.ensure_client_enabled(client)
            user = self.uow.users.get(user_id=user_dto.employee_id)
            user.remove_account()

            return self._save_and_to_dto(user)

    def change_password(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:




            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )
            user = self.uow.users.get(user_id=user_dto.employee_id)
            client = self.uow.clients.get(client_id=user.client_id)
            TicketPolicy.ensure_client_enabled(client)
            user.change_password(password=user_dto.password)

            return self._save_and_to_dto(user)

    def grant_role(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:

            actor=self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            user = self.uow.users.get(user_id=user_dto.employee_id)
            client = self.uow.clients.get(client_id=user.client_id)

            TicketPolicy.ensure_client_enabled(client)
            self.role_manager.grant_roles(actor=actor, target=user, role_ids=frozenset(user_dto.roles),
                                          required_permission=AdminPermission.USER_OPERATION)
            return self._save_and_to_dto(user)

    def revoke_role(self, *, user_dto: UserDTO) -> UserResponseDTO:
        with self.uow:

            actor=self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )
            user = self.uow.users.get(user_id=user_dto.employee_id)
            self.role_manager.revoke_roles(actor=actor, target=user, role_ids=frozenset(user_dto.roles), required_permission=AdminPermission.USER_OPERATION)

            return self._save_and_to_dto(user)

    def disable(self, *, user_dto:UserDTO) -> UserResponseDTO:

        # todo но заявки перенести в отлженные

        with self.uow:

            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )
            user = self.uow.users.get(user_id=user_dto.employee_id)
            user.disable()

            return self._save_and_to_dto(user)

    def enable(self, *, user_dto:UserDTO) -> UserResponseDTO:

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )
            user = self.uow.users.get(user_id=user_dto.employee_id)
            client = self.uow.clients.get(client_id=user.client_id)
            TicketPolicy.ensure_client_enabled(client)
            user.enable()

            return self._save_and_to_dto(user)

    def delete(self, *, user_dto: UserDTO) -> None:

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )
            user = self.uow.users.get(user_id=user_dto.employee_id)

            user_tickets = self.uow.user_tickets.get_all()
            # todo проверить участвуебт пользователб в заявках
            for user_ticket in user_tickets:
                if user_ticket.belong(employee_id=user.employee_id):
                    raise DomainOperationError(
                        "You can't delete this user because it has tickets"
                    )

            self.uow.users.delete(user.employee_id)

    # --------------------------------
    # Queries
    # --------------------------------

    def find_by_login(self, *, user_dto:UserDTO) -> UserResponseDTO:
        with self.uow:
            if not user_dto.login:
                raise DomainOperationError("Login is required")
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_VIEW,
            )

            user = self.uow.users.find_by_login(login=user_dto.login)
            return UserAssembler.to_dto(user)

    def get_by_id(self, *, user_dto:UserDTO) -> UserResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_VIEW,
            )
            user = self.uow.users.get(user_id=user_dto.employee_id)
            return UserAssembler.to_dto(user)

    def get_all(self, *, user_dto:UserDTO) -> list[UserResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_VIEW,
            )


            return [
                UserAssembler.to_dto(user)
                for user in self.uow.users.get_all()
            ]

    def get_by_client_id(self,*,user_dto:UserDTO)->list[UserResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_VIEW,
            )
            return [
                UserAssembler.to_dto(user)
                for user in self.uow.users.get_all_by_client_id(client_id=user_dto.client_id)
            ]
