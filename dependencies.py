from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import sqlite3

from config import settings
from src.services.service_layer.factory import ServiceFactory  # Fixed import
from src.services.uow.uowsqlite import SqliteUnitOfWork  # Add this import
from utils.db.connect import Connection

# Security
security = HTTPBearer()


def get_db_connection():
    """Get database connection"""
    conn = None
    try:
        conn = Connection.create_connection(
            url="admins.db",  # Fixed path
            engine=sqlite3
        )
        yield conn
    finally:
        if conn:
            conn.close()


def get_uow(conn: Connection = Depends(get_db_connection)):
    """Get Unit of Work"""
    return SqliteUnitOfWork(connection=conn)


def get_service_factory(uow: SqliteUnitOfWork = Depends(get_uow)):
    """Get service factory"""
    return ServiceFactory(uow=uow)


def get_current_admin(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        factory: ServiceFactory = Depends(get_service_factory)
):
    """Get current admin from token"""
    # This is a simplified version - in production, use JWT tokens
    token = credentials.credentials
    admin_service = factory.get_admin_service()

    try:
        # Simple token validation - in real app, decode JWT
        admin_name = token  # Using token as admin name for demo
        admin = admin_service.execute('get_by_name', name=admin_name)
        if not admin or not admin.enabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return admin
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
