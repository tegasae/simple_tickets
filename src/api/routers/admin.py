from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from ..dependencies import get_service_factory, get_current_admin
from ..models import AdminResponse, AdminCreate, AdminUpdate
from ...services.service_layer.data import CreateAdminData
from ...domain.model import AdminAbstract

router = APIRouter(prefix="/admins", tags=["admins"])


@router.post("/", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
        admin_data: AdminCreate,
        factory=Depends(get_service_factory),
        current_admin: AdminAbstract = Depends(get_current_admin)
):
    """Create a new admin"""
    try:
        admin_service = factory.get_admin_service()

        # Convert to service layer data
        create_data = CreateAdminData(
            name=admin_data.name,
            email=admin_data.email,
            password=admin_data.password,
            enabled=admin_data.enabled
        )

        admin = admin_service.execute('create', create_admin_data=create_data)

        return AdminResponse(
            admin_id=admin.admin_id,
            name=admin.name,
            email=admin.email,
            enabled=admin.enabled,
            date_created=admin.date_created
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[AdminResponse])
async def list_admins(
        enabled_only: bool = Query(False, description="Only return enabled admins"),
        factory=Depends(get_service_factory),
        current_admin: AdminAbstract = Depends(get_current_admin)
):
    """Get list of admins"""
    try:
        admin_service = factory.get_admin_service()

        if enabled_only:
            admins = admin_service.list_enabled_admins()
        else:
            admins = admin_service.list_all_admins()

        return [
            AdminResponse(
                admin_id=admin.admin_id,
                name=admin.name,
                email=admin.email,
                enabled=admin.enabled,
                date_created=admin.date_created
            )
            for admin in admins
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin(
        admin_id: int,
        factory=Depends(get_service_factory),
        current_admin: AdminAbstract = Depends(get_current_admin)
):
    """Get admin by ID"""
    try:
        admin_service = factory.get_admin_service()
        admin = admin_service.execute('get_by_id', admin_id=admin_id)

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        return AdminResponse(
            admin_id=admin.admin_id,
            name=admin.name,
            email=admin.email,
            enabled=admin.enabled,
            date_created=admin.date_created
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/name/{admin_name}", response_model=AdminResponse)
async def get_admin_by_name(
        admin_name: str,
        factory=Depends(get_service_factory),
        current_admin: AdminAbstract = Depends(get_current_admin)
):
    """Get admin by name"""
    try:
        admin_service = factory.get_admin_service()
        admin = admin_service.execute('get_by_name', name=admin_name)

        return AdminResponse(
            admin_id=admin.admin_id,
            name=admin.name,
            email=admin.email,
            enabled=admin.enabled,
            date_created=admin.date_created
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{admin_id}", response_model=AdminResponse)
async def update_admin(
        admin_id: int,
        admin_update: AdminUpdate,
        factory=Depends(get_service_factory),
        current_admin: AdminAbstract = Depends(get_current_admin)
):
    """Update admin information"""
    try:
        admin_service = factory.get_admin_service()

        # Get current admin to know the name
        admin = admin_service.execute('get_by_id', admin_id=admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        # Update email if provided
        if admin_update.email is not None:
            updated_admin = admin_service.execute(
                'update_email',
                name=admin.name,
                new_email=admin_update.email
            )

        # Update password if provided
        if admin_update.password is not None:
            updated_admin = admin_service.execute(
                'change_password',
                name=admin.name,
                new_password=admin_update.password
            )

        # Toggle status if provided
        if admin_update.enabled is not None:
            current_status = admin.enabled
            if admin_update.enabled != current_status:
                updated_admin = admin_service.execute('toggle_status', name=admin.name)

        # Get the final updated admin
        final_admin = admin_service.execute('get_by_id', admin_id=admin_id)

        return AdminResponse(
            admin_id=final_admin.admin_id,
            name=final_admin.name,
            email=final_admin.email,
            enabled=final_admin.enabled,
            date_created=final_admin.date_created
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
        admin_id: int,
        factory=Depends(get_service_factory),
        current_admin: AdminAbstract = Depends(get_current_admin)
):
    """Delete admin by ID"""
    try:
        admin_service = factory.get_admin_service()

        # Check if admin exists
        admin = admin_service.execute('get_by_id', admin_id=admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        # Prevent self-deletion
        if admin.admin_id == current_admin.admin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        admin_service.execute('remove_by_id', admin_id=admin_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{admin_name}/toggle-status", response_model=AdminResponse)
async def toggle_admin_status(
        admin_name: str,
        factory=Depends(get_service_factory),
        current_admin: AdminAbstract = Depends(get_current_admin)
):
    """Toggle admin enabled/disabled status"""
    try:
        admin_service = factory.get_admin_service()

        admin = admin_service.execute('toggle_status', name=admin_name)

        return AdminResponse(
            admin_id=admin.admin_id,
            name=admin.name,
            email=admin.email,
            enabled=admin.enabled,
            date_created=admin.date_created
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/check/{admin_name}/exists")
async def check_admin_exists(
        admin_name: str,
        factory=Depends(get_service_factory)
):
    """Check if admin exists (public endpoint)"""
    try:
        admin_service = factory.get_admin_service()
        exists = admin_service.admin_exists(admin_name)

        return {"exists": exists}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )