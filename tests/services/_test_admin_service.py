# tests/unit/services/test_admin_service.py
import pytest
from unittest.mock import Mock, create_autospec, patch
from typing import List

from src.services.service_layer.admins import AdminService
from src.services.service_layer.data import CreateAdminData
from src.services.uow.uowsqlite import AbstractUnitOfWork
from src.domain.exceptions import DomainOperationError
from src.domain.model import Admin, AdminAbstract, AdminsAggregate


class TestAdminService:
    """Test suite for AdminService"""

    @pytest.fixture
    def mock_uow(self):
        """Mock Unit of Work"""
        uow = create_autospec(AbstractUnitOfWork)
        uow.admins = Mock()
        return uow

    @pytest.fixture
    def mock_aggregate(self):
        """Mock AdminsAggregate"""
        aggregate = create_autospec(AdminsAggregate)
        return aggregate

    @pytest.fixture
    def mock_admin(self):
        """Mock Admin object"""
        admin = create_autospec(AdminAbstract)
        admin.admin_id = 1
        admin.name = "test_admin"
        admin.email = "test@example.com"
        admin.enabled = True
        return admin

    @pytest.fixture
    def admin_service(self, mock_uow):
        """AdminService instance"""
        return AdminService(uow=mock_uow)

    @pytest.fixture
    def create_admin_data(self):
        """Sample CreateAdminData"""
        return CreateAdminData(
            name="new_admin",
            email="new@example.com",
            password="secure_password",
            enabled=True
        )

    # Test execute method
    def test_execute_valid_operation(self, admin_service, mock_uow, mock_aggregate, mock_admin):
        """Test execute with valid operation"""
        # Setup
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.require_admin_by_name.return_value = mock_admin

        # Execute
        result = admin_service.execute("get_by_name", name="test_admin")

        # Assert
        assert result == mock_admin

    def test_execute_invalid_operation(self, admin_service):
        """Test execute with invalid operation"""
        with pytest.raises(DomainOperationError, match="Unknown operation: invalid_op"):
            admin_service.execute("invalid_op", name="test")

    def test_execute_missing_parameters(self, admin_service):
        """Test execute with missing required parameters"""
        with pytest.raises(ValueError, match="Parameter 'name' cannot be None"):
            admin_service.execute("get_by_name")  # Missing name

    def test_execute_none_operation(self, admin_service):
        """Test execute with None operation"""
        with pytest.raises(ValueError, match="Parameter 'operation' cannot be None"):
            admin_service.execute(None)

    # Test _create_admin
    def test_create_admin_success(self, admin_service, mock_uow, mock_aggregate, create_admin_data, mock_admin):
        """Test successful admin creation"""
        # Setup
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        fresh_admin = create_autospec(AdminAbstract)
        fresh_admin.admin_id = 1
        fresh_admin.name = create_admin_data.name

        # Mock the reload operation
        admin_service._get_admin_by_name = Mock(return_value=fresh_admin)

        # Execute
        result = admin_service._create_admin(create_admin_data)

        # Assert
        mock_aggregate.create_admin.assert_called_once_with(
            admin_id=0,
            name=create_admin_data.name,
            email=create_admin_data.email,
            password=create_admin_data.password,
            enabled=create_admin_data.enabled
        )
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()
        assert result == fresh_admin

    def test_create_admin_id_not_generated(self, admin_service, mock_uow, mock_aggregate, create_admin_data):
        """Test admin creation when ID is not properly generated"""
        # Setup
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        fresh_admin = create_autospec(AdminAbstract)
        fresh_admin.admin_id = 0  # ID not generated

        admin_service._get_admin_by_name = Mock(return_value=fresh_admin)

        # Execute & Assert
        with pytest.raises(DomainOperationError, match="Admin was created but ID wasn't properly generated"):
            admin_service._create_admin(create_admin_data)

    def test_create_admin_unexpected_error(self, admin_service, mock_uow, create_admin_data):
        """Test admin creation with unexpected error"""
        mock_uow.admins.get_list_of_admins.side_effect = Exception("Database error")

        with pytest.raises(RuntimeError, match="Failed to create admin"):
            admin_service._create_admin(create_admin_data)

    # Test _get_admin_by_name
    def test_get_admin_by_name_success(self, admin_service, mock_uow, mock_aggregate, mock_admin):
        """Test successful admin retrieval by name"""
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.require_admin_by_name.return_value = mock_admin

        result = admin_service._get_admin_by_name("test_admin")

        mock_aggregate.require_admin_by_name.assert_called_once_with("test_admin")
        assert result == mock_admin

    def test_get_admin_by_name_not_found(self, admin_service, mock_uow, mock_aggregate):
        """Test admin retrieval by name when not found"""
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.require_admin_by_name.side_effect = DomainOperationError("Admin not found")

        with pytest.raises(DomainOperationError, match="Admin not found"):
            admin_service._get_admin_by_name("nonexistent")

    # Test _get_admin_by_id
    def test_get_admin_by_id_success(self, admin_service, mock_uow, mock_aggregate, mock_admin):
        """Test successful admin retrieval by ID"""
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_admin_by_id.return_value = mock_admin

        result = admin_service._get_admin_by_id(1)

        mock_aggregate.get_admin_by_id.assert_called_once_with(admin_id=1)
        assert result == mock_admin

    def test_get_admin_by_id_not_found(self, admin_service, mock_uow, mock_aggregate):
        """Test admin retrieval by ID when not found"""
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_admin_by_id.return_value = None

        result = admin_service._get_admin_by_id(999)

        assert result is None

    # Test _update_admin_email
    def test_update_admin_email_success(self, admin_service, mock_uow, mock_aggregate, mock_admin):
        """Test successful email update"""
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.require_admin_by_name.return_value = mock_admin

        result = admin_service._update_admin_email("test_admin", "new@example.com")

        mock_aggregate.require_admin_by_name.assert_called_with("test_admin")
        mock_aggregate.change_admin_email.assert_called_once_with("test_admin", "new@example.com")
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()
        assert result == mock_admin

    # Test _toggle_admin_status
    def test_toggle_admin_status_success(self, admin_service, mock_uow, mock_aggregate, mock_admin):
        """Test successful admin status toggle"""
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.require_admin_by_name.return_value = mock_admin

        result = admin_service._toggle_admin_status("test_admin")

        mock_aggregate.toggle_admin_status.assert_called_once_with("test_admin")
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()
        assert result == mock_admin

    def test_toggle_admin_status_logging(self, admin_service, mock_uow, mock_aggregate, mock_admin, caplog):
        """Test logging during status toggle"""
        caplog.set_level(logging.INFO)
        mock_admin.enabled = True

        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.require_admin_by_name.return_value = mock_admin

        admin_service._toggle_admin_status("test_admin")

        assert "Admin test_admin status toggled to disabled" in caplog.text

    # Test _change_admin_password
    def test_change_admin_password_success(self, admin_service, mock_uow, mock_aggregate, mock_admin):
        """Test successful password change"""
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.require_admin_by_name.return_value = mock_admin

        result = admin_service._change_admin_password("test_admin", "new_password")

        mock_aggregate.change_admin_password.assert_called_once_with("test_admin", "new_password")
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()
        assert result == mock_admin

    # Test _remove_admin_by_id
    def test_remove_admin_by_id_success(self, admin_service, mock_uow, mock_aggregate):
        """Test successful admin removal"""
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate

        admin_service._remove_admin_by_id(1)

        mock_aggregate.remove_admin_by_id.assert_called_once_with(1)
        mock_uow.admins.save_admins.assert_called_once_with(mock_aggregate)
        mock_uow.commit.assert_called_once()

    # Test bulk operations
    def test_list_all_admins(self, admin_service, mock_uow, mock_aggregate):
        """Test listing all admins"""
        admin1 = create_autospec(Admin)
        admin2 = create_autospec(Admin)
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_all_admins.return_value = [admin1, admin2]

        result = admin_service.list_all_admins()

        assert len(result) == 2
        assert admin1 in result
        assert admin2 in result

    def test_list_enabled_admins(self, admin_service, mock_uow, mock_aggregate):
        """Test listing enabled admins"""
        enabled_admin = create_autospec(Admin)
        disabled_admin = create_autospec(Admin)
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.get_enabled_admins.return_value = [enabled_admin]

        result = admin_service.list_enabled_admins()

        assert len(result) == 1
        assert enabled_admin in result

    def test_admin_exists_true(self, admin_service, mock_uow, mock_aggregate):
        """Test admin exists returns True"""
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = True

        result = admin_service.admin_exists("existing_admin")

        assert result is True
        mock_aggregate.admin_exists.assert_called_once_with("existing_admin")

    def test_admin_exists_false(self, admin_service, mock_uow, mock_aggregate):
        """Test admin exists returns False"""
        mock_uow.admins.get_list_of_admins.return_value = mock_aggregate
        mock_aggregate.admin_exists.return_value = False

        result = admin_service.admin_exists("nonexistent_admin")

        assert result is False

    # Test error scenarios
    def test_uow_context_manager_error(self, admin_service, mock_uow):
        """Test behavior when UoW context manager fails"""
        mock_uow.__enter__.side_effect = Exception("UoW error")

        with pytest.raises(RuntimeError, match="Failed to create admin"):
            admin_service._create_admin(Mock())

    def test_operation_with_empty_string(self, admin_service):
        """Test operations with empty string parameters"""
        with pytest.raises(ValueError, match="Parameter 'name' cannot be None"):
            admin_service.execute("get_by_name", name="")  # Empty string


