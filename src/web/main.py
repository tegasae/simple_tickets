import logging
import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends

import uvicorn
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette import status

# from config import settings
from src.web.config import Settings, get_settings
from src.adapters.repositorysqlite import CreateDB

from src.web.exception_handlers import ExceptionHandlerRegistry

from src.web.routers import admins

from utils.db.connect import Connection

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting lifespan")
    yield
    print("Finishing lifespan")


# Dependency for settings
def get_app_settings() -> Settings:
    return get_settings()


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": False,
    },
}



def fake_hash_password(password: str):
    return "fakehashed" + password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
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
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}




@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
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
