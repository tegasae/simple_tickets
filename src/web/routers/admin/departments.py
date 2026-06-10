# src/web/routers/admin/departments.py

from fastapi import APIRouter, Depends, status

from src.application.dto.department_dto import DepartmentDTO


from src.web.dependencies.auth import get_current_admin, get_employee_id_from_request
from src.web.dependencies.services import get_application_service_factory
from src.web.models.department import DepartmentCreateRequest, DepartmentUpdateRequest, DepartmentResponse

router = APIRouter(
    prefix="/admin/departments",
    tags=["admin departments"],
    dependencies=[Depends(get_current_admin)],
)


# -------------------------
# Exception handlers
# -------------------------

#exception_handlers = ExceptionHandlerRegistry()

#exception_handlers.add_all_standard_handlers(
#    exceptions={
#        DomainOperationError: status.HTTP_400_BAD_REQUEST,
#        ItemValidationError: status.HTTP_400_BAD_REQUEST,
#        NotFoundError: status.HTTP_404_NOT_FOUND,
#        OptimisticLockError: status.HTTP_409_CONFLICT,
#    }
#)


# -------------------------
# Mappers
# -------------------------

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


def id_to_dto(
    *,
    department_id: int,
    actor_admin_id: int,
) -> DepartmentDTO:
    return DepartmentDTO(
        actor_admin_id=actor_admin_id,
        department_id=department_id,
    )


def response_dto_to_response(dto) -> DepartmentResponse:
    return DepartmentResponse(
        department_id=dto.department_id,
        name=dto.name,
        enabled=dto.enabled,
        date_created=dto.date_created,
    )


# -------------------------
# Endpoints
# -------------------------

@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    request: DepartmentCreateRequest,
    actor_admin_id: int = Depends(get_employee_id_from_request),
    asf=Depends(get_application_service_factory),
):
    dto = create_request_to_dto(
        request=request,
        actor_admin_id=actor_admin_id,
    )

    result = asf.department_service().create_department(
        department_dto=dto,
    )

    return response_dto_to_response(result)


@router.get(
    "/",
    response_model=list[DepartmentResponse],
)
def get_all_departments(
    actor_admin_id: int = Depends(get_employee_id_from_request),
    asf=Depends(get_application_service_factory),
):
    dto = DepartmentDTO(
        actor_admin_id=actor_admin_id,
    )

    result = asf.department_service().get_all(
        department_dto=dto,
    )

    return [
        response_dto_to_response(department)
        for department in result
    ]


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
)
def get_department(
    department_id: int,
    actor_admin_id: int = Depends(get_employee_id_from_request),
    asf=Depends(get_application_service_factory),
):
    dto = id_to_dto(
        department_id=department_id,
        actor_admin_id=actor_admin_id,
    )

    result = asf.department_service().get_by_id(
        department_dto=dto,
    )

    return response_dto_to_response(result)


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
)
def update_department(
    department_id: int,
    request: DepartmentUpdateRequest,
    actor_admin_id: int = Depends(get_employee_id_from_request),
    asf=Depends(get_application_service_factory),
):
    dto = update_request_to_dto(
        department_id=department_id,
        request=request,
        actor_admin_id=actor_admin_id,
    )

    result = asf.department_service().update_department(
        department_dto=dto,
    )

    return response_dto_to_response(result)


@router.patch(
    "/{department_id}/enable",
    response_model=DepartmentResponse,
)
def enable_department(
    department_id: int,
    actor_admin_id: int = Depends(get_employee_id_from_request),
    asf=Depends(get_application_service_factory),
):
    dto = id_to_dto(
        department_id=department_id,
        actor_admin_id=actor_admin_id,
    )

    result = asf.department_service().enable_department(
        department_dto=dto,
    )

    return response_dto_to_response(result)


@router.patch(
    "/{department_id}/disable",
    response_model=DepartmentResponse,
)
def disable_department(
    department_id: int,
    actor_admin_id: int = Depends(get_employee_id_from_request),
    asf=Depends(get_application_service_factory),
):
    dto = id_to_dto(
        department_id=department_id,
        actor_admin_id=actor_admin_id,
    )

    result = asf.department_service().disable_department(
        department_dto=dto,
    )

    return response_dto_to_response(result)


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_department(
    department_id: int,
    actor_admin_id: int = Depends(get_employee_id_from_request),
    asf=Depends(get_application_service_factory),
):
    dto = id_to_dto(
        department_id=department_id,
        actor_admin_id=actor_admin_id,
    )

    asf.department_service().delete_department(
        department_dto=dto,
    )

    return None