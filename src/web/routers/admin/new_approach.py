

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette import status

from src.application.factory import ApplicationServiceFactory
from src.web.dependencies.auth import require_current_admin, get_current_admin, get_user_id_from_request
from src.web.dependencies.services import get_application_service_factory

router = APIRouter(prefix="/admin/new", tags=["new approcach"], dependencies=[Depends(get_current_admin)])


class ClientCreateRequest(BaseModel):
    name: str
    email: str = ""
    address: str = ""
    phone: str = ""


class ClientUpdateContactRequest(BaseModel):
    email: str = ""
    address: str = ""
    phone: str = ""



@router.post(
    "/",
    response_model=AdminView,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new admin",
    description="Create a new admin account."
)
async def create_admin(
        admin_create: AdminCreate,
        #sf: ServiceFactory = Depends(get_service_factory_admin_name_new),
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Create a new admin account.

    - **name**: Unique admin username
    - **email**: Admin email address
    - **password**: Admin password (min 8 characters)
    - **enabled**: Whether the admin is active (default: True)
    """
    # try:
    admin_service=sf.get_admin_service()


    # Convert to service layer data
    create_data = CreateAdminData(
        name=admin_create.name,
        email=admin_create.email,
        password=admin_create.password,
        enabled=admin_create.enabled
    )

    # Create admin

    admin = admin_service.create_admin(create_admin_data=create_data)

    # Convert to view model
    return AdminView.from_admin(admin)




@router.post("/admin-id", response_model=None)
def new(
    sf:ApplicationServiceFactory=Depends(get_application_service_factory),
    actor_admin_id: int = Depends(get_user_id_from_request)
):
        print(sf)
        return jsonable_encoder({"new":1,"actor":actor_admin_id})


@router.post("/without", response_model=None)
def new(

):

        return jsonable_encoder({"new":2})


