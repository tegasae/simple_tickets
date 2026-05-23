from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.domain.account import Account
from src.web.auth.models import RefreshRequest, LogoutRequest, LoginRequest
from src.web.auth.services.services import AuthManager

from src.web.dependencies.auth import get_auth_manager_admin, get_auth_manager_user

router = APIRouter(prefix="/auth", tags=["auth"])


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


#@router.post("/admin/login", response_model=None)
#def admin_login(
#    form: OAuth2PasswordRequestForm = Depends(),
#    uow = Depends(get_uow),
#):
#    try:
#        admin = uow.admins.find_by_login(login=form.username)
#    except Exception:
#        raise HTTPException(
#            status_code=status.HTTP_401_UNAUTHORIZED,
#            detail="Invalid login or password",
#        )
#
#    _verify_account_password(admin, form.password)
#
#    token = create_access_token(
#        subject_id=admin.employee_id,
#        subject_type="admin",
#    )
#
#    return {
#        "access_token": token,
#        "token_type": "bearer",
#        "subject_type": "admin",
#        "subject_id": admin.employee_id,
#    }



####
@router.post("/admin/login")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        auth_manager: AuthManager = Depends(get_auth_manager_admin)
):
    #
    scopes = form_data.scopes if form_data.scopes else []
    login_request = LoginRequest(username=form_data.username, password=form_data.password, scope=scopes)
    return auth_manager.login(login_request=login_request)


@router.post("/admin/refresh")
async def refresh(
        refresh_request: RefreshRequest,
        auth_manager: AuthManager = Depends(get_auth_manager_admin)
):
    refresh_request = RefreshRequest(refresh_token=refresh_request.refresh_token)
    return auth_manager.refresh(refresh_request=refresh_request)


@router.post("/admin/logout")
async def logout(
        auth_manager: AuthManager = Depends(get_auth_manager_admin)
):
    logout_request=LogoutRequest()
    auth_manager.logout(logout_request=logout_request)
    return {"message": "Logged out successfully"}




@router.post("/user/login")
async def login_user(
        form_data: OAuth2PasswordRequestForm = Depends(),
        auth_manager: AuthManager = Depends(get_auth_manager_user)
):
    #
    scopes = form_data.scopes if form_data.scopes else []
    login_request = LoginRequest(username=form_data.username, password=form_data.password, scope=scopes)
    return auth_manager.login(login_request=login_request)


@router.post("/user/refresh")
async def refresh_user(
        refresh_request: RefreshRequest,
        auth_manager: AuthManager = Depends(get_auth_manager_user)
):
    refresh_request = RefreshRequest(refresh_token=refresh_request.refresh_token)
    return auth_manager.refresh(refresh_request=refresh_request)


@router.post("/user/logout")
async def logout(
        logout_request: LogoutRequest,
        auth_manager: AuthManager = Depends(get_auth_manager_user)
):

    auth_manager.logout(logout_request=logout_request)
    return {"message": "Logged out successfully"}




#@router.post("/user/login", response_model=None)
#def user_login(
#    form: OAuth2PasswordRequestForm = Depends(),
#    uow = Depends(get_uow),
#):
#    try:
#        user = uow.users.find_by_login(login=form.username)
#    except Exception:
#        raise HTTPException(
#            status_code=status.HTTP_401_UNAUTHORIZED,
#            detail="Invalid login or password",
#        )

#    _verify_account_password(user, form.password)
#
#    token = create_access_token(
#        subject_id=user.employee_id,
#        subject_type="user",
#    )

#    return {
#        "access_token": token,
#        "token_type": "bearer",
#        "subject_type": "user",
#        "subject_id": user.employee_id,
#    }
