# tests/unit/services/test_base_service.py
import pytest
from unittest.mock import Mock, create_autospec
import logging

from src.services.service_layer.base import BaseService
from src.services.uow.uowsqlite import AbstractUnitOfWork


class TestBaseService:
    """Test suite for BaseService abstract class"""

    @pytest.fixture
    def mock_uow(self):
        """Mock Unit of Work"""
        return create_autospec(AbstractUnitOfWork)

    @pytest.fixture
    def concrete_service(self, mock_uow):
        """Concrete implementation for testing abstract class"""

        class ConcreteService(BaseService):
            def execute(self, *args, **kwargs):
                return "result"

        return ConcreteService(uow=mock_uow)



    def test_validate_input_success(self, concrete_service):
        """Test _validate_input with valid parameters"""
        # Should not raise
        concrete_service._validate_input(name="test", value=123, flag=True)

    def test_validate_input_none_value(self, concrete_service):
        """Test _validate_input with None values"""
        with pytest.raises(ValueError, match="Parameter 'name' cannot be None"):
            concrete_service._validate_input(name=None, value="test")

    def test_validate_input_multiple_none(self, concrete_service):
        """Test _validate_input with multiple None values"""
        with pytest.raises(ValueError, match="Parameter 'email' cannot be None"):
            concrete_service._validate_input(name="test", email=None, age=None)

    def test_log_operation(self, concrete_service, caplog):
        """Test _log_operation method"""
        caplog.set_level(logging.INFO)

        concrete_service._log_operation("test_operation", user_id=123, action="create")

        assert "test_operation" in caplog.text
        assert "'user_id': 123" in caplog.text
        assert "'action': 'create'" in caplog.text

    def test_abstract_method_implementation(self):
        """Test that subclasses must implement execute method"""

        class IncompleteService(BaseService):
            pass  # Doesn't implement execute

        with pytest.raises(TypeError):
            IncompleteService(uow=Mock())


