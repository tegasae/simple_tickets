import uvicorn
from fastapi import FastAPI

from src.web.routers.auth import router as auth_router
#from src.web.routers.admin.clients import router as admin_clients_router
from src.web.routers.user.ticket import router as user_ticket_router


def create_app() -> FastAPI:
    app1 = FastAPI(title="Simple Tickets API")

    app1.include_router(auth_router)
    #app1.include_router(admin_clients_router)
    app1.include_router(user_ticket_router)

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
