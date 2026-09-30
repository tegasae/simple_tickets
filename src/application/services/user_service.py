# src/application/services/user_service.py

from src.application.assemblers.assembler import UserAssembler
from src.application.dto.employee_dto import (
    UserDTO,
    UserResponseDTO,
)
from src.application.helper.actor_helper import EmployeeActorHelper
from src.application.helper.employee_helper import EmployeeHelper

from src.domain.employee import User
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_sync_service import TicketSyncService
from src.domain.services.user_service import UserService
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from src.domain.uow.unit_of_work import UnitOfWork


class UserApplicationService:
    """
    Application service for User.

    Responsibilities:
    - opens UnitOfWork;
    - validates actor and permissions;
    - loads required aggregates;
    - obtains external domain facts from repositories;
    - calls UserService;
    - applies optimistic concurrency guards;
    - persists changed aggregates;
    - converts results to DTO.

    Does not contain:
    - User business rules;
    - cross-aggregate business decisions;
    - SQL;
    - Ticket workflow logic;
    - User disable cascade rules.

    RBAC role operations remain delegated to RoleManager.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

        self.helper = EmployeeHelper(self.uow)
        self.actor = EmployeeActorHelper(self.uow)

        self.role_manager = (
            self.helper.get_role_manager_user()
        )

        self.ticket_sync_service = TicketSyncService()

        self.user_service = UserService(
            ticket_sync_service=self.ticket_sync_service,
        )

    # ==================================================================
    # Helpers
    # ==================================================================

    def _save_and_to_dto(
        self,
        user: User,
    ) -> UserResponseDTO:
        saved_user = self.uow.users.save(
            user
        )

        return UserAssembler.to_dto(
            saved_user
        )

    def _get_related_tickets(
        self,
        *,
        user_id: int,
    ) -> list[Ticket]:
        """
        Load all Tickets related to User.

        User may be referenced as:
        - Ticket.user_id;
        - Ticket.contact_user_id.

        The same Ticket may occur in both collections.
        UserService performs deduplication.
        """

        owned_tickets = self.uow.tickets.get_by_user_id(
            user_id=user_id,
        )

        contact_tickets = (
            self.uow.tickets.get_by_contact_user_id(
                contact_user_id=user_id,
            )
        )

        return owned_tickets + contact_tickets

    def _load_linked_ticket_users(
        self,
        *,
        tickets: list[Ticket],
    ) -> dict[int, TicketUser]:
        """
        Load TicketUser aggregates linked to supplied Tickets.

        Mapping:

            TicketUser.user_ticket_id -> TicketUser

        Application layer does not decide which TicketUser
        aggregates must actually change.
        """

        result: dict[int, TicketUser] = {}

        for ticket in tickets:
            if ticket.user_ticket_id == 0:
                continue

            if ticket.user_ticket_id in result:
                continue

            ticket_user = self.uow.user_tickets.get(
                ticket_id=ticket.user_ticket_id,
            )

            result[ticket_user.ticket_user_id] = ticket_user

        return result

    def _has_ticket_references(
        self,
        *,
        user_id: int,
    ) -> bool:
        """
        Return True when User is referenced by at least one Ticket
        either as User or as contact User.
        """

        if self.uow.tickets.get_by_user_id(
            user_id=user_id,
        ):
            return True

        return bool(
            self.uow.tickets.get_by_contact_user_id(
                contact_user_id=user_id,
            )
        )

    # ==================================================================
    # Create
    # ==================================================================

    def create_user(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            self.helper.ensure_login_is_free(
                login=user_dto.login,
            )

            client = self.uow.clients.get(
                client_id=user_dto.client_id,
            )

            user = self.user_service.create(
                client=client,
                employee_id=0,
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
                email=user_dto.email,
                phone=user_dto.phone,
                enabled=user_dto.enable,
                login=user_dto.login,
                password=user_dto.password,
                enabled_account=user_dto.enable_account,
            )

            if user_dto.roles:
                # User must receive a real employee_id before
                # roles can be assigned.
                user = self.uow.users.save(
                    user
                )

                self.role_manager.grant_roles(
                    actor=actor,
                    target=user,
                    role_ids=frozenset(
                        user_dto.roles
                    ),
                    required_permission=(
                        AdminPermission.USER_OPERATION
                    ),
                )

            # UserService.create() relied on Client.enabled.
            self.uow.clients.touch(
                client
            )

            return self._save_and_to_dto(
                user
            )

    # ==================================================================
    # Update
    # ==================================================================

    def update_user(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            user = self.uow.users.get(
                user_id=user_dto.employee_id,
            )

            client = self.uow.clients.get(
                client_id=user.client_id,
            )

            self.user_service.update(
                user=user,
                client=client,
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
                email=user_dto.email,
                phone=user_dto.phone,
            )

            # UserService.update() relied on Client.enabled.
            self.uow.clients.touch(
                client
            )

            return self._save_and_to_dto(
                user
            )

    # ==================================================================
    # Account
    # ==================================================================

    def attach_account(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            self.helper.ensure_login_is_free(
                login=user_dto.login,
            )

            user = self.uow.users.get(
                user_id=user_dto.employee_id,
            )

            client = self.uow.clients.get(
                client_id=user.client_id,
            )

            self.user_service.attach_account(
                user=user,
                client=client,
                login=user_dto.login,
                password=user_dto.password,
                enabled_account=user_dto.enable_account,
            )

            self.uow.clients.touch(
                client
            )

            return self._save_and_to_dto(
                user
            )

    def detach_account(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            user = self.uow.users.get(
                user_id=user_dto.employee_id,
            )

            client = self.uow.clients.get(
                client_id=user.client_id,
            )

            self.user_service.detach_account(
                user=user,
                client=client,
            )

            self.uow.clients.touch(
                client
            )

            return self._save_and_to_dto(
                user
            )

    def change_password(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            if not user_dto.password:
                raise DomainOperationError(
                    "Password is required"
                )

            user = self.uow.users.get(
                user_id=user_dto.employee_id,
            )

            client = self.uow.clients.get(
                client_id=user.client_id,
            )

            self.user_service.change_password(
                user=user,
                client=client,
                password=user_dto.password,
            )

            self.uow.clients.touch(
                client
            )

            return self._save_and_to_dto(
                user
            )

    # ==================================================================
    # Roles
    # ==================================================================

    def grant_role(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            user = self.uow.users.get(
                user_id=user_dto.employee_id,
            )

            client = self.uow.clients.get(
                client_id=user.client_id,
            )

            # Granting roles is handled by RBAC, but this operation
            # still depends on User/Client domain state.
            self.user_service.ensure_can_grant_roles(
                user=user,
                client=client,
            )

            self.role_manager.grant_roles(
                actor=actor,
                target=user,
                role_ids=frozenset(
                    user_dto.roles
                ),
                required_permission=(
                    AdminPermission.USER_OPERATION
                ),
            )

            self.uow.clients.touch(
                client
            )

            return self._save_and_to_dto(
                user
            )

    def revoke_role(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            user = self.uow.users.get(
                user_id=user_dto.employee_id,
            )

            # Revoking role is intentionally allowed without
            # requiring Client.enabled.
            self.role_manager.revoke_roles(
                actor=actor,
                target=user,
                role_ids=frozenset(
                    user_dto.roles
                ),
                required_permission=(
                    AdminPermission.USER_OPERATION
                ),
            )

            return self._save_and_to_dto(
                user
            )

    # ==================================================================
    # Enable / disable
    # ==================================================================

    def enable(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        """
        Enable User.

        Client must be enabled.

        Ticket and TicketUser statuses are not changed automatically.
        """

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            user = self.uow.users.get(
                user_id=user_dto.employee_id,
            )

            client = self.uow.clients.get(
                client_id=user.client_id,
            )

            self.user_service.enable(
                user=user,
                client=client,
            )

            # UserService.enable() relied on Client.enabled.
            self.uow.clients.touch(
                client
            )

            return self._save_and_to_dto(
                user
            )

    def disable(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        """
        Disable User and apply related Ticket / TicketUser rules.

        Application layer:
        - loads User;
        - loads related Tickets;
        - loads linked TicketUser aggregates;
        - calls UserService;
        - persists changed aggregates.

        All cascade rules belong to UserService.
        """

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            user = self.uow.users.get(
                user_id=user_dto.employee_id,
            )

            tickets = self._get_related_tickets(
                user_id=user.employee_id,
            )

            ticket_users = self._load_linked_ticket_users(
                tickets=tickets,
            )

            result = self.user_service.disable(
                user=user,
                tickets=tickets,
                ticket_users=ticket_users,
                actor_employee_id=actor.employee_id,
            )

            for ticket in result.tickets:
                self.uow.tickets.save(
                    ticket
                )

            for ticket_user in result.ticket_users:
                self.uow.user_tickets.save(
                    ticket_user
                )

            return self._save_and_to_dto(
                user
            )

    # ==================================================================
    # Delete
    # ==================================================================

    def delete(
        self,
        *,
        user_dto: UserDTO,
    ) -> None:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_OPERATION,
            )

            user = self.uow.users.get(
                user_id=user_dto.employee_id,
            )

            self.user_service.ensure_can_delete(
                user=user,
                has_ticket_user_references=(
                    self.uow.user_tickets.has_user_reference(
                        user_id=user.employee_id,
                    )
                ),
                has_ticket_references=(
                    self._has_ticket_references(
                        user_id=user.employee_id,
                    )
                ),
            )

            self.uow.users.delete(
                user.employee_id,
            )

    # ==================================================================
    # Queries
    # ==================================================================

    def find_by_login(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_VIEW,
            )

            if not user_dto.login:
                raise DomainOperationError(
                    "Login is required"
                )

            user = self.uow.users.find_by_login(
                login=user_dto.login,
            )

            return UserAssembler.to_dto(
                user
            )

    def get_by_id(
        self,
        *,
        user_dto: UserDTO,
    ) -> UserResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_VIEW,
            )

            user = self.uow.users.get(
                user_id=user_dto.employee_id,
            )

            return UserAssembler.to_dto(
                user
            )

    def get_all(
        self,
        *,
        user_dto: UserDTO,
    ) -> list[UserResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_VIEW,
            )

            return [
                UserAssembler.to_dto(user)
                for user in self.uow.users.get_all()
            ]

    def get_by_client_id(
        self,
        *,
        user_dto: UserDTO,
    ) -> list[UserResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=user_dto.actor_admin_id,
                permission=AdminPermission.USER_VIEW,
            )

            return [
                UserAssembler.to_dto(user)
                for user
                in self.uow.users.get_all_by_client_id(
                    client_id=user_dto.client_id,
                )
            ]