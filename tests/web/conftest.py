import pytest
import sqlite3
from fastapi.testclient import TestClient
from unittest.mock import Mock

from src.web.main import app
from utils.db.connect import Connection
from src.adapters.repositorysqlite import CreateDB
from src.services.service_layer.factory import ServiceFactory


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


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