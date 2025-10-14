from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException

import uvicorn

from config import settings

from src.services.service_layer.factory import ServiceFactory

from src.web.models import AdminView
from src.web.routers import admins


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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
