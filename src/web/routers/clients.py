#web/routers/client.py
# web/routers/client.py
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException

from src.domain.exceptions import ItemNotFoundError, DomainSecurityError, DomainOperationError, ItemValidationError, \
    ItemAlreadyExistsError
from src.services.service_layer.factory import ServiceFactory
from src.services.service_layer.data import CreateClientData
from src.web.dependicies.dependencies import get_service_factory
from src.web.dependicies.dependicies_auth import get_current_user, get_service_factory_auth
from src.web.models import ClientView, ClientCreate, ClientUpdate

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)]  # All endpoints require authentication
)

# Exception mapping for consistent error responses
handlers = {
    'ItemNotFoundError': 404,
    'DomainSecurityError': 403,
    'DomainOperationError': 400,
    'ItemValidationError': 400,
    'ItemAlreadyExistsError': 409,
}


# ========== PUBLIC ENDPOINT (no auth override) ==========

@router.get(
    "/check/{client_name}/exists",
    summary="Check client existence",
    description="Check if a client with the given name exists. Public endpoint.",
    dependencies=[]  # Override router authentication
)
async def check_client_exists(
        client_name: str,
        sf: ServiceFactory = Depends(get_service_factory)  # Use non-auth factory
):
    """
    Check if a client with the given name exists.

    - **client_name**: The client name to check
    """
    client_service = sf.get_client_service()
    exists = client_service.client_exists(client_name)
    return {"exists": exists}


# ========== AUTHENTICATED ENDPOINTS ==========

# CREATE - Create new client
@router.post(
    "/",
    response_model=ClientView,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
    description="Create a new client account. Requires authentication."
)
async def create_client(
        client_create: ClientCreate,
        sf: ServiceFactory = Depends(get_service_factory_auth)  # Authenticated factory
):
    """
    Create a new client account.

    - **name**: Client name
    - **email**: Client email address
    - **address**: Client address (optional)
    - **phones**: Client phone numbers (optional)
    - **enabled**: Whether the client is active (default: True)
    - **admin_id**: Specific admin ID to assign (optional, defaults to current admin)
    """
    client_service = sf.get_client_service()

    # Convert to service layer data
    create_data = CreateClientData(
        name=client_create.name,
        email=client_create.email,
        address=client_create.address or "",
        phones=client_create.phones or "",
        enabled=client_create.enabled,
        admin_id=client_create.admin_id or 0  # 0 means use current admin
    )

    # Create client (permission checked inside service)
    client = client_service.create_client(create_data)

    return ClientView.from_client(client)


# READ - Get all clients
@router.get(
    "/",
    response_model=List[ClientView],
    summary="Get all clients",
    description="Retrieve list of all clients. Requires authentication."
)
async def read_clients(
        sf: ServiceFactory = Depends(get_service_factory_auth)  # Authenticated factory
):
    """
    Retrieve a list of all client accounts.

    Returns all clients in the system.
    """
    client_service = sf.get_client_service()
    all_clients = client_service.get_all_clients()
    return [ClientView.from_client(client) for client in all_clients]


# READ - Get my clients (clients created by current admin)
@router.get(
    "/my",
    response_model=List[ClientView],
    summary="Get my clients",
    description="Retrieve list of clients created by the current admin. Requires authentication."
)
async def read_my_clients(
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Retrieve clients created by the currently authenticated admin.
    """
    client_service = sf.get_client_service()
    my_clients = client_service.get_my_clients()
    return [ClientView.from_client(client) for client in my_clients]


# READ - Get client by ID
@router.get(
    "/{client_id}",
    response_model=ClientView,
    summary="Get client by ID",
    description="Retrieve specific client by ID. Requires authentication."
)
async def read_client(
        client_id: int,
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Retrieve a specific client by their ID.

    - **client_id**: The unique identifier of the client
    """
    client_service = sf.get_client_service()
    client = client_service.get_client_by_id(client_id)
    return ClientView.from_client(client)


# READ - Get client by name
@router.get(
    "/name/{client_name}",
    response_model=List[ClientView],
    summary="Get clients by name",
    description="Retrieve clients by name. Requires authentication."
)
async def read_client_by_name(
        client_name: str,
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Retrieve clients by name (partial match).

    - **client_name**: The name to search for
    """
    client_service = sf.get_client_service()
    clients = client_service.get_client_by_name(client_name)
    return [ClientView.from_client(client) for client in clients]


# READ - Get clients by admin ID
@router.get(
    "/admin/{admin_id}",
    response_model=List[ClientView],
    summary="Get clients by admin",
    description="Retrieve clients created by a specific admin. Requires authentication."
)
async def read_clients_by_admin(
        admin_id: int,
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Retrieve clients created by a specific admin.

    - **admin_id**: The admin whose clients to retrieve
    """
    client_service = sf.get_client_service()
    clients = client_service.get_clients_by_admin(admin_id)
    return [ClientView.from_client(client) for client in clients]


# UPDATE - Update client
@router.put(
    "/{client_id}",
    response_model=ClientView,
    summary="Update client",
    description="Update an existing client account. Requires authentication."
)
async def update_client(
        client_id: int,
        client_update: ClientUpdate,
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Update an existing client account.

    - **client_id**: The client to update
    - **email**: New email address (optional)
    - **address**: New address (optional)
    - **phones**: New phone numbers (optional)
    - **enabled**: New enabled status (optional)
    - **admin_id**: New admin owner (optional)
    """
    client_service = sf.get_client_service()

    # Update email if provided
    if client_update.email is not None:
        client_service.update_client_email(client_id, client_update.email)

    # Update address if provided
    if client_update.address is not None:
        client_service.update_client_address(client_id, client_update.address)

    # Update phones if provided
    if client_update.phones is not None:
        client_service.update_client_phones(client_id, client_update.phones)

    # Update enabled status if provided
    if client_update.enabled is not None:
        client_service.change_client_status(client_id, client_update.enabled)

    # Update admin if provided
    if client_update.admin_id is not None and client_update.admin_id > 0:
        client_service.change_client_admin(client_id, client_update.admin_id)

    # Get the final updated client
    final_client = client_service.get_client_by_id(client_id)
    return ClientView.from_client(final_client)


# DELETE - Delete client (soft delete)
@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete client",
    description="Delete a client account (soft delete). Requires authentication."
)
async def delete_client(
        client_id: int,
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Delete a client account (soft delete).

    - **client_id**: The client to delete
    """
    client_service = sf.get_client_service()
    client_service.remove_client_by_id(client_id)
    return None


# Change client status (enable/disable)
@router.post(
    "/{client_id}/status",
    response_model=ClientView,
    summary="Change client status",
    description="Change client enabled/disabled status. Requires authentication."
)
async def change_client_status(
        client_id: int,
        enabled: bool,
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Change a client's enabled/disabled status.

    - **client_id**: The client whose status to change
    - **enabled**: True to enable, False to disable
    """
    client_service = sf.get_client_service()
    updated_client = client_service.change_client_status(client_id, enabled)
    return ClientView.from_client(updated_client)


# Update client name
@router.patch(
    "/{client_id}/name",
    response_model=ClientView,
    summary="Update client name",
    description="Update client name. Requires authentication."
)
async def update_client_name(
        client_id: int,
        name: str,
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Update a client's name.

    - **client_id**: The client to update
    - **name**: New name
    """
    client_service = sf.get_client_service()
    updated_client = client_service.update_client_name(client_id, name)
    return ClientView.from_client(updated_client)


# Transfer client to another admin
@router.post(
    "/{client_id}/transfer",
    response_model=ClientView,
    summary="Transfer client",
    description="Transfer client to another admin. Requires authentication."
)
async def transfer_client(
        client_id: int,
        new_admin_id: int,
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Transfer a client to another admin.

    - **client_id**: The client to transfer
    - **new_admin_id**: The new admin ID
    """
    client_service = sf.get_client_service()
    updated_client = client_service.change_client_admin(client_id, new_admin_id)
    return ClientView.from_client(updated_client)


# Bulk operations
@router.post(
    "/bulk/enable",
    response_model=List[ClientView],
    summary="Enable all my clients",
    description="Enable all clients belonging to the current admin. Requires authentication."
)
async def enable_all_my_clients(
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Enable all clients belonging to the current admin.
    """
    client_service = sf.get_client_service()
    enabled_clients = client_service.enable_all_clients()
    return [ClientView.from_client(client) for client in enabled_clients]


@router.post(
    "/bulk/disable",
    response_model=List[ClientView],
    summary="Disable all my clients",
    description="Disable all clients belonging to the current admin. Requires authentication."
)
async def disable_all_my_clients(
        sf: ServiceFactory = Depends(get_service_factory_auth)
):
    """
    Disable all clients belonging to the current admin.
    """
    client_service = sf.get_client_service()
    disabled_clients = client_service.disable_all_clients()
    return [ClientView.from_client(client) for client in disabled_clients]


# ========== ERROR HANDLER ==========

@router.get("/error-test/{error_type}")
async def test_error_handling(error_type: str):
    """
    Test endpoint for error handling (development only).
    """
    error_map = {
        "not_found": ItemNotFoundError("Test client not found"),
        "security": DomainSecurityError("Test security error"),
        "operation": DomainOperationError("Test operation error"),
        "validation": ItemValidationError("Test validation error"),
        "exists": ItemAlreadyExistsError("Test already exists"),
    }

    if error_type in error_map:
        raise error_map[error_type]

    raise HTTPException(status_code=400, detail="Unknown error type")