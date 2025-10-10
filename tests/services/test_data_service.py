# tests/unit/services/test_data.py
import pytest
from src.services.service_layer.data import CreateAdminData


class TestCreateAdminData:
    """Test suite for CreateAdminData DTO"""

    def test_creation_with_all_fields(self):
        """Test CreateAdminData creation with all fields"""
        data = CreateAdminData(
            name="admin",
            email="admin@example.com",
            password="password123",
            enabled=True
        )

        assert data.name == "admin"
        assert data.email == "admin@example.com"
        assert data.password == "password123"
        assert data.enabled is True

    def test_creation_with_default_enabled(self):
        """Test CreateAdminData creation with default enabled"""
        data = CreateAdminData(
            name="admin",
            email="admin@example.com",
            password="password123"
        )

        assert data.enabled is True  # Default value

    def test_immutability(self):
        """Test that CreateAdminData is immutable"""
        data = CreateAdminData(
            name="admin",
            email="admin@example.com",
            password="password123"
        )

        with pytest.raises(Exception):  # Should be frozen
            data.name = "new_name"

    def test_equality(self):
        """Test CreateAdminData equality"""
        data1 = CreateAdminData(name="a", email="e", password="p")
        data2 = CreateAdminData(name="a", email="e", password="p")

        assert data1 == data2

    def test_representation(self):
        """Test CreateAdminData string representation"""
        data = CreateAdminData(name="admin", email="test@example.com", password="pwd")

        repr_str = repr(data)
        assert "CreateAdminData" in repr_str
        assert "admin" in repr_str


