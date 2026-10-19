from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role import Authorizer
from src.domain.uow.unit_of_work import UnitOfWork


class EmployeeActorHelper:
    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

        self._admins: dict[int, Admin] = {}
        self._users: dict[int, User] = {}

    # ==============================================================
    # Admin
    # ==============================================================

    def require_actor_admin(
        self,
        *,
        actor_admin_id: int,
        permission: AdminPermission,
    ) -> Admin:
        actor = self._get_admin(
            actor_admin_id=actor_admin_id,
        )

        Authorizer(
            self.uow.roles_admin
        ).require(
            actor,
            permission,
        )

        return actor

    def require_actor_admin_any(
        self,
        *,
        actor_admin_id: int,
        permissions: tuple[AdminPermission, ...],
    ) -> Admin:
        if not permissions:
            raise ValueError(
                "permissions must not be empty"
            )

        actor = self._get_admin(
            actor_admin_id=actor_admin_id,
        )

        authorizer = Authorizer(
            self.uow.roles_admin
        )

        last_error: PermissionError | None = None

        for permission in permissions:
            try:
                authorizer.require(
                    actor,
                    permission,
                )

                return actor

            except PermissionError as error:
                last_error = error

        assert last_error is not None
        raise last_error

    def require_actor_admin_all(
        self,
        *,
        actor_admin_id: int,
        permissions: tuple[AdminPermission, ...],
    ) -> Admin:
        if not permissions:
            raise ValueError(
                "permissions must not be empty"
            )

        actor = self._get_admin(
            actor_admin_id=actor_admin_id,
        )

        authorizer = Authorizer(
            self.uow.roles_admin
        )

        for permission in permissions:
            authorizer.require(
                actor,
                permission,
            )

        return actor

    def has_admin_permission(
        self,
        *,
        actor_admin_id: int,
        permission: AdminPermission,
    ) -> bool:
        actor = self._get_admin(
            actor_admin_id=actor_admin_id,
        )

        try:
            Authorizer(
                self.uow.roles_admin
            ).require(
                actor,
                permission,
            )

        except PermissionError:
            return False

        return True

    # ==============================================================
    # User
    # ==============================================================

    def require_actor_user(
        self,
        *,
        actor_user_id: int,
        permission: UserPermission,
    ) -> User:
        actor = self._get_user(
            actor_user_id=actor_user_id,
        )

        Authorizer(
            self.uow.roles_user
        ).require(
            actor,
            permission,
        )

        return actor

    def require_actor_user_any(
        self,
        *,
        actor_user_id: int,
        permissions: tuple[UserPermission, ...],
    ) -> User:
        if not permissions:
            raise ValueError(
                "permissions must not be empty"
            )

        actor = self._get_user(
            actor_user_id=actor_user_id,
        )

        authorizer = Authorizer(
            self.uow.roles_user
        )

        last_error: PermissionError | None = None

        for permission in permissions:
            try:
                authorizer.require(
                    actor,
                    permission,
                )

                return actor

            except PermissionError as error:
                last_error = error

        assert last_error is not None
        raise last_error

    def require_actor_user_all(
        self,
        *,
        actor_user_id: int,
        permissions: tuple[UserPermission, ...],
    ) -> User:
        if not permissions:
            raise ValueError(
                "permissions must not be empty"
            )

        actor = self._get_user(
            actor_user_id=actor_user_id,
        )

        authorizer = Authorizer(
            self.uow.roles_user
        )

        for permission in permissions:
            authorizer.require(
                actor,
                permission,
            )

        return actor

    def has_user_permission(
        self,
        *,
        actor_user_id: int,
        permission: UserPermission,
    ) -> bool:
        actor = self._get_user(
            actor_user_id=actor_user_id,
        )

        try:
            Authorizer(
                self.uow.roles_user
            ).require(
                actor,
                permission,
            )

        except PermissionError:
            return False

        return True

    # ==============================================================
    # Cache
    # ==============================================================

    def _get_admin(
        self,
        *,
        actor_admin_id: int,
    ) -> Admin:
        actor = self._admins.get(
            actor_admin_id
        )

        if actor is None:
            actor = self.uow.admins.get(
                admin_id=actor_admin_id,
            )

            self._admins[actor_admin_id] = actor

        actor.can_do_operation()

        return actor

    def _get_user(
        self,
        *,
        actor_user_id: int,
    ) -> User:
        actor = self._users.get(
            actor_user_id
        )

        if actor is None:
            actor = self.uow.users.get(
                user_id=actor_user_id,
            )

            self._users[actor_user_id] = actor

        actor.can_do_operation()

        return actor

    def clear(self) -> None:
        self._admins.clear()
        self._users.clear()