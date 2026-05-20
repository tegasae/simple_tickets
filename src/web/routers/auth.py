from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.domain.account import Account
from src.web.dependencies.auth import create_access_token
from src.web.dependencies.services import get_uow

router = APIRouter(prefix="/auth_old", tags=["auth_old"])


def _verify_account_password(entity, plain_password: str) -> None:
    account = getattr(entity, "account", None)

    if not isinstance(account, Account):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )

    if not entity.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee is disabled",
        )

    if not account.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    if not account.verify_password(plain_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )


@router.post("/admin/login", response_model=None)
def admin_login(
    form: OAuth2PasswordRequestForm = Depends(),
    uow = Depends(get_uow),
):
    try:
        admin = uow.admins.find_by_login(login=form.username)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )

    _verify_account_password(admin, form.password)

    token = create_access_token(
        subject_id=admin.employee_id,
        subject_type="admin",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "subject_type": "admin",
        "subject_id": admin.employee_id,
    }


@router.post("/user/login", response_model=None)
def user_login(
    form: OAuth2PasswordRequestForm = Depends(),
    uow = Depends(get_uow),
):
    try:
        user = uow.users.find_by_login(login=form.username)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )

    _verify_account_password(user, form.password)

    token = create_access_token(
        subject_id=user.employee_id,
        subject_type="user",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "subject_type": "user",
        "subject_id": user.employee_id,
    }
