# tests/domain/services/test_client_service.py
import pytest
from unittest.mock import Mock, create_autospec


from src.domain.client import Client
from src.domain.exceptions import ItemValidationError, DomainOperationError
from src.domain.repositories.client_repository import ClientRepository
from src.domain.services.client import ClientService
from src.domain.value_objects import Name, Email, Address, Phone


class TestClientService:
    """Test suite for ClientService orchestration."""

    @pytest.fixture
    def mock_client_repository(self) -> Mock:
        """Create a mock ClientRepository with autospec."""
        return create_autospec(ClientRepository)

    @pytest.fixture
    def client_service(self, mock_client_repository: Mock) -> ClientService:
        """Create ClientService with mocked repository."""
        return ClientService(clients=mock_client_repository)

    @pytest.fixture
    def sample_client(self) -> Client:
        """Create a sample client for testing."""
        return Client(
            client_id=1,
            name=Name("Test Client"),
            email=Email("test@example.com"),
            address=Address("123 Test St"),
            phone=Phone("555-1234"),
            created_by_admin_id=100,
            enabled=True,
            is_deleted=False
        )

    @pytest.fixture
    def deleted_client(self) -> Client:
        """Create a sample deleted client for testing."""
        client = Client(
            client_id=2,
            name=Name("Deleted Client"),
            email=Email("deleted@example.com"),
            created_by_admin_id=100,
            enabled=False,
            is_deleted=True,
            address=None,
            phone=None

        )
        return client

    # ---------------------------
    # Create Client Tests
    # ---------------------------

    def test_create_client_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock
    ):
        """Test successful client creation."""
        # Arrange
        mock_client_repository.exists_by_name.return_value = False

        # Act
        client = client_service.create_client(
            client_id=1,
            name="New Client",
            created_by_admin_id=100,
            email="new@example.com",
            address="456 New St",
            phone="555-5678",
            enabled=True
        )

        # Assert
        assert client.client_id == 1
        assert client.name.value == "New Client"
        assert client.email.value == "new@example.com"
        assert client.address.value == "456 New St"
        assert client.phone.value == "555-5678"
        assert client.created_by_admin_id == 100
        assert client.enabled is True

        mock_client_repository.exists_by_name.assert_called_once_with("New Client")
        mock_client_repository.save.assert_called_once_with(client)

    def test_create_client_duplicate_name(
            self,
            client_service: ClientService,
            mock_client_repository: Mock
    ):
        """Test client creation fails when name already exists."""
        # Arrange
        mock_client_repository.exists_by_name.return_value = True

        # Act & Assert
        with pytest.raises(ItemValidationError, match="Client with name 'Duplicate' already exists"):
            client_service.create_client(
                client_id=1,
                name="Duplicate",
                created_by_admin_id=100
            )

        mock_client_repository.exists_by_name.assert_called_once_with("Duplicate")
        mock_client_repository.save.assert_not_called()

    def test_create_client_minimal_fields(
            self,
            client_service: ClientService,
            mock_client_repository: Mock
    ):
        """Test client creation with only required fields."""
        # Arrange
        mock_client_repository.exists_by_name.return_value = False

        # Act
        client = client_service.create_client(
            client_id=1,
            name="Minimal Client",
            created_by_admin_id=100
        )

        # Assert
        assert client.client_id == 1
        assert client.name.value == "Minimal Client"
        assert client.created_by_admin_id == 100
        assert client.email is None
        assert client.address is None
        assert client.phone is None
        assert client.enabled is True  # default

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
            phone="555-9999"
        )

        # Assert
        assert updated_client.email.value == "updated@example.com"
        assert updated_client.address.value == "Updated Address"
        assert updated_client.phone.value == "555-9999"

        mock_client_repository.get.assert_called_once_with(1)
        mock_client_repository.save.assert_called_once_with(sample_client)

    def test_update_contact_info_partial(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test updating only some contact fields."""
        # Arrange
        mock_client_repository.get.return_value = sample_client
        original_email = sample_client.email
        original_address = sample_client.address

        # Act - update only phone
        updated_client = client_service.update_contact_info(
            client_id=1,
            phone="555-8888"
        )

        # Assert
        assert updated_client.email == original_email  # unchanged
        assert updated_client.address == original_address  # unchanged
        assert updated_client.phone.value == "555-8888"  # updated

    def test_update_contact_info_deleted_client(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            deleted_client: Client
    ):
        """Test updating contact info of deleted client fails."""
        # Arrange
        mock_client_repository.get.return_value = deleted_client

        # Act & Assert
        with pytest.raises(DomainOperationError, match="Cannot update a deleted client"):
            client_service.update_contact_info(
                client_id=2,
                email="test@example.com"
            )

        mock_client_repository.save.assert_not_called()

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
    # Enable/Disable Client Tests
    # ---------------------------

    def test_disable_client_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test successfully disabling a client."""
        # Arrange
        sample_client.enable()  # ensure client is enabled
        mock_client_repository.get.return_value = sample_client

        # Act
        disabled_client = client_service.disable_client(client_id=1)

        # Assert
        assert disabled_client.enabled is False
        mock_client_repository.get.assert_called_once_with(1)
        mock_client_repository.save.assert_called_once()

    def test_disable_already_disabled_client(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test disabling an already disabled client (should be idempotent)."""
        # Arrange
        sample_client.disable()  # disable first
        assert sample_client.enabled is False
        mock_client_repository.get.return_value = sample_client

        # Act
        disabled_client = client_service.disable_client(client_id=1)

        # Assert
        assert disabled_client.enabled is False
        mock_client_repository.save.assert_called_once()  # still called

    def test_disable_deleted_client(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            deleted_client: Client
    ):
        """Test disabling a deleted client fails."""
        # Arrange
        mock_client_repository.get.return_value = deleted_client

        # Act & Assert
        with pytest.raises(DomainOperationError, match="Cannot disable a deleted client"):
            client_service.disable_client(client_id=2)

        mock_client_repository.save.assert_not_called()

    def test_enable_client_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test successfully enabling a client."""
        # Arrange
        sample_client.disable()  # disable first
        mock_client_repository.get.return_value = sample_client

        # Act
        enabled_client = client_service.enable_client(client_id=1)

        # Assert
        assert enabled_client.enabled is True
        mock_client_repository.get.assert_called_once_with(1)
        mock_client_repository.save.assert_called_once()

    def test_enable_deleted_client(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            deleted_client: Client
    ):
        """Test enabling a deleted client fails."""
        # Arrange
        mock_client_repository.get.return_value = deleted_client

        # Act & Assert
        with pytest.raises(DomainOperationError, match="Cannot enable a deleted client"):
            client_service.enable_client(client_id=2)

        mock_client_repository.save.assert_not_called()

    # ---------------------------
    # Soft Delete/Restore Tests
    # ---------------------------

    def test_soft_delete_client_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test successfully soft deleting a client."""
        # Arrange
        mock_client_repository.get.return_value = sample_client
        assert sample_client.is_deleted is False

        # Act
        deleted_client = client_service.soft_delete_client(client_id=1)

        # Assert
        assert deleted_client.is_deleted is True
        mock_client_repository.get.assert_called_once_with(1)
        mock_client_repository.save.assert_called_once()

    def test_soft_delete_already_deleted_client(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            deleted_client: Client
    ):
        """Test soft deleting an already deleted client (idempotent)."""
        # Arrange
        mock_client_repository.get.return_value = deleted_client


        # Act
        result = client_service.soft_delete_client(client_id=2)

        # Assert
        assert result.is_deleted is True

        mock_client_repository.get.assert_called_once_with(2)
        mock_client_repository.save.assert_not_called()  # no save needed

    def test_restore_client_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            deleted_client: Client
    ):
        """Test successfully restoring a deleted client."""
        # Arrange
        mock_client_repository.get.return_value = deleted_client

        # Act
        restored_client = client_service.restore_client(client_id=2)

        # Assert
        assert restored_client.is_deleted is False

        mock_client_repository.get.assert_called_once_with(2)
        mock_client_repository.save.assert_called_once()

    def test_restore_non_deleted_client(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test restoring a non-deleted client (idempotent)."""
        # Arrange
        mock_client_repository.get.return_value = sample_client
        assert sample_client.is_deleted is False

        # Act
        result = client_service.restore_client(client_id=1)

        # Assert
        assert result.is_deleted is False
        mock_client_repository.save.assert_not_called()

    # ---------------------------
    # Hard Delete Tests
    # ---------------------------

    def test_hard_delete_client_success(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test successfully hard deleting a client."""
        # Arrange
        mock_client_repository.get.return_value = sample_client

        # Act
        client_service.hard_delete_client(client_id=1)

        # Assert
        mock_client_repository.get.assert_called_once_with(1)
        mock_client_repository.hard_delete.assert_called_once_with(1)

    def test_hard_delete_client_not_found(
            self,
            client_service: ClientService,
            mock_client_repository: Mock
    ):
        """Test hard deleting non-existent client."""
        # Arrange
        mock_client_repository.get.side_effect = ItemValidationError("Client not found")

        # Act & Assert
        with pytest.raises(ItemValidationError, match="Client not found"):
            client_service.hard_delete_client(client_id=999)

        mock_client_repository.hard_delete.assert_not_called()

    # ---------------------------
    # Integration/Combined Scenarios
    # ---------------------------

    def test_full_client_lifecycle(
            self,
            client_service: ClientService,
            mock_client_repository: Mock
    ):
        """Test complete client lifecycle: create -> update -> disable -> restore -> soft delete -> hard delete."""
        # Arrange
        mock_client_repository.exists_by_name.return_value = False

        # 1. Create client
        client = client_service.create_client(
            client_id=1,
            name="Lifecycle Client",
            created_by_admin_id=100,
            email="lifecycle@example.com"
        )
        assert client.enabled is True
        assert client.is_deleted is False

        # Update mock for subsequent operations
        mock_client_repository.get.return_value = client

        # 2. Update contact info
        updated = client_service.update_contact_info(
            client_id=1,
            phone="555-1234"
        )
        assert updated.phone.value == "555-1234"

        # 3. Disable client
        disabled = client_service.disable_client(client_id=1)
        assert disabled.enabled is False

        # 4. Enable client again
        enabled = client_service.enable_client(client_id=1)
        assert enabled.enabled is True

        # 5. Soft delete
        deleted = client_service.soft_delete_client(client_id=1)
        assert deleted.is_deleted is True

        # 6. Restore
        restored = client_service.restore_client(client_id=1)
        assert restored.is_deleted is False

        # 7. Hard delete
        client_service.hard_delete_client(client_id=1)
        mock_client_repository.hard_delete.assert_called_once_with(1)

    def test_cannot_modify_after_hard_delete(
            self,
            client_service: ClientService,
            mock_client_repository: Mock
    ):
        """Test that operations fail after client is hard deleted."""
        # Arrange
        mock_client_repository.get.side_effect = ItemValidationError("Client not found")

        # Act & Assert
        with pytest.raises(ItemValidationError, match="Client not found"):
            client_service.update_contact_info(client_id=1, email="test@example.com")

        with pytest.raises(ItemValidationError, match="Client not found"):
            client_service.disable_client(client_id=1)

        with pytest.raises(ItemValidationError, match="Client not found"):
            client_service.soft_delete_client(client_id=1)

    # ---------------------------
    # Edge Cases and Error Handling
    # ---------------------------


    def test_repository_save_failure(
            self,
            client_service: ClientService,
            mock_client_repository: Mock
    ):
        """Test handling of repository save failure."""
        # Arrange
        mock_client_repository.exists_by_name.return_value = False
        mock_client_repository.save.side_effect = RuntimeError("Database connection failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Database connection failed"):
            client_service.create_client(
                client_id=1,
                name="Test Client",
                created_by_admin_id=100
            )

    def test_concurrent_modification(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            sample_client: Client
    ):
        """Test handling of concurrent modifications (if repository implements versioning)."""
        # Arrange
        mock_client_repository.get.return_value = sample_client

        # Simulate version conflict
        def save_with_conflict(client):
            raise DomainOperationError("Version mismatch - client was modified by another user")

        mock_client_repository.save.side_effect = save_with_conflict

        # Act & Assert
        with pytest.raises(DomainOperationError, match="Version mismatch"):
            client_service.update_contact_info(
                client_id=1,
                email="conflict@example.com"
            )

    @pytest.mark.parametrize("invalid_client_id", [-1, 0, None])
    def test_operations_with_invalid_client_id(
            self,
            client_service: ClientService,
            mock_client_repository: Mock,
            invalid_client_id
    ):
        """Test various operations with invalid client IDs."""
        # Arrange
        mock_client_repository.get.side_effect = ItemValidationError(f"Client {invalid_client_id} not found")

        # Act & Assert
        operations = [
            lambda: client_service.update_contact_info(client_id=invalid_client_id, email="test@example.com"),
            lambda: client_service.disable_client(client_id=invalid_client_id),
            lambda: client_service.enable_client(client_id=invalid_client_id),
            lambda: client_service.soft_delete_client(client_id=invalid_client_id),
            lambda: client_service.restore_client(client_id=invalid_client_id),
        ]

        for operation in operations:
            with pytest.raises(ItemValidationError, match=f"Client {invalid_client_id} not found"):
                operation()