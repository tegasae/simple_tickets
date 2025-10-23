from typing import List, Annotated

from fastapi import APIRouter, Depends, status

from src.domain.model import Admin
from src.services.service_layer.data import CreateAdminData
from src.services.service_layer.factory import ServiceFactory
from src.web.dependicies import get_service_factory
from src.web.dependicies_auth import get_current_user

from src.web.models import AdminView, AdminCreate, AdminUpdate

router = APIRouter(
    prefix="/admins",
    tags=["admins"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)]
)

handlers = {
    'AdminError':500,
    'AdminNotFoundError':404,
    'AdminAlreadyExistsError': 409,
    'AdminValidationError': 400,
    'AdminOperationError': 400,
    'AdminSecurityError':403
}




# CREATE - Create new admin (no authorization for now)
@router.post(
    "/",
    response_model=AdminView,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new admin",
    description="Create a new admin account."
)
async def create_admin(
        admin_create: AdminCreate,
        sf: ServiceFactory = Depends(get_service_factory)
):
    """
    Create a new admin account.

    - **name**: Unique admin username
    - **email**: Admin email address
    - **password**: Admin password (min 8 characters)
    - **enabled**: Whether the admin is active (default: True)
    """
    # try:
    admin_service = sf.get_admin_service()

    # Check if admin already exists
    # if admin_service.admin_exists(admin_create.name):
    #    raise HTTPException(
    #        status_code=status.HTTP_409_CONFLICT,
    #        detail=f"Admin with name '{admin_create.name}' already exists"
    #    )

    # Convert to service layer data
    create_data = CreateAdminData(
        name=admin_create.name,
        email=admin_create.email,
        password=admin_create.password,
        enabled=admin_create.enabled
    )

    # Create admin
    admin = admin_service.execute('create', create_admin_data=create_data)

    # Convert to view model
    return AdminView.from_admin(admin)




# READ - Get all admins (no authorization for now)
@router.get(
    "/",
    response_model=List[AdminView],
    summary="Get all admins",
    description="Retrieve list of all admins."
)
async def read_admins(
        sf: ServiceFactory = Depends(get_service_factory)
):
    """
    Retrieve a list of all admin accounts.

    Returns all admins in the system.
    """
    admin_service = sf.get_admin_service()
    all_admins = admin_service.list_all_admins()

    # Convert to view models
    return [AdminView.from_admin(admin) for admin in all_admins]



# READ - Get admin by ID (no authorization for now)
@router.get(
    "/{admin_id}",
    response_model=AdminView,
    summary="Get admin by ID",
    description="Retrieve specific admin by ID."
)
async def read_admin(
        admin_id: int,
        sf: ServiceFactory = Depends(get_service_factory)
):
    """
    Retrieve a specific admin by their ID.

    - **admin_id**: The unique identifier of the admin
    """
    # try:
    admin_service = sf.get_admin_service()
    admin = admin_service.execute('get_by_id', admin_id=admin_id)



    return AdminView.from_admin(admin)




# READ - Get admin by name (no authorization for now)
@router.get(
    "/name/{admin_name}",
    response_model=AdminView,
    summary="Get admin by name",
    description="Retrieve specific admin by name."
)
async def read_admin_by_name(
        admin_name: str,
        sf: ServiceFactory = Depends(get_service_factory)
):
    """
    Retrieve a specific admin by their username.

    - **admin_name**: The unique username of the admin
    """
    admin_service = sf.get_admin_service()
    admin = admin_service.execute('get_by_name', name=admin_name)

    return AdminView.from_admin(admin)


# UPDATE - Update admin (no authorization for now)
@router.put(
    "/{admin_id}",
    response_model=AdminView,
    summary="Update admin",
    description="Update an existing admin account."
)
async def update_admin(
        admin_id: int,
        admin_update: AdminUpdate,
        sf: ServiceFactory = Depends(get_service_factory)
):
    """
    Update an existing admin account.

    - **admin_id**: The admin to update
    - **email**: New email address (optional)
    - **enabled**: New enabled status (optional)
    - **password**: New password (optional)
    """
    admin_service = sf.get_admin_service()
   # Get the target admin
    target_admin = admin_service.execute('get_by_id', admin_id=admin_id)


    updated_admin = None

    # Update email if provided
    if admin_update.email is not None:
        updated_admin = admin_service.execute(
            'update_email',
            name=target_admin.name,
            new_email=admin_update.email
        )

    # Update password if provided
    if admin_update.password is not None:
        updated_admin = admin_service.execute(
       'change_password',
        name=target_admin.name,
        new_password=admin_update.password
        )

    # Update enabled status if provided
    if admin_update.enabled is not None:
        if admin_update.enabled != target_admin.enabled:
            updated_admin = admin_service.execute('toggle_status', name=target_admin.name)

    # Get the final updated admin
    final_admin = admin_service.execute('get_by_id', admin_id=admin_id)

    return AdminView.from_admin(final_admin)



# DELETE - Delete admin (no authorization for now)
@router.delete(
    "/{admin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete admin",
    description="Delete an admin account."
)
async def delete_admin(
        admin_id: int,
        sf: ServiceFactory = Depends(get_service_factory)
):
    """
    Delete an admin account.

    - **admin_id**: The admin to delete
    """
    admin_service = sf.get_admin_service()
    # Check if admin exists

    admin_service.execute('remove_by_id',admin_id=admin_id)
    return None



# Toggle admin status (no authorization for now)
@router.post(
    "/{admin_id}/toggle-status",
    response_model=AdminView,
    summary="Toggle admin status",
    description="Toggle admin enabled/disabled status."
)
async def toggle_admin_status(
        admin_id: int,
        sf: ServiceFactory = Depends(get_service_factory)
):
    """
    Toggle an admin's enabled/disabled status.

    - **admin_id**: The admin whose status to toggle
    """

    admin_service = sf.get_admin_service()

    # Get admin to ensure they exist
    target_admin = admin_service.execute('get_by_id', admin_id=admin_id)

        # Toggle status
    updated_admin = admin_service.execute('toggle_status', name=target_admin.name)

    return AdminView.from_admin(updated_admin)


# Check if admin exists (public endpoint)
@router.get(
    "/check/{admin_name}/exists",
    summary="Check admin existence",
    description="Check if an admin with the given name exists."
)
async def check_admin_exists(
        admin_name: str,
        sf: ServiceFactory = Depends(get_service_factory)
):
    """
    Check if an admin with the given name exists.

    - **admin_name**: The admin name to check
    """
    admin_service = sf.get_admin_service()
    exists = admin_service.admin_exists(admin_name)

    return {"exists": exists}


