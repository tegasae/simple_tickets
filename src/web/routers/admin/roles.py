# src/web/routers/admin/roles.py

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role

from src.web.dependencies.auth import get_current_admin
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
    role: Role[AdminPermission],
) -> AdminRoleResponse:
    return AdminRoleResponse(
        role_id=role.role_id,
        name=role.name,
        permissions=sorted(
            role.permissions,
            key=lambda permission: permission.value,
        ),
        description=role.description,
        is_system_role=role.is_system_role,
    )


def to_admin_role_responses(
    roles,
) -> list[AdminRoleResponse]:
    return [
        to_admin_role_response(role)
        for role in roles
    ]


def to_user_role_response(
    role: Role[UserPermission],
) -> UserRoleResponse:
    return UserRoleResponse(
        role_id=role.role_id,
        name=role.name,
        permissions=sorted(
            role.permissions,
            key=lambda permission: permission.value,
        ),
        description=role.description,
        is_system_role=role.is_system_role,
    )


def to_user_role_responses(
    roles,
) -> list[UserRoleResponse]:
    return [
        to_user_role_response(role)
        for role in roles
    ]


# ---------------------------------------------------------------------
# Request -> Application mappers
# ---------------------------------------------------------------------

def admin_role_create_request_to_kwargs(
    *,
    request: AdminRoleCreateRequest,
) -> dict:
    return {
        "name": request.name,
        "permissions": request.permissions,
        "description": request.description,
        "is_system_role": request.is_system_role,
    }


def user_role_create_request_to_kwargs(
    *,
    request: UserRoleCreateRequest,
) -> dict:
    return {
        "name": request.name,
        "permissions": request.permissions,
        "description": request.description,
        "is_system_role": request.is_system_role,
    }


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
):
    kwargs = admin_role_create_request_to_kwargs(
        request=role_request,
    )

    role = asf.admin_role_service().create_role(
        **kwargs,
    )

    return to_admin_role_response(role)


@router.get(
    "/admin",
    response_model=list[AdminRoleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all admin roles",
)
def get_all_admin_roles(
    asf=Depends(get_application_service_factory),
):
    roles = asf.admin_role_service().get_all_roles()

    return to_admin_role_responses(roles)


@router.get(
    "/admin/{role_id}",
    response_model=AdminRoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get admin role by id",
)
def get_admin_role(
    role_id: int,
    asf=Depends(get_application_service_factory),
):
    role = asf.admin_role_service().get_role(
        role_id=role_id,
    )

    return to_admin_role_response(role)


@router.delete(
    "/admin/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete admin role",
)
def delete_admin_role(
    role_id: int,
    asf=Depends(get_application_service_factory),
):
    asf.admin_role_service().delete_role(
        role_id=role_id,
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
):
    kwargs = user_role_create_request_to_kwargs(
        request=role_request,
    )

    role = asf.user_role_service().create_role(
        **kwargs,
    )

    return to_user_role_response(role)


@router.get(
    "/user",
    response_model=list[UserRoleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all user roles",
)
def get_all_user_roles(
    asf=Depends(get_application_service_factory),
):
    roles = asf.user_role_service().get_all_roles()

    return to_user_role_responses(roles)


@router.get(
    "/user/{role_id}",
    response_model=UserRoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user role by id",
)
def get_user_role(
    role_id: int,
    asf=Depends(get_application_service_factory),
):
    role = asf.user_role_service().get_role(
        role_id=role_id,
    )

    return to_user_role_response(role)


@router.delete(
    "/user/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user role",
)
def delete_user_role(
    role_id: int,
    asf=Depends(get_application_service_factory),
):
    asf.user_role_service().delete_role(
        role_id=role_id,
    )

    return None