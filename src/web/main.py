import uvicorn
from fastapi import FastAPI

from src.adapters.repositories.exceptions import NotFoundError as RepositoryNotFoundError
from src.adapters.repositories.exceptions import OptimisticLockError
from src.application.exceptions import ApplicationValidateError
from src.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DomainOperationError,
    ItemAlreadyExistsError,
    ItemNotFoundError,
    ItemValidationError,
)
from src.web.auth.exceptions import AuthError, AuthPermissionError
from src.web.execeptions.exception_handlers import ExceptionHandlerRegistry

from src.web.routers import admin
from src.web.routers.auth import router as auth_router
from src.web.routers.admin.clients import router as admin_clients_router
from src.web.routers.admin.admins import router as admin_admins_router
from src.web.routers.admin.departments import router as admin_departments_router


from src.web.routers.user.tickets import router as user_ticket_router


from src.web.routers.admin.users import router as admin_users_router
from src.web.routers.admin.tickets import router as admin_tickets_router
from src.web.routers.admin.roles import router as admin_roles_router

from src.web.auth.storage import TokenStorageMemory
from src.web.auth.storage_sqlite import TokenStorageSQLite
from src.web.config import Settings


def create_app() -> FastAPI:
    #settings=get_settings()
    settings = Settings()

    app1 = FastAPI(title=settings.APP_NAME)
    # noinspection PyUnresolvedReferences
    app1.state.settings = settings
    if settings.REFRESH_TOKEN_BACKEND == "sqlite":
        path = settings.REFRESH_TOKEN_SQLITE_PATH
        if path is None:
            raise ValueError("Configure REFRESH_TOKEN_SQLITE_PATH")
        app1.state.refresh_token_storage = TokenStorageSQLite(path)
    else:
        app1.state.refresh_token_storage = TokenStorageMemory()

    app1.include_router(auth_router)
    app1.include_router(admin_clients_router)
    app1.include_router(admin_admins_router)
    app1.include_router(user_ticket_router)
    app1.include_router(admin_users_router)
    app1.include_router(admin_tickets_router)
    app1.include_router(admin_departments_router)
    app1.include_router(admin_roles_router)
    registry = ExceptionHandlerRegistry(
        app1,
        log_error=True,
        with_traceback=False,
        expose_traceback=False,
        expose_error_type=True,
    )

    registry.add_all_standard_handlers(
        exceptions={
            AuthPermissionError: 403,
            ApplicationValidateError: 400,
            AuthenticationError: 401,
            AuthorizationError: 403,
            PermissionError: 403,
            ItemValidationError: 400,
            DomainOperationError: 400,
            ItemAlreadyExistsError: 409,
            OptimisticLockError: 409,
            ItemNotFoundError: 404,
            RepositoryNotFoundError: 404,
        }
    )
    registry.add_standard_handler(
        exception_type=AuthError,
        status_code=401,
        public_detail="Invalid credentials or session",
    )
    registry.add_standard_handler(
        exception_type=Exception,
        status_code=500,
        public_detail="Internal server error",
    )

    registry.register_all()

    @app1.get("/health", response_model=None)
    def health_check():
        return {"status": "ok"}

    return app1


app = create_app()
if __name__ == "__main__":
    uvicorn.run(
        "src.web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development entry point, with process-local sessions.
        log_level="info",
    )
