import logging
import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends

import uvicorn
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from src.web.auth.services import AuthManager

from src.web.config import Settings
from src.adapters.repositorysqlite import CreateDB
from src.web.dependicies.dependencies import get_app_settings
from src.web.dependicies.dependicies_auth import oauth2_scheme, \
    get_auth_manager, get_current_user_new
from src.web.auth.models import RefreshRequest, LogoutRequest

from src.web.exception_handlers import ExceptionHandlerRegistry

from src.web.routers import admins

from utils.db.connect import Connection

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting lifespan")
    yield
    print("Finishing lifespan")


# Create FastAPI app
app = FastAPI(
    title=get_app_settings().APP_NAME,
    version=get_app_settings().APP_VERSION,
    description="Admin Management API with FastAPI",
    lifespan=lifespan,

)


app.include_router(admins.router)
# LoggingMiddleware(app)
registry = ExceptionHandlerRegistry(app)

registry.add_all_handler('src.domain.exceptions', admins.handlers)
registry.add_all_handler('src.web.auth.exceptions', {'TokenError': 401, 'TokenNotFoundError': 401,
                                                     'TokenExpiredError': 401, 'UserNotValidError': 401})
registry.add_standard_handler(Exception, 500)
registry.register_all()


@app.get("/")
def root():
    return {"message": "Welcome to Admin Management API"}


@app.get("/health")
async def health_check(settings: Settings = Depends(get_app_settings)):
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/info")
async def app_info(token: Annotated[str, Depends(oauth2_scheme)], settings: Settings = Depends(get_app_settings)):
    """Application information"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Admin Management System"
    }


@app.get("/info1")
async def app_info1(username: str = Depends(get_current_user_new), settings: Settings = Depends(get_app_settings)):
    """Application information"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Admin Management System"
    }


@app.post("/token")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        auth_manager: AuthManager = Depends(get_auth_manager)
):
    #
    scopes = form_data.scopes if form_data.scopes else []
    return auth_manager.login(form_data.username, form_data.password, scopes)


@app.post("/refresh")
async def refresh(
        refresh_request: RefreshRequest,
        auth_manager: AuthManager = Depends(get_auth_manager)
):
    return auth_manager.refresh(refresh_request.refresh_token)


@app.post("/logout")
async def logout(
        logout_request: LogoutRequest,
        auth_manager: AuthManager = Depends(get_auth_manager)
):
    auth_manager.logout(refresh_token_id=logout_request.refresh_token)
    return {"message": "Logged out successfully"}


@app.get("/users/me")
async def read_current_user(
        username: str = Depends(get_current_user_new)
):
    return {"username": username}


@app.post("/create-db", status_code=status.HTTP_201_CREATED)
async def create_database(settings: Settings = Depends(get_app_settings)):
    """
    Initialize the database schema and tables.

    This endpoint creates the necessary database tables for the admin system.
    """
    try:
        # Create database connection
        conn = Connection.create_connection(url=settings.DATABASE_URL, engine=sqlite3)

        # Initialize database schema
        create_db = CreateDB(conn)
        create_db.init_data()
        create_db.create_indexes()

        conn.close()

        return {
            "message": "Database created successfully",
            "database_file": "admins.db",
            "tables_created": ["admins_aggregate", "admins"],
            "indexes_created": ["idx_admins_name", "idx_admins_email", "idx_admins_enabled"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create database: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info",
        workers=4
    )
