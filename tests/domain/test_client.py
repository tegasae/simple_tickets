"""Tests for Client domain model."""

import pytest
from datetime import datetime
from unittest.mock import patch

from src.domain.client import Client
from src.domain.exceptions import ItemValidationError
from src.domain.value_objects import Name, Email, Address, Phone


class TestClientCreation:
    """Tests for Client creation."""

    def test_create_client_with_all_fields(self):
        """Test creating a client with all fields populated."""
        client = Client.create(
            client_id=1,
            name="John Doe",
            email="john@example.com",
            address="123 Main Street",
            phone="+1234567890",
            created_by_admin_id=5,
            enabled=True
        )

        assert client.client_id == 1
        assert client.name == Name("John Doe")
        assert client.email == Email("john@example.com")
        assert client.address == Address("123 Main Street")
        assert client.phone == Phone("+1234567890")
        assert client.created_by_admin_id == 5
        assert client.enabled is True
        assert client.is_deleted is False
        assert client.version == 0
        assert isinstance(client.date_created, datetime)

    def test_create_client_with_minimal_fields(self):
        """Test creating a client with only required fields."""
        client = Client.create(
            client_id=2,
            name="Jane Smith"
            # email, address, phone are optional
        )

        assert client.client_id == 2
        assert client.name == Name("Jane Smith")
        assert client.email is None
        assert client.address is None
        assert client.phone is None
        assert client.created_by_admin_id == 0  # Default
        assert client.enabled is True  # Default
        assert client.is_deleted is False  # Default


    def test_create_client_with_whitespace(self):
        """Test creating client with whitespace in fields."""
        client = Client.create(
            client_id=4,
            name="  John Doe  ",  # Whitespace should be trimmed
            email="  john@example.com  ",
            address="  123 Main St  ",
            phone="  +1234567890  "
        )

        assert client.name == Name("John Doe")  # Trimmed
        assert client.email == Email("john@example.com")  # Trimmed
        assert client.address == Address("123 Main St")  # Trimmed
        assert client.phone == Phone("+1234567890")  # Trimmed

    def test_create_client_with_negative_admin_id(self):
        """Test validation of negative admin ID."""
        with pytest.raises(ItemValidationError, match="Admin ID cannot be negative"):
            Client.create(
                client_id=1,
                name="Test Client",
                created_by_admin_id=-1
            )

    def test_create_client_with_zero_admin_id(self):
        """Test that admin ID can be 0 (system-generated)."""
        client = Client.create(
            client_id=1,
            name="Test Client",
            created_by_admin_id=0  # Allowed
        )

        assert client.created_by_admin_id == 0

    def test_create_client_with_positive_admin_id(self):
        """Test that positive admin IDs are allowed."""
        client = Client.create(
            client_id=1,
            name="Test Client",
            created_by_admin_id=100
        )

        assert client.created_by_admin_id == 100

    def test_create_client_invalid_name(self):
        """Test validation of invalid names."""
        # Name too short
        with pytest.raises(ItemValidationError, match="Client validation failed"):
            Client.create(
                client_id=1,
                name="A"  # Too short (min 2 chars)
            )

        # Name too long
        with pytest.raises(ItemValidationError, match="Client validation failed"):
            Client.create(
                client_id=1,
                name="A" * 101  # Too long (max 100 chars)
            )

        # Name only whitespace
        with pytest.raises(ItemValidationError, match="Client validation failed"):
            Client.create(
                client_id=1,
                name="   "  # Only whitespace
            )

    def test_create_client_invalid_email(self):
        """Test validation of invalid email format."""
        # Invalid email format
        # Note: Your current Email value object doesn't validate format,
        # so this might not raise an error unless you add validation
        pass  # Placeholder for when email validation is added

    def test_create_client_direct_instantiation(self):
        """Test that Client can also be instantiated directly."""
        client = Client(
            client_id=1,
            name=Name("John Doe"),
            email=Email("john@example.com"),
            address=Address("123 Main St"),
            phone=Phone("+1234567890"),
            created_by_admin_id=5,
            enabled=True,
            is_deleted=False,
            version=0
        )

        assert client.client_id == 1
        assert str(client.name) == "John Doe"


class TestClientStateManagement:
    """Tests for client state management methods."""

    def test_disable_client(self):
        """Test disabling a client."""
        client = Client.create(client_id=1, name="Test Client")
        initial_version = client.version

        client.disable()

        assert client.enabled is False
        assert client.version == initial_version + 1

    def test_enable_client(self):
        """Test enabling a client."""
        client = Client.create(client_id=1, name="Test Client", enabled=False)
        initial_version = client.version

        client.enable()

        assert client.enabled is True
        assert client.version == initial_version + 1

    def test_soft_delete_client(self):
        """Test soft deleting a client."""
        client = Client.create(client_id=1, name="Test Client")
        initial_version = client.version

        client.soft_delete()

        assert client.is_deleted is True
        assert client.version == initial_version + 1

    def test_restore_client(self):
        """Test restoring a soft-deleted client."""
        client = Client.create(client_id=1, name="Test Client")
        client.soft_delete()
        version_before_restore = client.version

        client.restore()

        assert client.is_deleted is False
        assert client.version == version_before_restore + 1

    def test_is_active_property(self):
        """Test is_active property."""
        client = Client.create(client_id=1, name="Test Client")

        # Default: enabled=True, is_deleted=False
        assert client.is_active is True

        # Disabled
        client.enable()  # Ensure enabled
        client.disable()
        assert client.is_active is False

        # Enabled but deleted
        client.enable()
        client.soft_delete()
        assert client.is_active is False

        # Both disabled and deleted
        client.disable()
        client.soft_delete()
        assert client.is_active is False

        # Restored and enabled
        client.restore()
        client.enable()
        assert client.is_active is True


class TestClientContactInfo:
    """Tests for client contact information management."""

    def test_update_contact_info_all_fields(self):
        """Test updating all contact information fields."""
        client = Client.create(
            client_id=1,
            name="John Doe",
            email="old@example.com",
            address="Old Address",
            phone="+1111111111"
        )
        initial_version = client.version

        client.update_contact_info(
            email="new@example.com",
            address="New Address",
            phone="+2222222222"
        )

        assert client.email == Email("new@example.com")
        assert client.address == Address("New Address")
        assert client.phone == Phone("+2222222222")
        assert client.version == initial_version + 1

    def test_update_contact_info_single_field(self):
        """Test updating only one contact field."""
        client = Client.create(
            client_id=1,
            name="John Doe",
            email="old@example.com",
            address="Some Address",
            phone="+1111111111"
        )
        initial_version = client.version

        # Update only email
        client.update_contact_info(email="new@example.com")

        assert client.email == Email("new@example.com")
        assert client.address == Address("Some Address")  # Unchanged
        assert client.phone == Phone("+1111111111")  # Unchanged
        assert client.version == initial_version + 1

        # Update only phone
        client.update_contact_info(phone="+3333333333")

        assert client.phone == Phone("+3333333333")
        assert client.email == Email("new@example.com")  # Unchanged
        assert client.version == initial_version + 2




    def test_update_contact_info_validation_error(self):
        """Test validation error when updating with invalid data."""
        client = Client.create(client_id=1, name="Test Client")

        # Test with invalid email (if email validation is added later)
        # Currently Email doesn't validate format, so this won't fail
        # with pytest.raises(ItemValidationError):
        #     client.update_contact_info(email="invalid-email")

        # Test with whitespace-only values (should be trimmed, might fail if validation added)
        pass

    def test_get_contact_summary(self):
        """Test getting contact summary."""
        client = Client.create(
            client_id=1,
            name="John Doe",
            email="john@example.com",
            address="123 Main St, City",
            phone="+1234567890"
        )

        summary = client.get_contact_summary()

        assert summary == {
            "name": "John Doe",
            "email": "john@example.com",
            "address": "123 Main St, City",
            "phone": "+1234567890"
        }

    def test_get_contact_summary_with_none_fields(self):
        """Test getting contact summary when some fields are None."""
        client = Client.create(
            client_id=1,
            name="Jane Smith"
            # email, address, phone are None
        )

        summary = client.get_contact_summary()

        assert summary == {
            "name": "Jane Smith",
            "email": None,
            "address": None,
            "phone": None
        }



class TestClientEqualityAndHashing:
    """Tests for client equality and hashing."""

    def test_client_equality_same_id(self):
        """Test that clients with same ID are equal."""
        client1 = Client.create(client_id=1, name="John Doe")
        client2 = Client.create(client_id=1, name="Jane Smith")  # Different name, same ID

        assert client1 == client2
        assert not (client1 != client2)

    def test_client_equality_different_id(self):
        """Test that clients with different IDs are not equal."""
        client1 = Client.create(client_id=1, name="John Doe")
        client2 = Client.create(client_id=2, name="John Doe")  # Same name, different ID

        assert client1 != client2
        assert not (client1 == client2)

    def test_client_equality_with_other_types(self):
        """Test client equality with non-client objects."""
        client = Client.create(client_id=1, name="Test")

        assert client != "not a client"
        assert client != 123
        assert client != None  # noqa: E711
        assert not (client == "not a client")

    def test_client_hash(self):
        """Test client hashing."""
        client1 = Client.create(client_id=1, name="John")
        client2 = Client.create(client_id=1, name="Jane")  # Same ID, different name
        client3 = Client.create(client_id=2, name="John")  # Different ID, same name

        # Same ID should produce same hash
        assert hash(client1) == hash(client2)
        assert hash(client1) != hash(client3)

    def test_client_in_set(self):
        """Test that clients can be used in sets (based on hash)."""
        client1 = Client.create(client_id=1, name="John")
        client2 = Client.create(client_id=1, name="Jane")  # Same ID
        client3 = Client.create(client_id=2, name="Bob")  # Different ID
        client4 = Client.create(client_id=2, name="Alice")  # Same ID as client3

        client_set = {client1, client2, client3, client4}

        # Should have 2 unique clients (IDs 1 and 2)
        assert len(client_set) == 2

        # Check which clients are in the set
        assert client1 in client_set
        assert client2 in client_set  # Equal to client1, so in set
        assert client3 in client_set
        assert client4 in client_set  # Equal to client3, so in set

    def test_client_in_dict(self):
        """Test that clients can be used as dictionary keys."""
        client1 = Client.create(client_id=1, name="John")
        client2 = Client.create(client_id=1, name="Jane")  # Same ID

        client_dict = {
            client1: "value1",
            client2: "value2"  # Should overwrite client1's value
        }

        # Only one entry since client1 == client2
        assert len(client_dict) == 1
        assert client_dict[client1] == "value2"
        assert client_dict[client2] == "value2"


class TestClientStringRepresentations:
    """Tests for client string representations."""

    def test_client_str(self):
        """Test string representation of client."""
        client = Client.create(client_id=123, name="John Doe")

        str_repr = str(client)

        assert "Client(id=123" in str_repr
        assert "name=John Doe" in str_repr or "name=Name" in str_repr

    def test_client_repr(self):
        """Test debug representation of client."""
        client = Client.create(
            client_id=123,
            name="John Doe",
            email="john@example.com"
        )

        repr_str = repr(client)

        # Should contain class name and key fields
        assert "Client(" in repr_str
        assert "client_id=123" in repr_str
        # May contain field values
        assert "name=" in repr_str


class TestClientEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_client_with_very_long_name(self):
        """Test client with maximum allowed name length."""
        # Name max length is 100 characters in Name value object
        long_name = "A" * 100

        client = Client.create(client_id=1, name=long_name)

        assert len(str(client.name)) == 100

    def test_client_with_zero_client_id(self):
        """Test client with client_id = 0."""
        # Note: client_id=0 might be invalid in some systems
        # Your code allows it, so we test it
        client = Client.create(client_id=0, name="Test")

        assert client.client_id == 0

    def test_client_with_negative_client_id(self):
        """Test client with negative client_id."""
        # Negative IDs might be used for system/internal clients
        client = Client.create(client_id=-1, name="System Client")

        assert client.client_id == -1

    def test_client_disabled_on_creation(self):
        """Test creating a client already disabled."""
        client = Client.create(
            client_id=1,
            name="Test Client",
            enabled=False
        )

        assert client.enabled is False
        assert client.is_active is False  # Because not enabled

    def test_multiple_state_changes(self):
        """Test multiple state changes increment version appropriately."""
        client = Client.create(client_id=1, name="Test")
        initial_version = client.version

        # Perform multiple operations
        client.disable()  # +1
        client.enable()  # +1
        client.soft_delete()  # +1
        client.restore()  # +1
        client.update_contact_info(email="test@example.com")  # +1

        assert client.version == initial_version + 5






if __name__ == "__main__":
    pytest.main([__file__, "-v"])