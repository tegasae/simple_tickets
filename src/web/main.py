import logging
import sqlite3
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends

import uvicorn
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from src.domain.model import Admin
from src.services.service_layer.factory import ServiceFactory

from src.web.config import Settings
from src.adapters.repositorysqlite import CreateDB
from src.web.dependicies import get_service_factory, get_app_settings
from src.web.dependicies_auth import Token, oauth2_scheme, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, \
    get_current_user, UserVerifier, get_user_verifier

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
    lifespan=lifespan
)

app.include_router(admins.router)

registry = ExceptionHandlerRegistry(app)

registry.add_all_handler('src.domain.exceptions', admins.handlers)
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


@app.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],user_verifier: UserVerifier = Depends(get_user_verifier)
) -> Token:
    username=form_data.username
    password=form_data.password

    return user_verifier(username=username,password=password)


@app.get("/users/me")
async def read_users_me(current_user: Annotated[Admin, Depends(get_current_user)]):
    return current_user


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
        log_level="info"
    )
