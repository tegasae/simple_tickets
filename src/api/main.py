from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uvicorn

from config import settings
from routers import admin
from dependencies import get_db_connection
from src.adapters.repositorysqlite import CreateDB

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Admin Management API with FastAPI"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        # Create database connection
        conn = Connection.create_connection(url="admins.db", engine=sqlite3)

        # Initialize database schema
        create_db = CreateDB(conn=conn)
        create_db.init_data()
        create_db.create_indexes()

        print("Database initialized successfully")
        conn.close()

    except Exception as e:
        print(f"Database initialization failed: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION
    }


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