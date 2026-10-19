# src/web/routers/admin/admins.py

from fastapi import APIRouter, Depends, status

from src.application.dto.employee_dto import AdminDTO

from src.web.dependencies.auth import (
    get_current_admin,
    get_employee_id_from_request,
)
from src.web.dependencies.services import get_application_service_factory
from src.web.models.admins import (
    AdminAttachAccountRequest,
    AdminChangePasswordRequest,
    AdminCreateRequest,
    AdminResponse,
    AdminRolesRequest,
    AdminUpdateRequest, AdminChangeDepartmentRequest, PermissionsResponse,
)

router = APIRouter(
    prefix="/admin/admins",
    tags=["admin admins"],

    # Protect all endpoints in this router.
    # Public/auth endpoints should live in another router.
    dependencies=[Depends(get_current_admin)],
)


# Exception mapping for ExceptionHandlerRegistry.
#
# Example in main.py:
#
#     registry.add_all_handlers_from_module(
#         module_name="src.domain.exceptions",
#         exceptions=admin.admins.handlers,
#     )
#




# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------
# todo нужны методы включения и отключения аккаунта, а не только его отвязки. Скорее на будущее
@router.post(
    "/",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new admin",
    description="Create a new admin.",
)
def create_admin(
    admin_request: AdminCreateRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:

    dto=AdminDTO(actor_admin_id=actor_admin_id,**admin_request.model_dump())

    response_dto = asf.admin_service().create_admin(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.get(
    "/",
    response_model=list[AdminResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all admins",
    description="Get all admins.",
)
def get_all_admins(
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->list[AdminResponse]:
    dto = AdminDTO(actor_admin_id=actor_admin_id)

    response_dtos = asf.admin_service().get_all(admin_dto=dto)

    return AdminResponse.from_dtos(response_dtos)


@router.get(
    "/permissions",
    response_model=PermissionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current admin permissions",
    description="Get permissions of the current authenticated admin.",
)
def get_permissions(
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->PermissionsResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=actor_admin_id,
    )

    response_dto = asf.admin_service().get_permissions(
        admin_dto=dto,
    )

    return PermissionsResponse.from_dto(response_dto)


@router.get(
    "/by-login/{login}",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Find admin by login",
    description="Find admin by login.",
)
def find_admin_by_login(
    login: str,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        login=login,
    )

    response_dto = asf.admin_service().find_by_login(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.get(
    "/{employee_id}",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Get admin by id",
    description="Get admin by id.",
)
def get_admin(
    employee_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().get_by_id(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.put(
    "/{employee_id}",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Update admin",
    description="Update admin personal/contact data.",
)
def update_admin(
    employee_id: int,
    admin_request: AdminUpdateRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:

    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        **admin_request.model_dump(),
    )
    response_dto = asf.admin_service().update_admin(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.post(
    "/{employee_id}/account",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Attach account",
    description="Attach login/password account to admin.",
)
def attach_account(
    employee_id: int,
    account_request: AdminAttachAccountRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        **account_request.model_dump(),
    )

    response_dto = asf.admin_service().attach_account(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.delete(
    "/{employee_id}/account",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Detach account",
    description="Detach account from admin.",
)
def detach_account(
    employee_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().detach_account(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.patch(
    "/{employee_id}/password",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change admin account password.",
)
def change_password(
    employee_id: int,
    password_request: AdminChangePasswordRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        **password_request.model_dump(),
    )

    response_dto = asf.admin_service().change_password(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.post(
    "/{employee_id}/roles",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Grant roles",
    description="Grant roles to admin.",
)
def grant_roles(
    employee_id: int,
    roles_request: AdminRolesRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        **roles_request.model_dump(),
    )

    response_dto = asf.admin_service().grant_role(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.delete(
    "/{employee_id}/roles",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke roles",
    description="Revoke roles from admin.",
)
def revoke_roles(
    employee_id: int,
    roles_request: AdminRolesRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:
    dto = AdminDTO(employee_id=employee_id, actor_admin_id=actor_admin_id,**roles_request.model_dump())

    response_dto = asf.admin_service().revoke_role(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.patch(
    "/{employee_id}/disable",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Disable admin",
    description="Disable admin.",
)
def disable_admin(
    employee_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().disable(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.patch(
    "/{employee_id}/enable",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Enable admin",
    description="Enable admin.",
)
def enable_admin(
    employee_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->AdminResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().enable(admin_dto=dto)

    return AdminResponse.from_dto(response_dto)


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete admin",
    description="Delete admin.",
)
def delete_admin(
    employee_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->None:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    asf.admin_service().delete(admin_dto=dto)

    return None

@router.patch(
    "/{employee_id}/department",
    response_model=AdminResponse,
)
def change_admin_department(
    employee_id: int,
    request: AdminChangeDepartmentRequest,
    actor_admin_id: int = Depends(get_employee_id_from_request),
    asf=Depends(get_application_service_factory),
)->AdminResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        department_id=request.department_id,
    )
    
    response_dto = asf.admin_service().change_department(
        admin_dto=dto,
    )

    return AdminResponse.from_dto(response_dto)

@router.delete(
    "/{employee_id}/department",
    response_model=AdminResponse,
)
def remove_admin_department(
    employee_id: int,
    actor_admin_id: int = Depends(get_employee_id_from_request),
    asf=Depends(get_application_service_factory),
)->AdminResponse:
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,

    )

    response_dto = asf.admin_service().remove_department(
        admin_dto=dto,
    )

    return AdminResponse.from_dto(response_dto)