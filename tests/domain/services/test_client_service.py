# tests/domain/services/test_client_service.py
"""Tests for ClientService with updated delete logic."""

import pytest
from unittest.mock import Mock, create_autospec
from typing import List

from src.domain.client import Client
from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.repositories.client_repository import ClientRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.client import ClientService


class TestClientService:
    """Test suite for ClientService."""

    @pytest.fixture
    def mock_client_repository(self) -> Mock:
        """Create a mock ClientRepository."""
        return create_autospec(ClientRepository)

    @pytest.fixture
    def mock_user_repository(self) -> Mock:
        """Create a mock UserRepository."""
        return create_autospec(UserRepository)

    @pytest.fixture
    def client_service(
            self,
            mock_client_repository: Mock,
            mock_user_repository: Mock
    ) -> ClientService:
        """Create ClientService with mocked repositories."""
        return ClientService(
            client_repository=mock_client_repository,
            user_repository=mock_user_repository
        )

    @pytest.fixture
    def sample_client(self) -> Client:
        """Create a sample client."""
        return Client.create(
            client_id=1,
            name="Test Client",
            email="test@example.com",
            address="123 Test St",
            phone="+1234567890",
            created_by_admin_id=100,
            enabled=True
        )

    @pytest.fixture
    def disabled_client(self) -> Client:
        """Create a disabled client."""
        client = Client.create(
            client_id=2,
            name="Disabled Client",
            email="disabled@example.com",
            created_by_admin_id=100,
            enabled=True
        )
        client.disable()
        return client

    # ---------------------------
    # Create Tests
    # ---------------------------

    def test_create_client_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            mock_user_repository: Mock
    ):
        """Test successful client creation."""
        # Act
        client = client_service.create(
            client_id=1,
            name="New Client",
            created_by_admin_id=100,
            email="new@example.com",
            address="456 New St",
            phone="+5555555555",
            enabled=True
        )

        # Assert
        assert client.client_id == 1
        assert str(client.name) == "New Client"
        assert str(client.email) == "new@example.com"

        mock_client_repository.save.assert_called_once_with(client)
        mock_user_repository.assert_not_called()  # User repo not used in create

    def test_create_client_minimal_fields(
            self,
            client_service: ClientService,
            mock_client_repository: Mock
    ):
        """Test client creation with minimal fields."""
        # Act
        client = client_service.create(
            client_id=1,
            name="Minimal Client",
            created_by_admin_id=100
        )

        # Assert
        assert client.client_id == 1
        assert str(client.name) == "Minimal Client"
        assert client.email is None
        assert client.address is None
        assert client.phone is None
        assert client.enabled is True

    # ---------------------------
    # Update Contact Info Tests
    # ---------------------------

    def test_update_contact_info_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test successful contact info update."""
        # Arrange
        mock_client_repository.get.return_value = sample_client

        # Act
        updated_client = client_service.update_contact_info(
            client_id=1,
            email="updated@example.com",
            address="Updated Address",
            phone="+9999999999"
        )

        # Assert
        assert str(updated_client.email) == "updated@example.com"
        assert str(updated_client.address) == "Updated Address"
        assert str(updated_client.phone) == "+9999999999"

        mock_client_repository.get.assert_called_once_with(1)
        mock_client_repository.save.assert_called_once()

    def test_update_contact_info_partial(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test partial contact info update."""
        # Arrange
        mock_client_repository.get.return_value = sample_client
        original_email = sample_client.email

        # Act
        updated_client = client_service.update_contact_info(
            client_id=1,
            phone="+8888888888"
        )

        # Assert
        assert updated_client.email == original_email  # Unchanged
        assert str(updated_client.phone) == "+8888888888"

    def test_update_contact_info_client_not_found(
            self,
            client_service: ClientService,
            mock_client_repository: Mock
    ):
        """Test updating non-existent client."""
        # Arrange
        mock_client_repository.get.side_effect = ItemValidationError("Client not found")

        # Act & Assert
        with pytest.raises(ItemValidationError, match="Client not found"):
            client_service.update_contact_info(
                client_id=999,
                email="test@example.com"
            )

    # ---------------------------
    # Enable/Disable Tests
    # ---------------------------

    def test_disable_client_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test successfully disabling a client."""
        # Arrange
        mock_client_repository.get.return_value = sample_client
        assert sample_client.enabled is True

        # Act
        disabled_client = client_service.disable(client_id=1)

        # Assert
        assert disabled_client.enabled is False
        mock_client_repository.save.assert_called_once()

    def test_enable_client_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            disabled_client: Client
    ):
        """Test successfully enabling a client."""
        # Arrange
        mock_client_repository.get.return_value = disabled_client
        assert disabled_client.enabled is False

        # Act
        enabled_client = client_service.enable(client_id=2)

        # Assert
        assert enabled_client.enabled is True
        mock_client_repository.save.assert_called_once()

    # ---------------------------
    # Delete Tests (with new business rules)
    # ---------------------------

    def test_delete_client_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            mock_user_repository: Mock,
            disabled_client: Client
    ):
        """Test successfully hard deleting a disabled client with no users."""
        # Arrange
        mock_client_repository.get.return_value = disabled_client
        mock_user_repository.get_all_by_client.return_value = []  # No users

        # Act
        client_service.delete(client_id=2)

        # Assert
        mock_client_repository.get.assert_called_once_with(2)
        mock_user_repository.get_all_by_client.assert_called_once_with(client_id=2)
        mock_client_repository.hard_delete.assert_called_once_with(2)

    def test_delete_active_client_fails(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            mock_user_repository: Mock,
            sample_client: Client
    ):
        """Test deleting an active client fails."""
        # Arrange
        mock_client_repository.get.return_value = sample_client
        assert sample_client.enabled is True

        # Act & Assert
        with pytest.raises(DomainOperationError, match="is active"):
            client_service.delete(client_id=1)

        mock_client_repository.hard_delete.assert_not_called()
        mock_user_repository.get_all_by_client.assert_not_called()  # Shouldn't check users if client is active

    def test_delete_client_with_users_fails(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            mock_user_repository: Mock,
            disabled_client: Client
    ):
        """Test deleting a client that has users fails."""
        # Arrange
        mock_client_repository.get.return_value = disabled_client
        # Mock that client has users
        mock_user_repository.get_all_by_client.return_value = [Mock(), Mock()]

        # Act & Assert
        with pytest.raises(DomainOperationError, match="has users"):
            client_service.delete(client_id=2)

        mock_client_repository.get.assert_called_once_with(2)
        mock_user_repository.get_all_by_client.assert_called_once_with(client_id=2)
        mock_client_repository.hard_delete.assert_not_called()

    def test_delete_client_not_found(
            self,
            client_service: ClientService,
            mock_client_repository: Mock
    ):
        """Test deleting non-existent client."""
        # Arrange
        mock_client_repository.get.side_effect = ItemValidationError("Client not found")

        # Act & Assert
        with pytest.raises(ItemValidationError, match="Client not found"):
            client_service.delete(client_id=999)

    # ---------------------------
    # _check_users Tests
    # ---------------------------

    def test_check_users_with_users(
            self,
            client_service: ClientService,
            mock_user_repository: Mock
    ):
        """Test _check_users returns True when client has users."""
        # Arrange
        mock_user_repository.get_all_by_client.return_value = [Mock(), Mock()]

        # Act
        result = client_service._check_users(client_id=1)

        # Assert
        assert result is True
        mock_user_repository.get_all_by_client.assert_called_once_with(client_id=1)

    def test_check_users_without_users(
            self,
            client_service: ClientService,
            mock_user_repository: Mock
    ):
        """Test _check_users returns False when client has no users."""
        # Arrange
        mock_user_repository.get_all_by_client.return_value = []

        # Act
        result = client_service._check_users(client_id=1)

        # Assert
        assert result is False
        mock_user_repository.get_all_by_client.assert_called_once_with(client_id=1)

    # ---------------------------
    # Integration/Combined Scenarios
    # ---------------------------

    def test_full_client_lifecycle_with_delete(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            mock_user_repository: Mock
    ):
        """Test complete client lifecycle including delete."""
        # 1. Create client
        client = client_service.create(
            client_id=1,
            name="Lifecycle Client",
            created_by_admin_id=100,
            email="lifecycle@example.com"
        )
        assert client.enabled is True

        # Update mock for subsequent operations
        mock_client_repository.get.return_value = client

        # 2. Update contact info
        updated = client_service.update_contact_info(
            client_id=1,
            phone="+1234567890"
        )
        assert str(updated.phone) == "+1234567890"

        # 3. Disable client (required for delete)
        disabled = client_service.disable(client_id=1)
        assert disabled.enabled is False

        # 4. Verify no users and delete
        mock_user_repository.get_all_by_client.return_value = []
        client_service.delete(client_id=1)

        # Verify final delete
        mock_client_repository.hard_delete.assert_called_once_with(1)

    def test_cannot_delete_reenabled_client(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            mock_user_repository: Mock,
            disabled_client: Client
    ):
        """Test that a client re-enabled after disable cannot be deleted."""
        # Arrange
        mock_client_repository.get.return_value = disabled_client

        # Re-enable the client
        disabled_client.enable()
        assert disabled_client.enabled is True

        # Act & Assert
        with pytest.raises(DomainOperationError, match="is active"):
            client_service.delete(client_id=2)

        mock_client_repository.hard_delete.assert_not_called()