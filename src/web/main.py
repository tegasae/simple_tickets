import logging
import sqlite3
from contextlib import asynccontextmanager
from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import FastAPI, HTTPException, Depends

import uvicorn
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from pydantic import BaseModel
from starlette import status

from src.domain.model import Admin, AdminEmpty
from src.services.service_layer.factory import ServiceFactory
# from config import settings
from src.web.config import Settings, get_settings
from src.adapters.repositorysqlite import CreateDB
from src.web.dependicies import get_service_factory

from src.web.exception_handlers import ExceptionHandlerRegistry

from src.web.routers import admins

from utils.db.connect import Connection

logger = logging.getLogger(__name__)


ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting lifespan")
    yield
    print("Finishing lifespan")


# Dependency for settings
def get_app_settings() -> Settings:
    return get_settings()




class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt





async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],sf: ServiceFactory = Depends(get_service_factory)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},

    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    admin_service = sf.get_admin_service()
    admin = admin_service.execute('get_by_name', name=username)
    if admin is AdminEmpty:
        raise credentials_exception
    return admin



async def get_current_active_user(
    current_user: Annotated[Admin, Depends(get_current_user)],
):
    if not current_user.enabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user






# Create FastAPI app
app = FastAPI(
    title=get_app_settings().APP_NAME,
    version=get_app_settings().APP_VERSION,
    description="Admin Management API with FastAPI",
    lifespan=lifespan
)

app.include_router(admins.router)

registry = ExceptionHandlerRegistry(app)
# registry.add_handler(
#    AdminAlreadyExistsError,
#    lambda request, exc: JSONResponse(status_code=409, content={"error": str(exc)})
# )

registry.add_all_handler('src.domain.exceptions', admins.handlers)
registry.add_standard_handler(Exception,500)
registry.register_all()


@app.get("/")
def root():
    return {"message": "Welcome to Admin Management API"}


@app.get("/health")
async def health_check(settings: Settings = Depends(get_app_settings)):
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/info")
async def app_info(token: Annotated[str, Depends(oauth2_scheme)],settings: Settings = Depends(get_app_settings)):
    """Application information"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Admin Management System"
    }


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],sf: ServiceFactory = Depends(get_service_factory)
) -> Token:
    admin_service = sf.get_admin_service()
    admin = admin_service.execute('get_by_name', name=form_data.username)



    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.name}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")




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
