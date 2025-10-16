import sqlite3

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from src.adapters.repositorysqlite import CreateDB
from src.services.service_layer.factory import ServiceFactory
from src.web.main import app
from src.services.service_layer.data import CreateAdminData
from utils.db.connect import Connection

client = TestClient(app)

#@pytest.fixture
#def client():
#    """Test client fixture"""
#    return TestClient(app)


@pytest.fixture
def in_memory_connection():
    """In-memory database connection for testing"""
    conn = Connection.create_connection(url=":memory:", engine=sqlite3)
    yield conn
    conn.close()


@pytest.fixture
def initialized_db(in_memory_connection):
    """Database with initialized schema"""
    create_db = CreateDB(in_memory_connection)
    create_db.init_data()
    create_db.create_indexes()
    return in_memory_connection


@pytest.fixture
def mock_service_factory():
    """Mock service factory"""
    factory = Mock(spec=ServiceFactory)
    factory.get_admin_service.return_value = Mock()
    return factory


@pytest.fixture
def sample_admin_data():
    """Sample admin data for testing"""
    return {
        "name": "test_admin",
        "email": "test@example.com",
        "password": "testpassword123",
        "enabled": True
    }


class TestAdminRoutes:
    """Test admin router endpoints"""

    def test_create_admin_success(self, sample_admin_data):
        """Test successful admin creation"""
        with patch('src.web.routers.admins.get_service_factory') as mock_factory:
            mock_service = mock_factory.return_value.get_admin_service.return_value
            mock_admin = Mock()
            mock_admin.admin_id = 1
            mock_admin.name = sample_admin_data["name"]
            mock_admin.email = sample_admin_data["email"]
            mock_admin.enabled = sample_admin_data["enabled"]
            mock_admin.date_created = "2023-01-01T00:00:00"

            mock_service.execute.return_value = mock_admin

            response = client.post("/admins/", json=sample_admin_data)

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == sample_admin_data["name"]
            assert data["email"] == sample_admin_data["email"]
            assert data["enabled"] == sample_admin_data["enabled"]

    def test_get_all_admins(self):
        """Test getting all admins"""
        with patch('src.web.routers.admins.get_service_factory') as mock_factory:
            mock_service = mock_factory.return_value.get_admin_service.return_value

            # Mock multiple admins
            mock_admin1 = Mock()
            mock_admin1.admin_id = 1
            mock_admin1.name = "admin1"
            mock_admin1.email = "admin1@example.com"
            mock_admin1.enabled = True
            mock_admin1.date_created = "2023-01-01T00:00:00"

            mock_admin2 = Mock()
            mock_admin2.admin_id = 2
            mock_admin2.name = "admin2"
            mock_admin2.email = "admin2@example.com"
            mock_admin2.enabled = False
            mock_admin2.date_created = "2023-01-02T00:00:00"

            mock_service.list_all_admins.return_value = [mock_admin1, mock_admin2]

            response = client.get("/admins/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "admin1"
            assert data[1]["name"] == "admin2"

    def test_get_admin_by_id(self):
        """Test getting admin by ID"""
        with patch('src.web.routers.admins.get_service_factory') as mock_factory:
            mock_service = mock_factory.return_value.get_admin_service.return_value

            mock_admin = Mock()
            mock_admin.admin_id = 1
            mock_admin.name = "test_admin"
            mock_admin.email = "test@example.com"
            mock_admin.enabled = True
            mock_admin.date_created = "2023-01-01T00:00:00"

            mock_service.execute.return_value = mock_admin

            response = client.get("/admins/1")

            assert response.status_code == 200
            data = response.json()
            assert data["admin_id"] == 1
            assert data["name"] == "test_admin"

    def test_get_admin_by_name(self):
        """Test getting admin by name"""
        with patch('src.web.routers.admins.get_service_factory') as mock_factory:
            mock_service = mock_factory.return_value.get_admin_service.return_value

            mock_admin = Mock()
            mock_admin.admin_id = 1
            mock_admin.name = "test_admin"
            mock_admin.email = "test@example.com"
            mock_admin.enabled = True
            mock_admin.date_created = "2023-01-01T00:00:00"

            mock_service.execute.return_value = mock_admin

            response = client.get("/admins/name/test_admin")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "test_admin"

    def test_update_admin(self):
        """Test updating admin"""
        with patch('src.web.routers.admins.get_service_factory') as mock_factory:
            mock_service = mock_factory.return_value.get_admin_service.return_value

            # Mock existing admin
            mock_admin = Mock()
            mock_admin.admin_id = 1
            mock_admin.name = "test_admin"
            mock_admin.email = "old@example.com"
            mock_admin.enabled = True

            mock_service.execute.return_value = mock_admin

            update_data = {
                "email": "new@example.com",
                "enabled": False
            }

            response = client.put("/admins/1", json=update_data)

            assert response.status_code == 200
            # Verify service methods were called
            assert mock_service.execute.call_count >= 2

    def test_delete_admin(self):
        """Test deleting admin"""
        with patch('src.web.routers.admins.get_service_factory') as mock_factory:
            mock_service = mock_factory.return_value.get_admin_service.return_value

            # Mock existing admin for the get_by_id call
            mock_admin = Mock()
            mock_admin.admin_id = 1
            mock_admin.name = "test_admin"

            mock_service.execute.return_value = mock_admin

            response = client.delete("/admins/1")

            assert response.status_code == 204
            mock_service.execute.assert_called_with('remove_by_id', admin_id=1)

    def test_toggle_admin_status(self):
        """Test toggling admin status"""
        with patch('src.web.routers.admins.get_service_factory') as mock_factory:
            mock_service = mock_factory.return_value.get_admin_service.return_value

            # Mock existing admin
            mock_admin = Mock()
            mock_admin.admin_id = 1
            mock_admin.name = "test_admin"
            mock_admin.enabled = True

            mock_service.execute.return_value = mock_admin

            response = client.post("/admins/1/toggle-status")

            assert response.status_code == 200
            mock_service.execute.assert_called_with('toggle_status', name="test_admin")

    def test_check_admin_exists(self):
        """Test checking if admin exists"""
        with patch('src.web.routers.admins.get_service_factory') as mock_factory:
            mock_service = mock_factory.return_value.get_admin_service.return_value
            mock_service.admin_exists.return_value = True

            response = client.get("/admins/check/test_admin/exists")

            assert response.status_code == 200
            data = response.json()
            assert data["exists"] is True

