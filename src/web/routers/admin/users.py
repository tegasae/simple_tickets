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
)->UserResponse:


    dto = UserDTO(actor_admin_id=actor_admin_id, **user_request.model_dump())

    response_dto = asf.user_service().create_user(user_dto=dto)

    return UserResponse.from_dto(response_dto)


@router.get(
    "/",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    description="Get all users.",
)
def get_all_users(
    client_id:int=0,
    asf=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_employee_id_from_request),
)->list[UserResponse]:
    dto = UserDTO(actor_admin_id=actor_admin_id,client_id=client_id)

    if not client_id:
        response_dtos = asf.user_service().get_all(user_dto=dto)
    else:
        response_dtos = asf.user_service().get_by_client_id(user_dto=dto)
    return UserResponse.from_dtos(response_dtos)




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
)->UserResponse:
    dto = UserDTO(
        actor_admin_id=actor_admin_id,
        login=login,
    )

    response_dto = asf.user_service().find_by_login(user_dto=dto)

    return UserResponse.from_dto(response_dto)





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
)->UserResponse:

    dto=UserDTO(actor_admin_id=actor_admin_id,
        employee_id=employee_id,)
    response_dto = asf.user_service().get_by_id(user_dto=dto)

    return UserResponse.from_dto(response_dto)



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
)->UserResponse:

    dto=UserDTO(actor_admin_id=actor_admin_id,
        employee_id=employee_id,**user_request.model_dump())
    response_dto = asf.user_service().update_user(user_dto=dto)

    return UserResponse.from_dto(response_dto)


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
)->UserResponse:

    dto=UserDTO(actor_admin_id=actor_admin_id,
        employee_id=employee_id,**account_request.model_dump())
    response_dto = asf.user_service().attach_account(user_dto=dto)

    return UserResponse.from_dto(response_dto)


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
)->UserResponse:

    dto=UserDTO(actor_admin_id=actor_admin_id,employee_id=employee_id,)

    response_dto = asf.user_service().detach_account(user_dto=dto)

    return UserResponse.from_dto(response_dto)


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
)->UserResponse:

    dto=UserDTO(actor_admin_id=actor_admin_id,employee_id=employee_id,**password_request.model_dump())
    response_dto = asf.user_service().change_password(user_dto=dto)

    return UserResponse.from_dto(response_dto)


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
)->UserResponse:

    dto=UserDTO(actor_admin_id=actor_admin_id,
        employee_id=employee_id,
                **roles_request.model_dump())
    response_dto = asf.user_service().grant_role(user_dto=dto)

    return UserResponse.from_dto(response_dto)


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
)->UserResponse:

    dto=UserDTO(actor_admin_id=actor_admin_id, employee_id=employee_id,**roles_request.model_dump())
    response_dto = asf.user_service().revoke_role(user_dto=dto)

    return UserResponse.from_dto(response_dto)


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
)->UserResponse:

    dto=UserDTO(actor_admin_id=actor_admin_id,
        employee_id=employee_id,)

    response_dto = asf.user_service().disable(user_dto=dto)

    return UserResponse.from_dto(response_dto)


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
)->UserResponse:

    dto=UserDTO(actor_admin_id=actor_admin_id,employee_id=employee_id,)

    response_dto = asf.user_service().enable(user_dto=dto)

    return UserResponse.from_dto(response_dto)


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
)->None:

    dto=UserDTO(actor_admin_id=actor_admin_id,employee_id=employee_id,)

    asf.user_service().delete(user_dto=dto)

    return None