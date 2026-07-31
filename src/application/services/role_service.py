# src/application/role_service.py

from __future__ import annotations

from typing import Generic, TypeVar, cast

from src.application.assemblers.assembler import RoleAssembler
from src.application.dto.roles_dto import RoleDTO, RoleResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import (
    AdminPermission,
    PermissionBase,
    UserPermission,
)
from src.domain.rbac.role_new import Role
from src.domain.rbac.role_repository import RoleRepository
from src.domain.uow.unit_of_work import UnitOfWork


T = TypeVar("T", bound=PermissionBase)


class RoleService(Generic[T]):
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
            self.permission_operation = AdminPermission.ADMIN_OPERATION
            self.repository=cast(RoleRepository[T], self.uow.roles_admin)
        elif self.permission_type is UserPermission:
            self.permission_operation = AdminPermission.ADMIN_OPERATION
            self.repository = cast(RoleRepository[T], self.uow.roles_user)
        else:
            raise DomainOperationError(
                f"Unknown permission type: {self.permission_type}"
            )

    def _check_actor(self,actor_admin_id:int):
        self.actor.require_actor_admin(
            actor_admin_id=actor_admin_id,
            permission=self.permission_operation
        )


    def create_role(
        self,
        *,
        role_dto: RoleDTO[T],
    ) -> RoleResponseDTO[T]:

        name = role_dto.name.strip()
        description = role_dto.description.strip()
        self._check_actor(actor_admin_id=role_dto.actor_admin_id)

        self._ensure_permissions_match_type(permissions=role_dto.permissions)




        if not name:
            raise DomainOperationError("Role name must not be empty")

        if not role_dto.permissions:
            raise DomainOperationError("Role must have at least one permission")





        with self.uow:
            role = Role(
                role_id=0,
                name=name,
                permissions=role_dto.permissions,
                description=description,
                is_system_role=role_dto.is_system_role,
            )

            return self._save_and_to_dto(
                role=role
            )

    def delete_role(
        self,
        *,
        role_dto: RoleDTO[T],
    ) -> None:


        with (self.uow):

            self._check_actor(actor_admin_id=role_dto.actor_admin_id)
            role = self.repository.get(role_dto.role_id)

            if role.is_system_role:
                raise DomainOperationError(
                    f"Cannot delete system role: {role.name}"
                )

            if self.repository.is_assigned(role_id=role_dto.role_id):
                raise DomainOperationError(
                    f"Role '{role.name}' cannot be deleted because it is assigned"
                )

            self.repository.delete(role_dto.role_id)

    def get_role(
        self,
        *,
        role_dto: RoleDTO[T],
    ) -> RoleResponseDTO[T]:


        with self.uow:
            self._check_actor(actor_admin_id=role_dto.actor_admin_id)

            role = self.repository.get(role_dto.role_id)

            return RoleAssembler.to_dto(role)

    def get_all_roles(self,role_dto:RoleDTO[T]) -> list[RoleResponseDTO[T]]:

        with self.uow:
            self._check_actor(actor_admin_id=role_dto.actor_admin_id)
            return [
                RoleAssembler.to_dto(role)
                for role in self.repository.all()
            ]


    def _save_and_to_dto(
        self,
        *,
        role: Role[T],
    ) -> RoleResponseDTO[T]:
        saved_role = self.repository.add(role)

        return RoleAssembler.to_dto(saved_role)

    def _ensure_permissions_match_type(
        self,
        permissions: frozenset[T],
    ) -> None:
        for permission in permissions:
            if type(permission) is not self.permission_type:
                raise DomainOperationError(
                    "Cannot mix permission types in a single role. "
                    f"Expected {self.permission_type.__name__}, "
                    f"found {type(permission).__name__}"
                )




class AdminRoleService:
    """
    Application service for admin roles.

    Admin roles contain AdminPermission values.
    """

    def __init__(self, uow: UnitOfWork):
        self._service = RoleService[AdminPermission](
            uow=uow,
            permission_type=AdminPermission,
        )

    def create_role(
        self,
        *,
        role_dto: RoleDTO[AdminPermission],
    ) -> RoleResponseDTO[AdminPermission]:


        return self._service.create_role(
            role_dto=role_dto,
        )

    def delete_role(
        self,
        *,
        role_dto: RoleDTO[AdminPermission],
    ) -> None:


        self._service.delete_role(
            role_dto=role_dto,
        )

    def get_role(
        self,
        *,
        role_dto: RoleDTO[AdminPermission],
    ) -> RoleResponseDTO[AdminPermission]:


        return self._service.get_role(
            role_dto=role_dto,
        )

    def get_all_roles(
        self,
        *,
        role_dto: RoleDTO[AdminPermission],
    ) -> list[RoleResponseDTO[AdminPermission]]:
        return self._service.get_all_roles(role_dto=role_dto)




class UserRoleService:
    """
    Application service for user roles.

    User roles contain UserPermission values,
    but they are managed by Admin.
    """

    def __init__(self, uow: UnitOfWork):
        self._service = RoleService[UserPermission](
            uow=uow,
            permission_type=UserPermission,
        )

    def create_role(
        self,
        *,
        role_dto: RoleDTO[UserPermission],
    ) -> RoleResponseDTO[UserPermission]:


        return self._service.create_role(
            role_dto=role_dto,
        )

    def delete_role(
        self,
        *,
        role_dto: RoleDTO[UserPermission],
    ) -> None:


        self._service.delete_role(
            role_dto=role_dto,
        )

    def get_role(
        self,
        *,
        role_dto: RoleDTO[UserPermission],
    ) -> RoleResponseDTO[UserPermission]:
        self._ensure_actor_admin_id_is_valid(role_dto.actor_admin_id)

        return self._service.get_role(
            role_dto=role_dto,
        )

    def get_all_roles(
        self,
        *,
        role_dto: RoleDTO[UserPermission],
    ) -> list[RoleResponseDTO[UserPermission]]:
        self._ensure_actor_admin_id_is_valid(role_dto.actor_admin_id)

        return self._service.get_all_roles(role_dto=role_dto)

    @staticmethod
    def _ensure_actor_admin_id_is_valid(
        actor_admin_id: int,
    ) -> None:
        if actor_admin_id <= 0:
            raise DomainOperationError(
                f"Actor admin id must be positive, got {actor_admin_id}"
            )