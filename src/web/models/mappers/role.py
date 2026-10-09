
from src.application.dto.roles_dto import RoleResponseDTO, RoleDTO
from src.web.models.roles import AdminRoleResponse, UserRoleResponse, AdminRoleCreateRequest, UserRoleCreateRequest


# ---------------------------------------------------------------------
# Response mappers
# ---------------------------------------------------------------------

class AdminRoleMapperDTO:
    @staticmethod
    def to_admin_role_response(
        response_dto: RoleResponseDTO,
    ) -> AdminRoleResponse:
        return AdminRoleResponse(
            role_id=response_dto.role_id,
            name=response_dto.name,
            permissions=sorted(
            response_dto.permissions,
            key=lambda permission: permission,
            ),
            description=response_dto.description,
            is_system_role=response_dto.is_system_role,
        )

    @staticmethod
    def to_admin_role_responses(
        response_dtos: list[RoleResponseDTO],
    ) -> list[AdminRoleResponse]:
        return [
            AdminRoleMapperDTO.to_admin_role_response(response_dto)
            for response_dto in response_dtos
        ]

    @staticmethod
    def admin_role_create_request_to_dto(
            *,
            request: AdminRoleCreateRequest,
            actor_admin_id: int,
    ) -> RoleDTO:
        return RoleDTO(
            actor_admin_id=actor_admin_id,
            name=request.name,
            permissions=frozenset(request.permissions),
            description=request.description,
            is_system_role=request.is_system_role,
        )

    @staticmethod
    def admin_role_id_to_dto(
            *,
            role_id: int,
            actor_admin_id: int,
    ) -> RoleDTO:
        return RoleDTO(
            actor_admin_id=actor_admin_id,
            role_id=role_id,
        )

    @staticmethod
    def admin_roles_list_to_dto(
            *,
            actor_admin_id: int,
    ) -> RoleDTO:
        return RoleDTO(
            actor_admin_id=actor_admin_id,
        )


class UserRoleMapperDTO:
    @staticmethod
    def to_user_role_response(
        response_dto: RoleResponseDTO,
    ) -> UserRoleResponse:
        return UserRoleResponse(
            role_id=response_dto.role_id,
            name=response_dto.name,
            permissions=sorted(
            response_dto.permissions,
            key=lambda permission: permission,
        ),
        description=response_dto.description,
        is_system_role=response_dto.is_system_role,
    )

    @staticmethod
    def to_user_role_responses(
        response_dtos: list[RoleResponseDTO],
    ) -> list[UserRoleResponse]:
        return [
            UserRoleMapperDTO.to_user_role_response(response_dto)
            for response_dto in response_dtos
        ]

    @staticmethod
    def user_role_create_request_to_dto(
        *,
        request: UserRoleCreateRequest,
        actor_admin_id: int,
    ) -> RoleDTO:
        return RoleDTO(
            actor_admin_id=actor_admin_id,
            name=request.name,
            permissions=frozenset(request.permissions),
            description=request.description,
            is_system_role=request.is_system_role,
        )

    @staticmethod
    def user_role_id_to_dto(
        *,
        role_id: int,
        actor_admin_id: int,
    ) -> RoleDTO:
        return RoleDTO(
            actor_admin_id=actor_admin_id,
            role_id=role_id,
        )

    @staticmethod
    def user_roles_list_to_dto(
        *,
        actor_admin_id: int,
    ) -> RoleDTO:
        return RoleDTO(
            actor_admin_id=actor_admin_id,
        )
