# tests/unit/services/test_factory.py
import pytest
from unittest.mock import Mock, create_autospec

from src.services.service_layer.factory import ServiceFactory
from src.services.service_layer.admins import AdminService
from src.services.uow.uowsqlite import AbstractUnitOfWork


class TestServiceFactory:
    """Test suite for ServiceFactory"""

    @pytest.fixture
    def mock_uow(self):
        """Mock Unit of Work"""
        return create_autospec(AbstractUnitOfWork)

    @pytest.fixture
    def factory(self, mock_uow):
        """ServiceFactory instance"""
        return ServiceFactory(uow=mock_uow)

    def test_initialization(self, factory, mock_uow):
        """Test ServiceFactory initialization"""
        assert factory.uow == mock_uow
        assert factory._services == {}

    def test_get_admin_service_creation(self, factory, mock_uow):
        """Test AdminService creation"""
        service = factory.get_admin_service()

        assert isinstance(service, AdminService)
        assert service.uow == mock_uow
        assert AdminService in factory._services

    def test_get_admin_service_caching(self, factory):
        """Test that AdminService is cached"""
        service1 = factory.get_admin_service()
        service2 = factory.get_admin_service()

        assert service1 is service2  # Same instance
        assert len(factory._services) == 1

    def test_clear_cache(self, factory):
        """Test clear_cache method"""
        # Create a service to populate cache
        factory.get_admin_service()
        assert len(factory._services) == 1

        # Clear cache
        factory.clear_cache()
        assert factory._services == {}

    def test_multiple_service_types(self, factory, mock_uow):
        """Test factory with multiple service types"""
        # This would test if you add more services later
        admin_service = factory.get_admin_service()

        assert len(factory._services) == 1
        assert factory._services[AdminService] is admin_service


