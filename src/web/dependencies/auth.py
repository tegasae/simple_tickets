from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from src.domain.exceptions import DomainError
from src.domain.policies.admin import AdminPolicy
from src.domain.policies.user import UserPolicy
from src.domain.uow.unit_of_work import UnitOfWork
from src.web.auth.exceptions import InvalidCredentialsError
from src.web.auth.services.auth_service import (
    AdminAuthService,
    UserAuthService,
)
from src.web.auth.services.services import TokenService
from src.web.auth.services.shared_sessions import SharedSessionAuthManager
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
) -> SharedSessionAuthManager:
    return SharedSessionAuthManager(
        uow=uow,
        auth_service=AdminAuthService(uow=uow),
        subject_type="admin",
        settings=settings

    )


def get_auth_manager_user(
    uow: UnitOfWork = Depends(get_uow),
    settings: Settings = Depends(get_settings),
) -> SharedSessionAuthManager:
    return SharedSessionAuthManager(
        uow=uow,
        auth_service=UserAuthService(uow=uow),
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
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    access_token = TokenService.verify_access_token(
        token,
        settings=settings,
    )

    employee_id = access_token.get_admin_id()
    try:
        state = uow.admins.get_login_state(admin_id=employee_id)
        AdminPolicy.ensure_login_state_is_valid(
            admin_enabled=state.admin_enabled,
            account_enabled=state.account_enabled,
        )
    except DomainError as exc:
        raise InvalidCredentialsError() from exc
    request.state.employee = EmployeeID(employee_id=employee_id)


def get_current_user(
    request: Request,
    token: str = Depends(user_oauth2_scheme),
    settings: Settings = Depends(get_settings),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    access_token = TokenService.verify_access_token(
        token,
        settings=settings,
    )

    employee_id = access_token.get_user_id()
    with uow:
        try:
            user = uow.users.get(user_id=employee_id)
            client = uow.clients.get(client_id=user.client_id)
            UserPolicy.ensure_login_is_still_valid(user=user, client=client)
        except DomainError as exc:
            raise InvalidCredentialsError() from exc
    request.state.employee = EmployeeID(employee_id=employee_id)


def get_employee_id_from_request(
    request: Request,
) -> int:
    return request.state.employee.employee_id
