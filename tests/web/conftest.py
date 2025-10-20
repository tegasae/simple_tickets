import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import Mock

from src.web.main import app
from src.web.config import get_settings


@pytest.fixture(scope="session")
def test_settings():
    """Return test settings"""
    return get_settings(environment='testing')


@pytest.fixture
def client(test_settings):
    """Create test client with test settings"""

    # Override the settings dependency
    def override_get_settings():
        return test_settings

    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def temp_db(test_settings):
    """Create a temporary database for testing (if not using in-memory)"""
    if test_settings.DATABASE_URL != ":memory:":
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            test_db_path = tmp.name

        original_db_url = test_settings.DATABASE_URL
        test_settings.DATABASE_URL = test_db_path

        yield test_db_path

        # Cleanup
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)
        test_settings.DATABASE_URL = original_db_url
    else:
        yield ":memory:"


@pytest.fixture
def sample_admin_data():
    """Sample admin data for testing"""
    return {
        "name": "testadmin",
        "email": "test@example.com",
        "password": "testpassword123",
        "enabled": True
    }


@pytest.fixture
def mock_admin():
    """Mock admin object for testing"""
    mock_admin = Mock()
    mock_admin.admin_id = 1
    mock_admin.name = "testadmin"
    mock_admin.email = "test@example.com"
    mock_admin.enabled = True
    mock_admin.date_created = "2023-01-01T00:00:00"
    return mock_admin

