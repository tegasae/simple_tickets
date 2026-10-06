from src.application.dto.department_dto import DepartmentDTO
from src.web.models.department import DepartmentCreateRequest, DepartmentUpdateRequest, DepartmentResponse

class DepartmentMapper:
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
    def response_dto_to_response(dto) -> DepartmentResponse:
        return DepartmentResponse(
            department_id=dto.department_id,
            name=dto.name,
            enabled=dto.enabled,
            date_created=dto.date_created,
        )
