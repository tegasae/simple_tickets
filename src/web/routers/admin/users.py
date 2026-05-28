# src/web/routers/admin/users.py

from fastapi import APIRouter, Depends, status

from src.application.dto.employee_dto import UserDTO
from src.web.dependencies.auth import (
    get_current_admin,
    get_employee_id_from_request,
)
from src.web.dependencies.services import get_application_service_factory
from src.web.models.users import (
    UserAttachAccountRequest,
    UserChangePasswordRequest,
    UserCreateRequest,
    UserResponse,
    UserRolesRequest,
    UserUpdateRequest,
)


router = APIRouter(
    prefix="/admin/users",
    tags=["admin users"],

    # This dependency protects the whole router.
    # Every endpoint below requires current admin authentication.
    dependencies=[Depends(get_current_admin)],
)


# Exception mapping for ExceptionHandlerRegistry.
#
# Example in main.py:
#
#     registry.add_all_handlers_from_module(
#         module_name="src.domain.exceptions",
#         exceptions=admin.users.handlers,
#     )
#
handlers = {
    # common domain errors
    "DomainOperationError": 400,
    "DomainSecurityError": 403,
    "ItemValidationError": 400,
    "ItemNotFoundError": 404,

    # admin/user-related domain errors if they exist in src.domain.exceptions
    "AdminError": 500,
    "AdminNotFoundError": 404,
    "AdminValidationError": 400,
    "AdminOperationError": 400,
    "AdminSecurityError": 403,

    "UserError": 500,
    "UserNotFoundError": 404,
    "UserAlreadyExistsError": 409,
    "UserValidationError": 400,
    "UserOperationError": 400,
    "UserSecurityError": 403,
}


# ---------------------------------------------------------------------
# Response mappers
# ---------------------------------------------------------------------

def to_user_response(response_dto) -> UserResponse:
    """
    Convert application UserResponseDTO to web UserResponse.
    """
    return UserResponse.model_validate(response_dto)


def to_user_responses(response_dtos) -> list[UserResponse]:
    """
    Convert list[UserResponseDTO] to list[UserResponse].
    """
    return [
        to_user_response(response_dto)
        for response_dto in response_dtos
    ]


# ---------------------------------------------------------------------
# Request -> Application DTO mappers
# ---------------------------------------------------------------------

def user_create_request_to_dto(
    *,
    request: UserCreateRequest,
    actor_admin_id: int,
) -> UserDTO:
    """
    Convert create request to application UserDTO.

    actor_admin_id comes from authenticated admin.
    Other fields come from request body.
    """
    return UserDTO(
        actor_admin_id=actor_admin_id,
        client_id=request.client_id,
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        phone=request.phone,
        login=request.login,
        password=request.password,
        enable=request.enable,
        enable_account=request.enable_account,
        roles=frozenset(request.roles),
    )


def user_update_request_to_dto(
    *,
    request: UserUpdateRequest,
    actor_admin_id: int,
    employee_id: int,
) -> UserDTO:
    """
    Convert update request to application UserDTO.

    employee_id comes from path parameter.
    actor_admin_id comes from authenticated admin.
    """
    return UserDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        phone=request.phone,
    )


def user_attach_account_request_to_dto(
    *,
    request: UserAttachAccountRequest,
    actor_admin_id: int,
    employee_id: int,
) -> UserDTO:
    """
    Convert attach-account request to UserDTO.
    """
    return UserDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        login=request.login,
        password=request.password,
        enable_account=request.enable_account,
    )


def user_change_password_request_to_dto(
    *,
    request: UserChangePasswordRequest,
    actor_admin_id: int,
    employee_id: int,
) -> UserDTO:
    """
    Convert change-password request to UserDTO.
    """
    return UserDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        password=request.password,
    )


def user_roles_request_to_dto(
    *,
    request: UserRolesRequest,
    actor_admin_id: int,
    employee_id: int,
) -> UserDTO:
    """
    Convert roles request to UserDTO.
    """
    return UserDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
        roles=frozenset(request.roles),
    )


def user_id_to_dto(
    *,
    actor_admin_id: int,
    employee_id: int,
) -> UserDTO:
    """
    Build UserDTO for operations that need only target user id.
    """
    return UserDTO(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user.",
)
def create_user(
    user_request: UserCreateRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_create_request_to_dto(
        request=user_request,
        actor_admin_id=actor_admin_id,
    )

    response_dto = asf.user_service().create_user(user_dto=dto)

    return to_user_response(response_dto)


@router.get(
    "/",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    description="Get all users.",
)
def get_all_users(
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = UserDTO(actor_admin_id=actor_admin_id)

    response_dtos = asf.user_service().get_all(user_dto=dto)

    return to_user_responses(response_dtos)


@router.get(
    "/by-login/{login}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Find user by login",
    description="Find user by login.",
)
def find_user_by_login(
    login: str,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = UserDTO(
        actor_admin_id=actor_admin_id,
        login=login,
    )

    response_dto = asf.user_service().find_by_login(user_dto=dto)

    return to_user_response(response_dto)


@router.get(
    "/{employee_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by id",
    description="Get user by id.",
)
def get_user(
    employee_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_id_to_dto(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.user_service().get_by_id(user_dto=dto)

    return to_user_response(response_dto)


@router.put(
    "/{employee_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
    description="Update user personal/contact data.",
)
def update_user(
    employee_id: int,
    user_request: UserUpdateRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_update_request_to_dto(
        request=user_request,
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.user_service().update_user(user_dto=dto)

    return to_user_response(response_dto)


@router.post(
    "/{employee_id}/account",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Attach account",
    description="Attach login/password account to user.",
)
def attach_account(
    employee_id: int,
    account_request: UserAttachAccountRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_attach_account_request_to_dto(
        request=account_request,
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.user_service().attach_account(user_dto=dto)

    return to_user_response(response_dto)


@router.delete(
    "/{employee_id}/account",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Detach account",
    description="Detach account from user.",
)
def detach_account(
    employee_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_id_to_dto(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.user_service().detach_account(user_dto=dto)

    return to_user_response(response_dto)


@router.patch(
    "/{employee_id}/password",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change user account password.",
)
def change_password(
    employee_id: int,
    password_request: UserChangePasswordRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_change_password_request_to_dto(
        request=password_request,
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.user_service().change_password(user_dto=dto)

    return to_user_response(response_dto)


@router.post(
    "/{employee_id}/roles",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Grant roles",
    description="Grant roles to user.",
)
def grant_roles(
    employee_id: int,
    roles_request: UserRolesRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_roles_request_to_dto(
        request=roles_request,
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.user_service().grant_role(user_dto=dto)

    return to_user_response(response_dto)


@router.delete(
    "/{employee_id}/roles",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke roles",
    description="Revoke roles from user.",
)
def revoke_roles(
    employee_id: int,
    roles_request: UserRolesRequest,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_roles_request_to_dto(
        request=roles_request,
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.user_service().revoke_role(user_dto=dto)

    return to_user_response(response_dto)


@router.patch(
    "/{employee_id}/disable",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Disable user",
    description="Disable user.",
)
def disable_user(
    employee_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_id_to_dto(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.user_service().disable(user_dto=dto)

    return to_user_response(response_dto)


@router.patch(
    "/{employee_id}/enable",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Enable user",
    description="Enable user.",
)
def enable_user(
    employee_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_id_to_dto(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    response_dto = asf.user_service().enable(user_dto=dto)

    return to_user_response(response_dto)


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete user.",
)
def delete_user(
    employee_id: int,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
):
    dto = user_id_to_dto(
        actor_admin_id=actor_admin_id,
        employee_id=employee_id,
    )

    asf.user_service().delete(user_dto=dto)

    return None