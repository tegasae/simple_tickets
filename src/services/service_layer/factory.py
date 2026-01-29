# services/factory.py
from typing import TypeVar, Generic, Type

from src.services.service_layer.clients import ClientService
from src.services.uow.uowsqlite import AbstractUnitOfWork
from src.services.service_layer.admins import AdminService

#T = TypeVar('T')
ServiceType = TypeVar('ServiceType')






class ServiceFactory(Generic[ServiceType]):
    """
    Factory for creating and managing services
    Promotes dependency injection and testability
    """

    def __init__(self, uow: AbstractUnitOfWork, admin_name: str = ""):
        self.uow = uow
        self._services: dict[Type, ServiceType] = {}
        self.admin_name = admin_name  # Can be empty for public endpoints

    def get_admin_service(self) -> AdminService:
        """Get or create AdminService instance"""
        # Check if we need to create new service or update existing one
        need_new_service = False

        if AdminService not in self._services:
            need_new_service = True
        else:
            # Safely check if admin changed
            existing_service = self._services[AdminService]
            existing_admin = existing_service.requesting_admin

            if self.admin_name and (not existing_admin or existing_admin.name != self.admin_name):
                # Admin name changed (or wasn't set before)
                need_new_service = True
            elif not self.admin_name and existing_admin:
                # Was authenticated, now public - need new service
                need_new_service = True

        if need_new_service:
            self._services[AdminService] = AdminService(
                self.uow,
                requesting_admin_name=self.admin_name
            )

        return self._services[AdminService]

    def get_client_service(self) -> ClientService:
        """Get or create ClientService instance"""
        if ClientService not in self._services:
            self._services[ClientService] = ClientService(self.uow)
        return self._services[ClientService]

    def clear_cache(self):
        """Clear service cache (useful for testing)"""
        self._services.clear()