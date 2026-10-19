from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from src.domain.uow.unit_of_work import UnitOfWork
from src.web.auth.services.auth_service import (
    AdminAuthService,
    UserAuthService,
)
from src.web.auth.services.services import AuthManager, TokenService
from src.web.auth.storage import TokenStorageMemory
from src.web.auth.tokens import AccessToken
from src.web.config import Settings
from src.web.dependencies.scheme import (
    admin_oauth2_scheme,
    user_oauth2_scheme,
)
from src.web.dependencies.services import (
    get_settings,
    get_uow,
)


# ---------------------------------------------------------------------
# Token storages
# ---------------------------------------------------------------------
#
# Storage must not be created inside get_auth_manager_*(),
# otherwise every request receives a new empty storage.
#
# Admin and User authentication are intentionally separate.
#

_admin_token_storage = TokenStorageMemory()
_user_token_storage = TokenStorageMemory()


# ---------------------------------------------------------------------
# Token principals
# ---------------------------------------------------------------------

def get_current_admin_principal(
    token: str = Depends(admin_oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    access_token = AccessToken.decode(
        token,
        settings=settings,
    )

    return access_token.to_payload()


def get_current_user_principal(
    token: str = Depends(user_oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    access_token = AccessToken.decode(
        token,
        settings=settings,
    )

    return access_token.to_payload()


def require_current_admin(
    payload: dict[str, Any] = Depends(get_current_admin_principal),
) -> int:
    if payload.get("subject_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return int(payload["sub"])


def require_current_user(
    payload: dict[str, Any] = Depends(get_current_user_principal),
) -> int:
    if payload.get("subject_type") != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required",
        )

    return int(payload["sub"])


# ---------------------------------------------------------------------
# Auth managers
# ---------------------------------------------------------------------

def get_auth_manager_admin(
    uow: UnitOfWork = Depends(get_uow),
    settings: Settings = Depends(get_settings),
) -> AuthManager:
    return AuthManager(
        auth_service=AdminAuthService(uow=uow),
        token_storage=_admin_token_storage,
        subject_type="admin",
        settings=settings

    )


def get_auth_manager_user(
    uow: UnitOfWork = Depends(get_uow),
    settings: Settings = Depends(get_settings),
) -> AuthManager:
    return AuthManager(
        auth_service=UserAuthService(uow=uow),
        token_storage=_user_token_storage,
        subject_type="user",
        settings = settings
    )


# ---------------------------------------------------------------------
# Authenticated employee
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EmployeeID:
    employee_id: int


def get_current_admin(
    request: Request,
    token: str = Depends(admin_oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> None:
    access_token = TokenService.verify_access_token(
        token,
        settings=settings,
    )

    request.state.employee = EmployeeID(
        employee_id=access_token.get_admin_id(),
    )


def get_current_user(
    request: Request,
    token: str = Depends(user_oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> None:
    access_token = TokenService.verify_access_token(
        token,
        settings=settings,
    )

    request.state.employee = EmployeeID(
        employee_id=access_token.get_user_id(),
    )


def get_employee_id_from_request(
    request: Request,
) -> int:
    return request.state.employee.employee_id
