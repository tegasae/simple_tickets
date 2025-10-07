import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List
import logging

from src.services.service_layer.admins import AdminService
from src.services.service_layer.data import CreateAdminData
from src.services.service_layer.base import BaseService
from src.services.service_layer.factory import ServiceFactory
from src.services.uow.uowsqlite import AbstractUnitOfWork
from src.domain.model import Admin, AdminsAggregate, AdminAbstract, AdminEmpty
from src.adapters.repository import AdminRepositoryAbstract


class TestAdminService:
    """Tests for AdminService functionality"""

    @pytest.fixture
    def mock_uow(self):
        """Create a mock Unit of Work"""
        uow = Mock(spec=AbstractUnitOfWork)
        uow.admins = Mock(spec=AdminRepositoryAbstract)
        return uow

    @pytest.fixture
    def mock_aggregate(self):
        """Create a mock AdminsAggregate"""
        aggregate = Mock(spec=AdminsAggregate)
        aggregate.admins = {}
        aggregate.version = 0
        return aggregate

    @pytest.fixture
    def admin_service(self, mock_uow):
        """Create AdminService with mocked UoW"""
        return AdminService(mock_uow)

    @pytest.fixture
    def sample_admin_data(self):
        """Sample admin data for testing"""
        return CreateAdminData(
            name="testadmin",
            password="securepassword123",
            email="test@example.com",
            enabled=True
        )

    @pytest.fixture
    def sample_admin(self):
        """Create a sample Admin instance"""
        return Admin(
            admin_id=1,
            name="testadmin",
            password="hashed_password",
            email="test@example.com",
            enabled=True
        )

    def test_initialization(self, mock_uow):
        """Test that AdminService initializes correctly"""
        service = AdminService(mock_uow)

        assert service.uow == mock_uow
        assert isinstance(service, BaseService)
        assert hasattr(service, 'logger')

    def test_execute_valid_operation(self, admin_service, sample_admin_data):
        """Test execute method with valid operation"""
        with patch.object(admin_service, '_create_admin') as mock_create:
            mock_create.return_value = Mock(spec=Admin)

            result = admin_service.execute('create', create_admin_data=sample_admin_data)

            mock_create.assert_called_once_with(sample_admin_data)
            assert result == mock_create.return_value

    def test_execute_invalid_operation(self, admin_service):
        """Test execute method with invalid operation"""
        with pytest.raises(ValueError, match="Unknown operation: invalid_op"):
            admin_service.execute('invalid_op', name="test")

    def test_execute_missing_parameters(self, admin_service):
        """Test execute method with missing parameters"""
        with pytest.raises(ValueError, match="Parameter 'operation' cannot be None"):
            admin_service.execute(None)

    def test_create_admin_success(self, admin_service, mock_uow, mock_aggregate, sample_admin_data, sample_admin):
        """Test successful admin creation"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = False
        mock_aggregate.create_admin.return_value = sample_admin
        mock_aggregate.get_admin_by_name.return_value = sample_admin

        # Mock the context manager behavior
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service._create_admin(sample_admin_data)

        # Assertions
        mock_aggregate.admin_exists.assert_called_once_with("testadmin")
        mock_aggregate.create_admin.assert_called_once_with(
            admin_id=0,
            name="testadmin",
            email="test@example.com",
            password="securepassword123",
            enabled=True
        )
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()
        assert result == sample_admin

    def test_create_admin_already_exists(self, admin_service, mock_uow, mock_aggregate, sample_admin_data):
        """Test admin creation when admin already exists"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = True

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute and assert
        with pytest.raises(ValueError, match="Admin with name 'testadmin' already exists"):
            admin_service._create_admin(sample_admin_data)

        # Ensure save and commit were NOT called
        mock_uow.admins.save_admins.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_create_admin_id_not_generated(self, admin_service, mock_uow, mock_aggregate, sample_admin_data):
        """Test admin creation when ID is not properly generated"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = False

        admin_with_zero_id = Mock(spec=Admin)
        admin_with_zero_id.admin_id = 0

        mock_aggregate.create_admin.return_value = admin_with_zero_id
        mock_aggregate.get_admin_by_name.return_value = admin_with_zero_id

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute and assert
        with pytest.raises(ValueError, match="Admin was created but ID wasn't properly generated"):
            admin_service._create_admin(sample_admin_data)

    def test_get_admin_by_name_success(self, admin_service, mock_uow, mock_aggregate, sample_admin):
        """Test successful admin retrieval by name"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.require_admin_by_name.return_value = sample_admin

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service._get_admin_by_name("testadmin")

        # Assertions
        mock_aggregate.require_admin_by_name.assert_called_once_with("testadmin")
        assert result == sample_admin

    def test_update_admin_email_success(self, admin_service, mock_uow, mock_aggregate, sample_admin):
        """Test successful admin email update"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = True
        mock_aggregate.require_admin_by_name.return_value = sample_admin

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service._update_admin_email("testadmin", "new@example.com")

        # Assertions
        mock_aggregate.admin_exists.assert_called_once_with("testadmin")
        mock_aggregate.change_admin_email.assert_called_once_with("testadmin", "new@example.com")
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()
        assert result == sample_admin

    def test_update_admin_email_not_found(self, admin_service, mock_uow, mock_aggregate):
        """Test email update when admin doesn't exist"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = False

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute and assert
        with pytest.raises(ValueError, match="Admin 'nonexistent' not found"):
            admin_service._update_admin_email("nonexistent", "new@example.com")

        mock_uow.admins.save_admins.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_toggle_admin_status_success(self, admin_service, mock_uow, mock_aggregate, sample_admin):
        """Test successful admin status toggle"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.require_admin_by_name.return_value = sample_admin

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service._toggle_admin_status("testadmin")

        # Assertions
        mock_aggregate.require_admin_by_name.assert_called_with("testadmin")
        mock_aggregate.toggle_admin_status.assert_called_once_with("testadmin")
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()
        assert result == sample_admin

    def test_change_admin_password_success(self, admin_service, mock_uow, mock_aggregate, sample_admin):
        """Test successful password change"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = True
        mock_aggregate.require_admin_by_name.return_value = sample_admin

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service._change_admin_password("testadmin", "newpassword123")

        # Assertions
        mock_aggregate.admin_exists.assert_called_once_with("testadmin")
        mock_aggregate.change_admin_password.assert_called_once_with("testadmin", "newpassword123")
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()
        assert result == sample_admin

    def test_change_admin_password_not_found(self, admin_service, mock_uow, mock_aggregate):
        """Test password change when admin doesn't exist"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = False

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute and assert
        with pytest.raises(ValueError, match="Admin 'nonexistent' not found"):
            admin_service._change_admin_password("nonexistent", "newpassword")

        mock_uow.admins.save_admins.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_list_all_admins(self, admin_service, mock_uow, mock_aggregate, sample_admin):
        """Test listing all admins"""
        # Setup mocks
        mock_admins = [sample_admin, Mock(spec=Admin)]
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_all_admins.return_value = mock_admins

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service.list_all_admins()

        # Assertions
        mock_aggregate.get_all_admins.assert_called_once()
        assert result == mock_admins

    def test_list_enabled_admins(self, admin_service, mock_uow, mock_aggregate, sample_admin):
        """Test listing enabled admins"""
        # Setup mocks
        mock_enabled_admins = [sample_admin]
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_enabled_admins.return_value = mock_enabled_admins

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service.list_enabled_admins()

        # Assertions
        mock_aggregate.get_enabled_admins.assert_called_once()
        assert result == mock_enabled_admins

    def test_admin_exists_true(self, admin_service, mock_uow, mock_aggregate):
        """Test admin_exists when admin exists"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = True

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service.admin_exists("testadmin")

        # Assertions
        mock_aggregate.admin_exists.assert_called_once_with("testadmin")
        assert result is True

    def test_admin_exists_false(self, admin_service, mock_uow, mock_aggregate):
        """Test admin_exists when admin doesn't exist"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = False

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service.admin_exists("nonexistent")

        # Assertions
        mock_aggregate.admin_exists.assert_called_once_with("nonexistent")
        assert result is False


class TestAdminServiceErrorHandling:
    """Tests for error handling in AdminService"""

    @pytest.fixture
    def admin_service(self):
        """Create AdminService with mocked UoW"""
        mock_uow = Mock(spec=AbstractUnitOfWork)
        mock_uow.admins = Mock(spec=AdminRepositoryAbstract)
        return AdminService(mock_uow)

    def test_create_admin_unexpected_error(self, admin_service, sample_admin_data):
        """Test handling of unexpected errors during admin creation"""
        with patch.object(admin_service, '_log_operation'):
            with patch.object(admin_service.uow, '__enter__') as mock_enter:
                mock_enter.side_effect = Exception("Database connection failed")

                with pytest.raises(RuntimeError, match="Failed to create admin"):
                    admin_service._create_admin(sample_admin_data)

    def test_create_admin_value_error_logging(self, admin_service, mock_uow, mock_aggregate, sample_admin_data, caplog):
        """Test that ValueErrors are properly logged"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = True

        admin_service.uow = mock_uow

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute with logging check
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                admin_service._create_admin(sample_admin_data)

            assert "Failed to create admin" in caplog.text


class TestCreateAdminData:
    """Tests for CreateAdminData data class"""

    def test_create_admin_data_initialization(self):
        """Test CreateAdminData initialization"""
        data = CreateAdminData(
            name="testadmin",
            password="password123",
            email="test@example.com",
            enabled=True
        )

        assert data.name == "testadmin"
        assert data.password == "password123"
        assert data.email == "test@example.com"
        assert data.enabled is True

    def test_create_admin_data_default_enabled(self):
        """Test that enabled defaults to True"""
        data = CreateAdminData(
            name="testadmin",
            password="password123",
            email="test@example.com"
        )

        assert data.enabled is True

    def test_create_admin_data_frozen(self):
        """Test that CreateAdminData is immutable"""
        data = CreateAdminData(
            name="testadmin",
            password="password123",
            email="test@example.com"
        )

        with pytest.raises(Exception):  # Should be frozen/dataclass error
            data.name = "newname"

    def test_create_admin_data_kw_only(self):
        """Test that CreateAdminData requires keyword arguments"""
        with pytest.raises(TypeError):
            CreateAdminData("testadmin", "password123", "test@example.com")  # Positional args should fail


class TestServiceFactory:
    """Tests for ServiceFactory"""

    @pytest.fixture
    def mock_uow(self):
        return Mock(spec=AbstractUnitOfWork)

    @pytest.fixture
    def service_factory(self, mock_uow):
        return ServiceFactory(mock_uow)

    def test_get_admin_service(self, service_factory, mock_uow):
        """Test getting AdminService from factory"""
        service1 = service_factory.get_admin_service()
        service2 = service_factory.get_admin_service()

        assert isinstance(service1, AdminService)
        assert service1.uow == mock_uow
        assert service1 is service2  # Should return same instance (cached)

    def test_clear_cache(self, service_factory, mock_uow):
        """Test clearing service cache"""
        service1 = service_factory.get_admin_service()
        service_factory.clear_cache()
        service2 = service_factory.get_admin_service()

        assert service1 is not service2  # Should be different instances after clear


# Test configuration
pytestmark = pytest.mark.unit


def test_imports():
    """Test that all required imports are available"""
    from src.services.service_layer.admins import AdminService
    from src.services.service_layer.data import CreateAdminData
    from src.services.service_layer.base import BaseService
    from src.services.service_layer.factory import ServiceFactory

    assert AdminService is not None
    assert CreateAdminData is not None
    assert BaseService is not None
    assert ServiceFactory is not None