import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List
import logging

from src.services.service_layer.admins import AdminService
from src.services.service_layer.data import CreateAdminData
from src.services.service_layer.base import BaseService
from src.services.uow.uowsqlite import AbstractUnitOfWork
from src.adapters.repository import AdminRepositoryAbstract
from src.domain.model import Admin, AdminsAggregate, AdminEmpty


@pytest.fixture
def mock_uow():
    """Create a mock Unit of Work"""
    uow = Mock(spec=AbstractUnitOfWork)
    uow.admins = Mock(spec=AdminRepositoryAbstract)
    return uow


class TestAdminService:
    """Comprehensive unit tests for AdminService"""


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

    @pytest.fixture
    def another_admin(self):
        """Create another sample Admin instance"""
        return Admin(
            admin_id=2,
            name="anotheradmin",
            password="anotherpassword",
            email="another@example.com",
            enabled=False
        )

    # ==================== EXECUTE METHOD TESTS ====================

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

    # ==================== CREATE ADMIN TESTS ====================

    def test_create_admin_success(self, admin_service, mock_uow, mock_aggregate, sample_admin_data, sample_admin):
        """Test successful admin creation"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = False
        mock_aggregate.create_admin.return_value = sample_admin

        # Mock context manager behavior
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Mock _get_admin_by_name to return the created admin with ID
        with patch.object(admin_service, '_get_admin_by_name') as mock_get:
            mock_get.return_value = sample_admin

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
            mock_get.assert_called_once_with("testadmin")
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

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Mock _get_admin_by_name to return admin with zero ID
        with patch.object(admin_service, '_get_admin_by_name') as mock_get:
            mock_get.return_value = admin_with_zero_id

            # Execute and assert
            with pytest.raises(ValueError, match="Admin was created but ID wasn't properly generated"):
                admin_service._create_admin(sample_admin_data)

    # ==================== GET ADMIN TESTS ====================

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

    def test_get_admin_by_id_success(self, admin_service, mock_uow, mock_aggregate, sample_admin):
        """Test successful admin retrieval by ID"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_all_admins.return_value = [sample_admin]

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service._get_admin_by_id(1)

        # Assertions
        mock_aggregate.get_all_admins.assert_called_once()
        assert result == sample_admin

    def test_get_admin_by_id_not_found(self, admin_service, mock_uow, mock_aggregate):
        """Test admin retrieval by ID when admin doesn't exist"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_all_admins.return_value = []

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute and assert
        with pytest.raises(ValueError, match="Admin with ID 999 not found"):
            admin_service._get_admin_by_id(999)

    def test_find_admin_by_id_success(self, admin_service, mock_aggregate, sample_admin):
        """Test _find_admin_by_id helper method when admin is found"""
        # Setup mock aggregate with admins
        mock_admins = [sample_admin]
        mock_aggregate.get_all_admins.return_value = mock_admins

        # Execute
        result = admin_service._find_admin_by_id(1, mock_aggregate)

        # Assertions
        assert result == sample_admin
        mock_aggregate.get_all_admins.assert_called_once()

    def test_find_admin_by_id_not_found(self, admin_service, mock_aggregate):
        """Test _find_admin_by_id helper method when admin is not found"""
        # Setup mock aggregate with no admins
        mock_aggregate.get_all_admins.return_value = []

        # Execute and assert
        with pytest.raises(ValueError, match="Admin with ID 999 not found in aggregate"):
            admin_service._find_admin_by_id(999, mock_aggregate)

    # ==================== UPDATE ADMIN TESTS ====================

    def test_update_admin_email_success(self, admin_service, mock_uow, mock_aggregate, sample_admin):
        """Test successful admin email update"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.require_admin_by_name.return_value = sample_admin

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service._update_admin_email("testadmin", "new@example.com")

        # Assertions
        mock_aggregate.require_admin_by_name.assert_called_with("testadmin")
        mock_aggregate.change_admin_email.assert_called_once_with("testadmin", "new@example.com")
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()
        assert result == sample_admin

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
        mock_aggregate.require_admin_by_name.return_value = sample_admin

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        result = admin_service._change_admin_password("testadmin", "newpassword123")

        # Assertions
        mock_aggregate.require_admin_by_name.assert_called_with("testadmin")
        mock_aggregate.change_admin_password.assert_called_once_with("testadmin", "newpassword123")
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()
        assert result == sample_admin

    # ==================== REMOVE ADMIN TESTS ====================

    def test_remove_admin_by_id_success(self, admin_service, mock_uow, mock_aggregate, sample_admin):
        """Test successful admin removal by ID"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_all_admins.return_value = [sample_admin]

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute
        admin_service._remove_admin_by_id(1)

        # Assertions
        mock_aggregate.get_all_admins.assert_called_once()
        mock_aggregate.remove_admin.assert_called_once_with("testadmin")
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()

    def test_remove_admin_by_id_not_found(self, admin_service, mock_uow, mock_aggregate):
        """Test removal by ID when admin doesn't exist"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_all_admins.return_value = []

        # Mock context manager
        mock_uow.__enter__ = Mock(return_value=mock_uow)
        mock_uow.__exit__ = Mock(return_value=None)

        # Execute and assert
        with pytest.raises(ValueError, match="Admin with ID 999 not found"):
            admin_service._remove_admin_by_id(999)

        # Ensure remove and save were NOT called
        mock_aggregate.remove_admin.assert_not_called()
        mock_uow.admins.save_admins.assert_not_called()
        mock_uow.commit.assert_not_called()

    # ==================== BULK OPERATIONS TESTS ====================

    def test_list_all_admins(self, admin_service, mock_uow, mock_aggregate, sample_admin, another_admin):
        """Test listing all admins"""
        # Setup mocks
        mock_admins = [sample_admin, another_admin]
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

    def test_list_enabled_admins(self, admin_service, mock_uow, mock_aggregate, sample_admin, another_admin):
        """Test listing enabled admins"""
        # Setup mocks
        mock_enabled_admins = [sample_admin]  # only enabled ones
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

    def test_admin_exists_by_id_true(self, admin_service, mock_uow, mock_aggregate, sample_admin):
        """Test admin_exists_by_id when admin exists"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_all_admins.return_value = [sample_admin]

        # Execute
        result = admin_service.admin_exists_by_id(1)

        # Assertions
        assert result is True

    def test_admin_exists_by_id_false(self, admin_service, mock_uow, mock_aggregate):
        """Test admin_exists_by_id when admin doesn't exist"""
        # Setup mocks
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_all_admins.return_value = []

        # Execute
        result = admin_service.admin_exists_by_id(999)

        # Assertions
        assert result is False

    # ==================== ERROR HANDLING TESTS ====================

    def test_create_admin_unexpected_error(self, admin_service, sample_admin_data):
        """Test handling of unexpected errors during admin creation"""
        with patch.object(admin_service, '_log_operation'):
            with patch.object(admin_service.uow, '__enter__') as mock_enter:
                mock_enter.side_effect = Exception("Database connection failed")

                with pytest.raises(RuntimeError, match="Failed to create admin"):
                    admin_service._create_admin(sample_admin_data)

    def test_create_admin_value_error_logging(self, admin_service, mock_uow, mock_aggregate, sample_admin_data, caplog):
        """Test that ValueErrors are properly logged during creation"""
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


class TestAdminServiceInitialization:
    """Tests for AdminService initialization and base functionality"""

    def test_initialization(self, mock_uow):
        """Test that AdminService initializes correctly"""
        service = AdminService(mock_uow)

        assert service.uow == mock_uow
        assert isinstance(service, BaseService)
        assert hasattr(service, 'logger')

    def test_inheritance(self, mock_uow):
        """Test that AdminService properly inherits from BaseService"""
        service = AdminService(mock_uow)

        # Test inherited methods
        assert hasattr(service, '_validate_input')
        assert hasattr(service, '_log_operation')

        # Test that execute method is implemented
        assert hasattr(service, 'execute')


# Test configuration
pytestmark = pytest.mark.unit


def test_imports():
    """Test that all required imports are available"""
    from src.services.service_layer.admins import AdminService
    from src.services.service_layer.data import CreateAdminData

    assert AdminService is not None
    assert CreateAdminData is not None