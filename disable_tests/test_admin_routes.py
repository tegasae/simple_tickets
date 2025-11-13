import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, status

from src.web.routers import admins
from src.web.models import AdminCreate, AdminUpdate
from src.services.service_layer.data import CreateAdminData


class TestCreateAdmin:
    """Unit tests for create_admin endpoint"""

    @pytest.mark.asyncio
    async def test_create_admin_success(self):
        """Test successful admin creation"""
        # Arrange
        mock_sf = AsyncMock()  # Use AsyncMock for async context
        mock_admin_service = AsyncMock()
        mock_admin = Mock()
        mock_sf.get_admin_service.return_value = mock_admin_service
        mock_admin_service.execute.return_value = mock_admin

        admin_create_data = AdminCreate(
            name="testadmin",
            email="test@example.com",
            password="testpassword123",
            enabled=True
        )

        # Act
        result = await admins.create_admin(admin_create_data, mock_sf)

        # Assert
        mock_sf.get_admin_service.assert_called_once()
        mock_admin_service.execute.assert_called_once()
        call_args = mock_admin_service.execute.call_args
        assert call_args[0][0] == 'create'
        assert isinstance(call_args[1]['create_admin_data'], CreateAdminData)

    @pytest.mark.asyncio
    async def test_create_admin_service_exception(self):
        """Test admin creation when service layer raises exception"""
        # Arrange
        mock_sf = AsyncMock()
        mock_admin_service = AsyncMock()
        mock_sf.get_admin_service.return_value = mock_admin_service
        mock_admin_service.execute.side_effect = Exception("Service error")

        admin_create_data = AdminCreate(
            name="testadmin",
            email="test@example.com",
            password="testpassword123"
        )

        # Act & Assert
        with pytest.raises(Exception, match="Service error"):
            await admins.create_admin(admin_create_data, mock_sf)


class TestReadAdmins:
    """Unit tests for read_admins endpoint"""

    @pytest.mark.asyncio
    async def test_read_admins_success(self):
        """Test successful retrieval of all admins"""
        # Arrange
        mock_sf = AsyncMock()
        mock_admin_service = AsyncMock()
        mock_admin1 = Mock()
        mock_admin2 = Mock()

        mock_sf.get_admin_service.return_value = mock_admin_service
        mock_admin_service.list_all_admins.return_value = [mock_admin1, mock_admin2]

        # Act
        result = await admins.read_admins(mock_sf)

        # Assert
        mock_sf.get_admin_service.assert_called_once()
        mock_admin_service.list_all_admins.assert_called_once()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_read_admins_empty_list(self):
        """Test retrieval when no admins exist"""
        # Arrange
        mock_sf = AsyncMock()
        mock_admin_service = AsyncMock()
        mock_sf.get_admin_service.return_value = mock_admin_service
        mock_admin_service.list_all_admins.return_value = []

        # Act
        result = await admins.read_admins(mock_sf)

        # Assert
        assert result == []


class TestReadAdmin:
    """Unit tests for read_admin endpoint"""

    @pytest.mark.asyncio
    async def test_read_admin_by_id_success(self):
        """Test successful retrieval of admin by ID"""
        # Arrange
        mock_sf = AsyncMock()
        mock_admin_service = AsyncMock()
        mock_admin = Mock()

        mock_sf.get_admin_service.return_value = mock_admin_service
        mock_admin_service.execute.return_value = mock_admin

        # Act
        result = await admins.read_admin(admin_id=1, sf=mock_sf)

        # Assert
        mock_sf.get_admin_service.assert_called_once()
        mock_admin_service.execute.assert_called_once_with('get_by_id', admin_id=1)


class TestReadAdminByName:
    """Unit tests for read_admin_by_name endpoint"""

    @pytest.mark.asyncio
    async def test_read_admin_by_name_success(self):
        """Test successful retrieval of admin by name"""
        # Arrange
        mock_sf = AsyncMock()
        mock_admin_service = AsyncMock()
        mock_admin = Mock()

        mock_sf.get_admin_service.return_value = mock_admin_service
        mock_admin_service.execute.return_value = mock_admin

        # Act
        result = await admins.read_admin_by_name(admin_name="testadmin", sf=mock_sf)

        # Assert
        mock_sf.get_admin_service.assert_called_once()
        mock_admin_service.execute.assert_called_once_with('get_by_name', name="testadmin")


class TestUpdateAdmin:
    """Unit tests for update_admin endpoint"""

    @pytest.mark.asyncio
    async def test_update_admin_email_only(self):
        """Test updating only email address"""
        # Arrange
        mock_sf = AsyncMock()
        mock_admin_service = AsyncMock()
        mock_target_admin = Mock()
        mock_target_admin.name = "testadmin"
        mock_target_admin.enabled = True

        mock_sf.get_admin_service.return_value = mock_admin_service
        # For async, we need to handle the side effect properly
        mock_admin_service.execute.side_effect = [
            mock_target_admin,  # First call: get_by_id
            Mock(),  # Second call: update_email
            Mock()  # Third call: get_by_id (final)
        ]

        update_data = AdminUpdate(email="new@example.com")

        # Act
        result = await admins.update_admin(admin_id=1, admin_update=update_data, sf=mock_sf)

        # Assert
        assert mock_admin_service.execute.call_count == 3


class TestDeleteAdmin:
    """Unit tests for delete_admin endpoint"""

    @pytest.mark.asyncio
    async def test_delete_admin_success(self):
        """Test successful admin deletion"""
        # Arrange
        mock_sf = AsyncMock()
        mock_admin_service = AsyncMock()
        mock_sf.get_admin_service.return_value = mock_admin_service

        # Act
        result = await admins.delete_admin(admin_id=1, sf=mock_sf)

        # Assert
        mock_sf.get_admin_service.assert_called_once()
        mock_admin_service.execute.assert_called_once_with('remove_by_id', admin_id=1)
        assert result is None


class TestToggleAdminStatus:
    """Unit tests for toggle_admin_status endpoint"""

    @pytest.mark.asyncio
    async def test_toggle_admin_status_success(self):
        """Test successful admin status toggle"""
        # Arrange
        mock_sf = AsyncMock()  # Use AsyncMock
        mock_admin_service = AsyncMock()  # Use AsyncMock
        mock_target_admin = Mock()
        mock_target_admin.name = "testadmin"
        mock_updated_admin = Mock()

        mock_sf.get_admin_service.return_value = mock_admin_service
        mock_admin_service.execute.side_effect = [
            mock_target_admin,  # get_by_id
            mock_updated_admin  # toggle_status
        ]

        # Act
        result = await admins.toggle_admin_status(admin_id=1, sf=mock_sf)

        # Assert
        assert mock_admin_service.execute.call_count == 2
        calls = mock_admin_service.execute.call_args_list
        assert calls[0][0] == ('get_by_id',)
        assert calls[0][1] == {'admin_id': 1}
        assert calls[1][0] == ('toggle_status',)
        assert calls[1][1] == {'name': 'testadmin'}


class TestCheckAdminExists:
    """Unit tests for check_admin_exists endpoint"""

    @pytest.mark.asyncio
    async def test_check_admin_exists_true(self):
        """Test when admin exists"""
        # Arrange
        mock_sf = AsyncMock()
        mock_admin_service = AsyncMock()
        mock_sf.get_admin_service.return_value = mock_admin_service
        mock_admin_service.admin_exists.return_value = True

        # Act
        result = await admins.check_admin_exists(admin_name="existingadmin", sf=mock_sf)

        # Assert
        mock_sf.get_admin_service.assert_called_once()
        mock_admin_service.admin_exists.assert_called_once_with("existingadmin")
        assert result == {"exists": True}


class TestRouterConfiguration:
    """Tests for router configuration"""

    def test_router_config(self):
        """Test router is configured correctly"""
        assert admins.router.prefix == "/admins"
        assert admins.router.tags == ["admins"]
        assert 404 in admins.router.responses
        assert admins.router.responses[404] == {"description": "Not found"}

    def test_exception_handlers_mapping(self):
        """Test exception handlers are properly mapped"""
        expected_handlers = {
            'AdminError': 500,
            'AdminNotFoundError': 404,
            'AdminAlreadyExistsError': 409,
            'AdminValidationError': 400,
            'AdminOperationError': 400,
            'AdminSecurityError': 403
        }
        assert admins.handlers == expected_handlers