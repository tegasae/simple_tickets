from fastapi.security import OAuth2PasswordBearer

admin_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/admin/login",
    scheme_name="AdminAuth",
)

user_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/user/login",
    scheme_name="UserAuth",
)
