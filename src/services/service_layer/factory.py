# services/factory.py
from typing import Dict, Type, TypeVar
from src.services.uow.uowsqlite import AbstractUnitOfWork
from src.services.service_layer.admins import AdminService

T = TypeVar('T')


class ServiceFactory:
    """
    Factory for creating and managing services
    Promotes dependency injection and testability
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self._services: Dict[Type, T] = {}

    def get_admin_service(self) -> AdminService:
        """Get or create AdminService instance"""
        if AdminService not in self._services:
            self._services[AdminService] = AdminService(self.uow)
        return self._services[AdminService]

    def clear_cache(self):
        """Clear service cache (useful for testing)"""
        self._services.clear()
