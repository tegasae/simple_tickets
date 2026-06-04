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
    AdminUpdateRequest,
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
# Response mappers
# ---------------------------------------------------------------------

def to_admin_response(response_dto) -> AdminResponse:
    """
    Convert application AdminResponseDTO to web AdminResponse.
    """
    return AdminResponse.model_validate(response_dto)


def to_admin_responses(response_dtos) -> list[AdminResponse]:
    """
    Convert list[AdminResponseDTO] to list[AdminResponse].
    """
    return [
        to_admin_response(response_dto)
        for response_dto in response_dtos
    ]


# ---------------------------------------------------------------------
# Request -> Application DTO mappers
# ---------------------------------------------------------------------

def admin_create_request_to_dto(
    *,
    request: AdminCreateRequest,
    actor_admin_id: int,
) -> AdminDTO:
    """
    Convert create request to application AdminDTO.

    actor_admin_id comes from authenticated admin.
    Other fields come from request body.
    """
    return AdminDTO(
        actor_admin_id=actor_admin_id,
        **request.model_dump(),
    )


def admin_update_request_to_dto(
    *,
    request: AdminUpdateRequest,
    actor_admin_id: int,
    employee_id: int,
) -> AdminDTO:
    """
    Convert update request to application AdminDTO.

    employee_id comes from path.
    actor_admin_id comes from authenticated admin.
    """
    return AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        **request.model_dump(),
    )


def admin_attach_account_request_to_dto(
    *,
    request: AdminAttachAccountRequest,
    actor_admin_id: int,
    employee_id: int,
) -> AdminDTO:
    """
    Convert attach-account request to AdminDTO.
    """
    return AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        login=request.login,
        password=request.password,
        enable_account=request.enable_account,
    )


def admin_change_password_request_to_dto(
    *,
    request: AdminChangePasswordRequest,
    actor_admin_id: int,
    employee_id: int,
) -> AdminDTO:
    """
    Convert change-password request to AdminDTO.
    """
    return AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        password=request.password,
    )


def admin_roles_request_to_dto(
    *,
    request: AdminRolesRequest,
    actor_admin_id: int,
    employee_id: int,
) -> AdminDTO:
    """
    Convert roles request to AdminDTO.
    """
    return AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        roles=frozenset(request.roles),
    )


def admin_id_to_dto(
    *,
    actor_admin_id: int,
    employee_id: int,
) -> AdminDTO:
    """
    Build AdminDTO for operations that need only target admin id.
    """
    return AdminDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------

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
):
    dto = admin_create_request_to_dto(
        request=admin_request,
        actor_admin_id=actor_admin_id,
    )

    response_dto = asf.admin_service().create_admin(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = AdminDTO(actor_admin_id=actor_admin_id)

    response_dtos = asf.admin_service().get_all(admin_dto=dto)

    return to_admin_responses(response_dtos)


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
):
    dto = AdminDTO(
        actor_admin_id=actor_admin_id,
        login=login,
    )

    response_dto = asf.admin_service().find_by_login(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = admin_id_to_dto(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().get_by_id(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = admin_update_request_to_dto(
        request=admin_request,
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().update_admin(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = admin_attach_account_request_to_dto(
        request=account_request,
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().attach_account(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = admin_id_to_dto(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().detach_account(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = admin_change_password_request_to_dto(
        request=password_request,
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().change_password(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = admin_roles_request_to_dto(
        request=roles_request,
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().grant_role(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = admin_roles_request_to_dto(
        request=roles_request,
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().revoke_role(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = admin_id_to_dto(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().disable(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = admin_id_to_dto(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.admin_service().enable(admin_dto=dto)

    return to_admin_response(response_dto)


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
):
    dto = admin_id_to_dto(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    asf.admin_service().delete(admin_dto=dto)

    return None