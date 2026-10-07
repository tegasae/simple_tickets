from src.application.dto.department_dto import DepartmentDTO
from src.web.models.department import DepartmentCreateRequest, DepartmentUpdateRequest, DepartmentResponse

class DepartmentMapperDTO:
    @staticmethod
    def create_request_to_dto(
        *,
        request: DepartmentCreateRequest,
        actor_admin_id: int,
    ) -> DepartmentDTO:
        return DepartmentDTO(
        actor_admin_id=actor_admin_id,
        name=request.name,
        enabled=request.enabled,
    )

    @staticmethod
    def update_request_to_dto(
        *,
        department_id: int,
        request: DepartmentUpdateRequest,
        actor_admin_id: int,
    ) -> DepartmentDTO:
        return DepartmentDTO(
            actor_admin_id=actor_admin_id,
            department_id=department_id,
            name=request.name,
        )

    @staticmethod
    def id_to_dto(
        *,
        department_id: int,
        actor_admin_id: int,
    ) -> DepartmentDTO:
        return DepartmentDTO(
            actor_admin_id=actor_admin_id,
            department_id=department_id,
        )

    @staticmethod
    def actor_id_to_dto(
            *,
            actor_admin_id: int,
    ) -> DepartmentDTO:
        return DepartmentDTO(
            actor_admin_id=actor_admin_id,
       )

    @staticmethod
    def to_response(response_dto) -> DepartmentResponse:
        return DepartmentResponse(
            department_id=response_dto.department_id,
            name=response_dto.name,
            enabled=response_dto.enabled,
            date_created=response_dto.date_created,
        )

    @staticmethod
    def to_responses(response_dtos) -> list[DepartmentResponse]:
        return [
            DepartmentResponse.model_validate(response_dto)
            for response_dto in response_dtos
        ]


