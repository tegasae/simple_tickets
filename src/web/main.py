import sqlite3
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException

import uvicorn

from config import settings
from routers import admins
from src.services.service_layer.factory import ServiceFactory
from src.services.uow.uowsqlite import SqliteUnitOfWork
from src.web.models import AdminView
from tests.intergrated.test_admin_service_integration import admin_service
from utils.db.connect import Connection  # Add this import
from src.adapters.repositorysqlite import CreateDB  # Fixed import path

@asynccontextmanager
async def lifespan(app: FastAPI):
    #conn = Connection.create_connection(url="admins.db", engine=sqlite3)
    #create_db = CreateDB(conn)
    #create_db.init_data()
    #create_db.create_indexes()
    #conn.close()
    print("Starting lifespan")
    yield
    print("Finishing lifespan")


def get_db_connection():
    """Create connection in the same thread that uses it"""
    conn = None
    try:
        # This will be called in the worker thread
        conn = Connection.create_connection(url=settings.DATABASE_URL, engine=sqlite3)
        yield conn
    finally:
        if conn:
            conn.close()

# The rest of your dependencies stay the same
def get_uow(conn: Connection = Depends(get_db_connection)):
    return SqliteUnitOfWork(connection=conn)

def get_service_factory(uow: SqliteUnitOfWork = Depends(get_uow)):
    return ServiceFactory(uow=uow)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Admin Management API with FastAPI",
    lifespan=lifespan
)

app.include_router(admins.router)




@app.get("/")
async def root(sf: ServiceFactory = Depends(get_service_factory)):
    admin_service = sf.get_admin_service()
    all_admins = admin_service.list_all_admins()
    admins_view:List[AdminView]=[]
    for admin in all_admins:
        admins_view.append(AdminView(admin_id=admin.admin_id,name=admin.name,email=admin.email,enabled=admin.enabled,date_created=admin.date_created))
    return {"admins": admins_view}


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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
