# src/web/routers/admin/roles.py

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.application.dto.roles_dto import RoleDTO, RoleResponseDTO
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.web.dependencies.auth import (
    get_current_admin,
    get_employee_id_from_request,
)
from src.web.dependencies.services import get_application_service_factory
from src.web.models.roles import (
    AdminRoleCreateRequest,
    AdminRoleResponse,
    UserRoleCreateRequest,
    UserRoleResponse,
)


router = APIRouter(
    prefix="/admin/roles",
    tags=["admin roles"],
    dependencies=[Depends(get_current_admin)],
)


handlers = {
    "DomainOperationError": 400,
    "DomainSecurityError": 403,
    "ItemValidationError": 400,
    "ItemNotFoundError": 404,

    "RoleError": 500,
    "RoleNotFoundError": 404,
    "RoleAlreadyExistsError": 409,
    "RoleValidationError": 400,
    "RoleOperationError": 400,
    "RoleSecurityError": 403,

    "AdminNotFoundError": 404,
    "AdminValidationError": 400,
}


# ---------------------------------------------------------------------
# Response mappers
# ---------------------------------------------------------------------

def to_admin_role_response(
    response_dto: RoleResponseDTO[AdminPermission],
) -> AdminRoleResponse:
    return AdminRoleResponse(
        role_id=response_dto.role_id,
        name=response_dto.name,
        permissions=sorted(
            response_dto.permissions,
            key=lambda permission: permission.value,
        ),
        description=response_dto.description,
        is_system_role=response_dto.is_system_role,
    )


def to_admin_role_responses(
    response_dtos: list[RoleResponseDTO[AdminPermission]],
) -> list[AdminRoleResponse]:
    return [
        to_admin_role_response(response_dto)
        for response_dto in response_dtos
    ]


def to_user_role_response(
    response_dto: RoleResponseDTO[UserPermission],
) -> UserRoleResponse:
    return UserRoleResponse(
        role_id=response_dto.role_id,
        name=response_dto.name,
        permissions=sorted(
            response_dto.permissions,
            key=lambda permission: permission.value,
        ),
        description=response_dto.description,
        is_system_role=response_dto.is_system_role,
    )


def to_user_role_responses(
    response_dtos: list[RoleResponseDTO[UserPermission]],
) -> list[UserRoleResponse]:
    return [
        to_user_role_response(response_dto)
        for response_dto in response_dtos
    ]


# ---------------------------------------------------------------------
# Request -> Application DTO mappers
# ---------------------------------------------------------------------

def admin_role_create_request_to_dto(
    *,
    request: AdminRoleCreateRequest,
    actor_admin_id: int,
) -> RoleDTO[AdminPermission]:
    return RoleDTO[AdminPermission](
        actor_admin_id=actor_admin_id,
        name=request.name,
        permissions=frozenset(request.permissions),
        description=request.description,
        is_system_role=request.is_system_role,
    )


def admin_role_id_to_dto(
    *,
    role_id: int,
    actor_admin_id: int,
) -> RoleDTO[AdminPermission]:
    return RoleDTO[AdminPermission](
        actor_admin_id=actor_admin_id,
        role_id=role_id,
    )


def admin_roles_list_to_dto(
    *,
    actor_admin_id: int,
) -> RoleDTO[AdminPermission]:
    return RoleDTO[AdminPermission](
        actor_admin_id=actor_admin_id,
    )


def user_role_create_request_to_dto(
    *,
    request: UserRoleCreateRequest,
    actor_admin_id: int,
) -> RoleDTO[UserPermission]:
    return RoleDTO[UserPermission](
        actor_admin_id=actor_admin_id,
        name=request.name,
        permissions=frozenset(request.permissions),
        description=request.description,
        is_system_role=request.is_system_role,
    )


def user_role_id_to_dto(
    *,
    role_id: int,
    actor_admin_id: int,
) -> RoleDTO[UserPermission]:
    return RoleDTO[UserPermission](
        actor_admin_id=actor_admin_id,
        role_id=role_id,
    )


def user_roles_list_to_dto(
    *,
    actor_admin_id: int,
) -> RoleDTO[UserPermission]:
    return RoleDTO[UserPermission](
        actor_admin_id=actor_admin_id,
    )


# ---------------------------------------------------------------------
# Permission endpoints
# ---------------------------------------------------------------------

@router.get(
    "/admin/permissions",
    response_model=list[AdminPermission],
    status_code=status.HTTP_200_OK,
    summary="Get available admin permissions",
)
def get_admin_permissions():
    return list(AdminPermission)


@router.get(
    "/user/permissions",
    response_model=list[UserPermission],
    status_code=status.HTTP_200_OK,
    summary="Get available user permissions",
)
def get_user_permissions():
    return list(UserPermission)


# ---------------------------------------------------------------------
# Admin role endpoints
# ---------------------------------------------------------------------

@router.post(
    "/admin",
    response_model=AdminRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create admin role",
)
def create_admin_role(
    role_request: AdminRoleCreateRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    role_dto = admin_role_create_request_to_dto(
        request=role_request,
        actor_admin_id=actor_admin_id,
    )

    response_dto = asf.admin_role_service().create_role(
        role_dto=role_dto,
    )

    return to_admin_role_response(response_dto)


@router.get(
    "/admin",
    response_model=list[AdminRoleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all admin roles",
)
def get_all_admin_roles(
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    role_dto = admin_roles_list_to_dto(
        actor_admin_id=actor_admin_id,
    )

    response_dtos = asf.admin_role_service().get_all_roles(
        role_dto=role_dto,
    )

    return to_admin_role_responses(response_dtos)


@router.get(
    "/admin/{role_id}",
    response_model=AdminRoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get admin role by id",
)
def get_admin_role(
    role_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    role_dto = admin_role_id_to_dto(
        role_id=role_id,
        actor_admin_id=actor_admin_id,
    )

    response_dto = asf.admin_role_service().get_role(
        role_dto=role_dto,
    )

    return to_admin_role_response(response_dto)


@router.delete(
    "/admin/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete admin role",
)
def delete_admin_role(
    role_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    role_dto = admin_role_id_to_dto(
        role_id=role_id,
        actor_admin_id=actor_admin_id,
    )

    asf.admin_role_service().delete_role(
        role_dto=role_dto,
    )

    return None


# ---------------------------------------------------------------------
# User role endpoints
# ---------------------------------------------------------------------

@router.post(
    "/user",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user role",
)
def create_user_role(
    role_request: UserRoleCreateRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    role_dto = user_role_create_request_to_dto(
        request=role_request,
        actor_admin_id=actor_admin_id,
    )

    response_dto = asf.user_role_service().create_role(
        role_dto=role_dto,
    )

    return to_user_role_response(response_dto)


@router.get(
    "/user",
    response_model=list[UserRoleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all user roles",
)
def get_all_user_roles(
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    role_dto = user_roles_list_to_dto(
        actor_admin_id=actor_admin_id,
    )

    response_dtos = asf.user_role_service().get_all_roles(
        role_dto=role_dto,
    )

    return to_user_role_responses(response_dtos)


@router.get(
    "/user/{role_id}",
    response_model=UserRoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user role by id",
)
def get_user_role(
    role_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    role_dto = user_role_id_to_dto(
        role_id=role_id,
        actor_admin_id=actor_admin_id,
    )

    response_dto = asf.user_role_service().get_role(
        role_dto=role_dto,
    )

    return to_user_role_response(response_dto)


@router.delete(
    "/user/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user role",
)
def delete_user_role(
    role_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    role_dto = user_role_id_to_dto(
        role_id=role_id,
        actor_admin_id=actor_admin_id,
    )

    asf.user_role_service().delete_role(
        role_dto=role_dto,
    )

    return None