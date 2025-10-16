import logging
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException


import uvicorn
from starlette import status

from config import settings

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




# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Admin Management API with FastAPI",
    lifespan=lifespan
)

app.include_router(admins.router)

registry = ExceptionHandlerRegistry(app)
#registry.add_handler(
#    AdminAlreadyExistsError,
#    lambda request, exc: JSONResponse(status_code=409, content={"error": str(exc)})
#)

registry.add_all_handler('src.domain.exceptions',admins.handlers)
registry.register_all()




@app.get("/")
def root():
    return {"message": "Welcome to Admin Management API"}



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/info")
async def app_info():
    """Application information"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Admin Management System"
    }




@app.post("/create-db", status_code=status.HTTP_201_CREATED)
async def create_database():
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
