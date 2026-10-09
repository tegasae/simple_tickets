# src/application/role_service.py



from typing import Generic, TypeVar, cast

from src.application.assemblers.assembler import RoleAssembler
from src.application.dto.roles_dto import RoleDTO, RoleResponseDTO
from src.application.exceptions import ApplicationValidateError
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.rbac.permissions import (
    AdminPermission,
    PermissionBase,
    UserPermission,
)
from src.domain.rbac.role_new import Role
from src.domain.rbac.role_repository import RoleRepository
from src.domain.services.role_service import RoleAdminService, RoleUserService
from src.domain.uow.unit_of_work import UnitOfWork


T = TypeVar("T", bound=PermissionBase)


class RoleApplicationService(Generic[T]):
    """
    Generic role service.

    Works with one permission family at a time:
        AdminPermission
        UserPermission

    Usually used through:
        AdminRoleService
        UserRoleService
    """

    def __init__(
        self,
        uow: UnitOfWork,
        permission_type: type[T],
    ):
        self.uow = uow
        self.permission_type = permission_type
        self.actor = EmployeeActorHelper(self.uow)

        if self.permission_type is AdminPermission:
            self.permission_operation = AdminPermission.ROLE_ASSIGN
            self.repository = cast(RoleRepository[T], self.uow.roles_admin)
            self._service=RoleAdminService()

        elif self.permission_type is UserPermission:
            self.permission_operation = AdminPermission.ROLE_USER_ASSIGN
            self.repository = cast(RoleRepository[T], self.uow.roles_user)
            self._service = RoleUserService()
        else:
            raise ApplicationValidateError(
                f"Unknown permission type: {self.permission_type}"
            )

    def create_role(
        self,
        *,
        role_dto: RoleDTO,
    ) -> RoleResponseDTO:




        with self.uow:
            self._check_actor(
                actor_admin_id=role_dto.actor_admin_id,
            )
            role=self._service.create_role(name=role_dto.name,
                                           permissions=role_dto.permissions,
                                           description=role_dto.description,
                                           is_system_role=role_dto.is_system_role)


            return self._save_and_to_dto(
                role=role,
            )

    def delete_role(
        self,
        *,
        role_dto: RoleDTO,
    ) -> None:


        with self.uow:
            self._check_actor(
                actor_admin_id=role_dto.actor_admin_id,
            )

            role = self.repository.get(role_dto.role_id)

            if role.is_system_role:
                raise ApplicationValidateError(
                    f"Cannot delete system role: {role.name}"
                )

            if self.repository.is_assigned(role_id=role_dto.role_id):
                raise ApplicationValidateError(
                    f"Role '{role.name}' cannot be deleted because it is assigned"
                )

            self.repository.delete(role_dto.role_id)

    def get_role(
        self,
        *,
        role_dto: RoleDTO,
    ) -> RoleResponseDTO:


        with self.uow:
            self._check_actor(
                actor_admin_id=role_dto.actor_admin_id,
            )

            role = self.repository.get(role_dto.role_id)

            return RoleAssembler.to_dto(role)

    def get_all_roles(
        self,
        *,
        role_dto: RoleDTO,
    ) -> list[RoleResponseDTO]:
        with self.uow:
            self._check_actor(
                actor_admin_id=role_dto.actor_admin_id,
            )

            return [
                RoleAssembler.to_dto(role)
                for role in self.repository.all()
            ]

    def _save_and_to_dto(
        self,
        *,
        role: Role[T],
    ) -> RoleResponseDTO:
        saved_role = self.repository.save(role)

        return RoleAssembler.to_dto(saved_role)

    def _check_actor(
        self,
        *,
        actor_admin_id: int,
    ) -> None:
        self.actor.require_actor_admin(
            actor_admin_id=actor_admin_id,
            permission=self.permission_operation,
        )




class AdminRoleApplicationService:
    """
    Application service for admin roles.

    Admin roles contain AdminPermission values.
    """

    def __init__(self, uow: UnitOfWork):
        self._application_service = RoleApplicationService[AdminPermission](
            uow=uow,
            permission_type=AdminPermission,
        )

    def create_role(
        self,
        *,
        role_dto: RoleDTO,
    ) -> RoleResponseDTO:
        return self._application_service.create_role(
            role_dto=role_dto,
        )

    def delete_role(
        self,
        *,
        role_dto: RoleDTO,
    ) -> None:
        self._application_service.delete_role(
            role_dto=role_dto,
        )

    def get_role(
        self,
        *,
        role_dto: RoleDTO,
    ) -> RoleResponseDTO:
        return self._application_service.get_role(
            role_dto=role_dto,
        )

    def get_all_roles(
        self,
        *,
        role_dto: RoleDTO,
    ) -> list[RoleResponseDTO]:
        return self._application_service.get_all_roles(
            role_dto=role_dto,
        )


class UserRoleApplicationService:
    """
    Application service for user roles.

    User roles contain UserPermission values,
    but they are managed by Admin.
    """

    def __init__(self, uow: UnitOfWork):
        self._application_service = RoleApplicationService[UserPermission](
            uow=uow,
            permission_type=UserPermission,
        )

    def create_role(
        self,
        *,
        role_dto: RoleDTO,
    ) -> RoleResponseDTO:
        return self._application_service.create_role(
            role_dto=role_dto,
        )

    def delete_role(
        self,
        *,
        role_dto: RoleDTO,
    ) -> None:
        self._application_service.delete_role(
            role_dto=role_dto,
        )

    def get_role(
        self,
        *,
        role_dto: RoleDTO,
    ) -> RoleResponseDTO:
        return self._application_service.get_role(
            role_dto=role_dto,
        )

    def get_all_roles(
        self,
        *,
        role_dto: RoleDTO,
    ) -> list[RoleResponseDTO]:
        return self._application_service.get_all_roles(
            role_dto=role_dto,
        )