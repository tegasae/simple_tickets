# tests/domain/test_client.py
"""Tests for Client domain entity."""

import pytest
from datetime import datetime

from src.domain.client import Client
from src.domain.exceptions import ItemValidationError
from src.domain.value_objects import Name, Email, Address, Phone


class TestClientCreation:
    """Test Client entity creation."""

    def test_create_client_with_all_fields(self):
        """Test creating a client with all fields provided."""
        client = Client.create(
            client_id=1,
            name="John Doe",
            email="john@example.com",
            address="123 Main St, City, 12345",
            phone="+1234567890",
            created_by_admin_id=100,
            enabled=True
        )

        assert client.client_id == 1
        assert isinstance(client.name, Name)
        assert str(client.name) == "John Doe"
        assert isinstance(client.email, Email)
        assert str(client.email) == "john@example.com"
        assert isinstance(client.address, Address)
        assert str(client.address) == "123 Main St, City, 12345"
        assert isinstance(client.phone, Phone)
        assert str(client.phone) == "+1234567890"
        assert client.created_by_admin_id == 100
        assert client.enabled is True
        assert isinstance(client.date_created, datetime)
        assert client.version == 0

    def test_create_client_with_minimal_fields(self):
        """Test creating a client with only required fields."""
        client = Client.create(
            client_id=1,
            name="Minimal Client",
            created_by_admin_id=100
        )

        assert client.client_id == 1
        assert str(client.name) == "Minimal Client"
        assert client.email is None
        assert client.address is None
        assert client.phone is None
        assert client.created_by_admin_id == 100
        assert client.enabled is True  # default

    def test_create_client_with_empty_name(self):
        """Test creating client with empty name raises error."""
        with pytest.raises(ItemValidationError, match="cannot be empty"):
            Client.create(
                client_id=1,
                name="",
                created_by_admin_id=100
            )

    def test_create_client_with_invalid_email(self):
        """Test creating client with invalid email raises error."""
        with pytest.raises(ItemValidationError, match="Invalid email format"):
            Client.create(
                client_id=1,
                name="Test Client",
                email="not-an-email",
                created_by_admin_id=100
            )


    def test_create_client_with_negative_admin_id(self):
        """Test creating client with negative admin ID raises error."""
        with pytest.raises(ItemValidationError, match="Admin ID cannot be negative"):
            Client.create(
                client_id=1,
                name="Test Client",
                created_by_admin_id=-1
            )

    @pytest.mark.parametrize("name", [
        "A" * 101,  # Too long

    ])
    def test_create_client_with_invalid_name(self, name):
        """Test creating client with invalid names."""
        with pytest.raises(ItemValidationError, match="failed:"):
            Client.create(
                client_id=1,
                name=name,
                created_by_admin_id=100
            )


class TestClientEquality:
    """Test Client equality and hashing."""

    def test_clients_equal_same_id(self):
        """Test clients with same ID are equal."""
        client1 = Client.create(client_id=1, name="Client A", created_by_admin_id=100)
        client2 = Client.create(client_id=1, name="Client B", created_by_admin_id=100)

        assert client1 == client2
        assert hash(client1) == hash(client2)

    def test_clients_not_equal_different_id(self):
        """Test clients with different IDs are not equal."""
        client1 = Client.create(client_id=1, name="Client A", created_by_admin_id=100)
        client2 = Client.create(client_id=2, name="Client A", created_by_admin_id=100)

        assert client1 != client2
        assert hash(client1) != hash(client2)

    def test_client_not_equal_to_non_client(self):
        """Test client not equal to non-client object."""
        client = Client.create(client_id=1, name="Client A", created_by_admin_id=100)
        assert client != "not a client"


class TestClientEnableDisable:
    """Test client enable/disable functionality."""

    @pytest.fixture
    def client(self):
        return Client.create(
            client_id=1,
            name="Test Client",
            created_by_admin_id=100
        )

    def test_disable_client(self, client):
        """Test disabling a client."""
        assert client.enabled is True
        initial_version = client.version

        client.disable()

        assert client.enabled is False
        assert client.version == initial_version + 1

    def test_enable_client(self, client):
        """Test enabling a client."""
        client.disable()
        assert client.enabled is False
        initial_version = client.version

        client.enable()

        assert client.enabled is True
        assert client.version == initial_version + 1

    def test_disable_already_disabled(self, client):
        """Test disabling an already disabled client."""
        client.disable()
        assert client.enabled is False
        initial_version = client.version

        client.disable()  # Disable again

        assert client.enabled is False  # Still false
        assert client.version == initial_version + 1  # Version still increments


class TestClientContactInfo:
    """Test client contact information updates."""

    @pytest.fixture
    def client(self):
        return Client.create(
            client_id=1,
            name="Test Client",
            email="original@example.com",
            address="Original Address",
            phone="+1111111111",
            created_by_admin_id=100
        )

    def test_update_all_contact_info(self, client):
        """Test updating all contact fields."""
        initial_version = client.version

        client.update_contact_info(
            email="new@example.com",
            address="New Address",
            phone="+2222222222"
        )

        assert str(client.email) == "new@example.com"
        assert str(client.address) == "New Address"
        assert str(client.phone) == "+2222222222"
        assert client.version == initial_version + 1

    def test_update_single_field(self, client):
        """Test updating only one contact field."""
        original_email = client.email
        original_address = client.address
        initial_version = client.version

        client.update_contact_info(phone="+3333333333")

        assert client.email == original_email  # Unchanged
        assert client.address == original_address  # Unchanged
        assert str(client.phone) == "+3333333333"
        assert client.version == initial_version + 1

    def test_update_to_none(self, client):
        """Test setting contact fields to None."""
        client.update_contact_info(
            email="",
            address="",
            phone=""
        )

        assert client.email is None
        assert client.address is None
        assert client.phone is None

    def test_update_with_invalid_email(self, client):
        """Test updating with invalid email raises error."""
        with pytest.raises(ItemValidationError, match="Invalid email format"):
            client.update_contact_info(email="invalid-email")


    def test_contact_summary(self, client):
        """Test getting contact summary."""
        summary = client.get_contact_summary()

        assert summary["name"] == "Test Client"
        assert summary["email"] == "original@example.com"
        assert summary["address"] == "Original Address"
        assert summary["phone"] == "+1111111111"

    def test_contact_summary_with_none_fields(self):
        """Test contact summary with None fields."""
        client = Client.create(
            client_id=1,
            name="Test Client",
            created_by_admin_id=100
        )

        summary = client.get_contact_summary()

        assert summary["name"] == "Test Client"
        assert summary["email"] is None
        assert summary["address"] is None
        assert summary["phone"] is None


class TestClientStringRepresentation:
    """Test Client string representation."""

    def test_str_representation(self):
        """Test string representation of client."""
        client = Client.create(
            client_id=1,
            name="Test Client",
            created_by_admin_id=100
        )

        assert str(client) == "Client(id=1, name=Test Client)"

    def test_repr_representation(self):
        """Test repr representation of client."""
        client = Client.create(
            client_id=1,
            name="Test Client",
            created_by_admin_id=100
        )

        repr_str = repr(client)
        assert "Client" in repr_str
        assert "client_id=1" in repr_str
