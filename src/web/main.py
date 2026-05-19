from fastapi import FastAPI

from src.web.routers.auth import router as auth_router
from src.web.routers.admin.clients import router as admin_clients_router
from src.web.routers.user.ticket import router as user_ticket_router


def create_app() -> FastAPI:
    app = FastAPI(title="Simple Tickets API")

    app.include_router(auth_router)
    app.include_router(admin_clients_router)
    app.include_router(user_ticket_router)

    @app.get("/health", response_model=None)
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
