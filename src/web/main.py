import uvicorn
from fastapi import FastAPI

from src.domain.exceptions import ItemValidationError
from src.web.auth.exceptions import TokenError, TokenNotFoundError, TokenExpiredError, UserNotValidError, \
    InvalidCredentialsError
from src.web.execeptions.exception_handlers import ExceptionHandlerRegistry

from src.web.routers import admin
from src.web.routers.auth import router as auth_router
from src.web.routers.admin.clients import router as admin_clients_router
from src.web.routers.admin.admins import router as admin_admins_router


from src.web.routers.user.ticket import router as user_ticket_router


from src.web.routers.admin.users import router as admin_users_router
from src.web.routers.admin.tickets import router as admin_tickets_router





def create_app() -> FastAPI:
    app1 = FastAPI(title="Simple Tickets API")

    app1.include_router(auth_router)
    app1.include_router(admin_clients_router)
    app1.include_router(admin_admins_router)
    app1.include_router(user_ticket_router)
    app1.include_router(admin_users_router)
    app1.include_router(admin_tickets_router)
    registry = ExceptionHandlerRegistry(
        app1,
        log_error=True,
        with_traceback=False,
        expose_traceback=False,
        expose_error_type=True,
    )
    registry.add_all_standard_handlers(
        exceptions={
            TokenError: 401,
            TokenNotFoundError: 401,
            TokenExpiredError: 401,
            UserNotValidError: 401,
            InvalidCredentialsError: 401,
            ItemValidationError: 400,
            PermissionError: 403
        }
    )
    registry.add_all_handlers_from_module(
        module_name="src.domain.exceptions",
        exceptions=admin.clients.handlers,
    )



    registry.add_standard_handler(
        exception_type=Exception,
        status_code=500
    )

    registry.register_all()

    @app1.get("/health", response_model=None)
    def health_check():
        return {"status": "ok"}

    return app1


app = create_app()
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info",
        workers=4
    )
