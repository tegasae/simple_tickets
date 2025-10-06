import pytest
from unittest.mock import Mock, patch, MagicMock
import logging
from typing import ContextManager

from src.adapters import repository, repositorysqlite
from utils.db.connect import Connection
from src.services.uow.uowsqlite import AbstractUnitOfWork, SqliteUnitOfWork


# ==================== FIXTURES (Move to module level) ====================

@pytest.fixture
def mock_connection():
    """Create a mock database connection - available to ALL test classes"""
    mock_conn = Mock(spec=Connection)
    mock_conn.begin_transaction = Mock()
    mock_conn.commit = Mock()
    mock_conn.rollback = Mock()
    return mock_conn


@pytest.fixture
def mock_repository():
    """Create a mock admin repository - available to ALL test classes"""
    return Mock(spec=repository.AdminRepositoryAbstract)


@pytest.fixture
def uow(mock_connection, mock_repository):
    """Create Unit of Work with mocked dependencies - available to ALL test classes"""
    with patch('src.adapters.repositorysqlite.SQLiteAdminRepository') as mock_repo_class:
        mock_repo_class.return_value = mock_repository
        return SqliteUnitOfWork(mock_connection)


@pytest.fixture
def real_mock_repository():
    """Create a more realistic mock repository - available to ALL test classes"""
    repo = Mock(spec=repositorysqlite.SQLiteAdminRepository)
    repo.get_list_of_admins = Mock(return_value=Mock())
    repo.save_admins = Mock()
    return repo


# ==================== TEST CLASSES ====================

class TestAbstractUnitOfWork:
    """Tests for the abstract base class interface"""

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that AbstractUnitOfWork cannot be instantiated"""
        with pytest.raises(TypeError):
            AbstractUnitOfWork()  # type: ignore

    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined"""
        abstract_methods = {
            '__enter__', '__exit__', 'commit', 'rollback', 'is_active'
        }
        abstract_properties = {'admins'}

        # Check methods
        for method_name in abstract_methods:
            assert hasattr(AbstractUnitOfWork, method_name)
            method = getattr(AbstractUnitOfWork, method_name)
            assert getattr(method, '__isabstractmethod__', False)

        # Check properties
        assert hasattr(AbstractUnitOfWork, 'admins')
        assert getattr(AbstractUnitOfWork.admins, '__isabstractmethod__', False)


class TestSqliteUnitOfWork:
    """Tests for the SQLite Unit of Work implementation"""

    def test_initialization(self, mock_connection, mock_repository):
        """Test that UoW initializes correctly"""
        with patch('src.adapters.repositorysqlite.SQLiteAdminRepository') as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            uow = SqliteUnitOfWork(mock_connection)

            # Check attributes
            assert uow.connection == mock_connection
            assert uow._active is False
            assert uow._committed is False
            assert uow.admins_repository == mock_repository

            # Verify repository was created with correct connection
            mock_repo_class.assert_called_once_with(conn=mock_connection)

    def test_context_manager_entrance(self, uow, mock_connection):
        """Test that entering context starts transaction"""
        with uow as context:
            # Should return self
            assert context is uow

            # Should be active
            assert uow.is_active() is True
            assert uow._active is True
            assert uow._committed is False

            # Should have started transaction
            mock_connection.begin_transaction.assert_called_once()

    def test_commit_success(self, uow, mock_connection):
        """Test successful commit"""
        with uow:
            uow.commit()

            # Should call connection commit
            mock_connection.commit.assert_called_once()

            # Should update state
            assert uow._committed is True
            assert uow.is_active() is True  # Still active until context exit

    def test_commit_without_active_transaction(self, uow):
        """Test that commit fails without active transaction"""
        # Not in context manager
        with pytest.raises(RuntimeError, match="No active transaction to commit"):
            uow.commit()

    def test_rollback_success(self, uow, mock_connection):
        """Test successful rollback"""
        with uow:
            uow.rollback()

            # Should call connection rollback
            mock_connection.rollback.assert_called_once()

            # Should update state
            assert uow._committed is True  # Marked as handled
            assert uow.is_active() is True  # Still active until context exit

    def test_rollback_without_active_transaction(self, uow, mock_connection):
        """Test rollback without active transaction does nothing"""
        uow.rollback()

        # Should not call connection rollback
        mock_connection.rollback.assert_not_called()

    def test_admins_property(self, uow, mock_repository):
        """Test that admins property returns repository"""
        assert uow.admins == mock_repository
        assert uow.admins is uow.admins_repository

    def test_auto_rollback_on_exception(self, uow, mock_connection):
        """Test automatic rollback when exception occurs in context"""
        with pytest.raises(ValueError):
            with uow:
                raise ValueError("Test exception")

        # Should have rolled back automatically
        mock_connection.rollback.assert_called_once()
        assert uow._active is False

    def test_auto_rollback_no_commit(self, uow, mock_connection):
        """Test automatic rollback when no commit is called"""
        with uow:
            # Do some work but forget to commit
            pass

        # Should have rolled back automatically
        mock_connection.rollback.assert_called_once()
        assert uow._active is False

    def test_successful_transaction_flow(self, uow, mock_connection):
        """Test complete successful transaction flow"""
        with uow:
            # Do some work
            uow.commit()

        # Should have called begin and commit, but not rollback
        mock_connection.begin_transaction.assert_called_once()
        mock_connection.commit.assert_called_once()
        mock_connection.rollback.assert_not_called()
        assert uow._active is False
        assert uow._committed is True

    def test_is_active(self, uow):
        """Test is_active method"""
        assert uow.is_active() is False

        with uow:
            assert uow.is_active() is True

        assert uow.is_active() is False

    def test_context_manager_protocol(self):
        """Test that UoW properly implements ContextManager protocol"""
        # Should inherit from ContextManager
        assert issubclass(SqliteUnitOfWork, ContextManager)

        # Should have required methods
        assert hasattr(SqliteUnitOfWork, '__enter__')
        assert hasattr(SqliteUnitOfWork, '__exit__')

    def test_abstract_implementation(self):
        """Test that SqliteUnitOfWork implements all abstract methods"""
        # Should not be abstract
        assert not getattr(SqliteUnitOfWork, '__abstractmethods__', set())

        # Check all abstract methods are implemented
        abstract_methods = AbstractUnitOfWork.__abstractmethods__
        for method_name in abstract_methods:
            method = getattr(SqliteUnitOfWork, method_name)
            assert not getattr(method, '__isabstractmethod__', False)


class TestSqliteUnitOfWorkIntegration:
    """Integration-style tests with more realistic mocks"""

    def test_usage_pattern(self, mock_connection, real_mock_repository):
        """Test typical usage pattern"""
        with patch('src.adapters.repositorysqlite.SQLiteAdminRepository') as mock_repo_class:
            mock_repo_class.return_value = real_mock_repository

            uow = SqliteUnitOfWork(mock_connection)

            # Simulate typical service usage
            with uow:
                aggregate = uow.admins.get_list_of_admins()
                # Do some business logic...
                uow.admins.save_admins(aggregate)
                uow.commit()

            # Verify interactions
            mock_connection.begin_transaction.assert_called_once()
            mock_connection.commit.assert_called_once()
            real_mock_repository.get_list_of_admins.assert_called_once()
            real_mock_repository.save_admins.assert_called_once()


class TestErrorScenarios:
    """Test error handling and edge cases"""

    def test_commit_after_context_exit(self, mock_connection):
        """Test that commit fails after context exit"""
        with patch('src.adapters.repositorysqlite.SQLiteAdminRepository'):
            uow = SqliteUnitOfWork(mock_connection)

            with uow:
                pass  # Context exits without commit

            # Try to commit after context exit
            with pytest.raises(RuntimeError, match="No active transaction to commit"):
                uow.commit()

    def test_double_commit(self, uow, mock_connection):
        """Test committing twice in same transaction"""
        with uow:
            uow.commit()

            # Second commit should work (depends on your connection implementation)
            uow.commit()

            # Should have called commit twice
            assert mock_connection.commit.call_count == 2

    def test_exception_during_cleanup(self, mock_connection, caplog):
        """Test behavior when rollback fails during cleanup"""
        # Create a fresh UoW for this specific test
        with patch('src.adapters.repositorysqlite.SQLiteAdminRepository'):
            uow = SqliteUnitOfWork(mock_connection)

            # Make rollback raise an exception
            mock_connection.rollback.side_effect = Exception("Rollback failed!")

            with pytest.raises(ValueError):  # Original exception
                with uow:
                    raise ValueError("Original error")

            # Should log the cleanup error but not mask original exception
            assert "Error during transaction cleanup" in caplog.text
            assert "Rollback failed" in caplog.text


class TestLogging:
    """Test logging behavior"""

    def test_logging_on_commit(self, uow, mock_connection, caplog):
        """Test that commits are logged"""
        with uow:
            with caplog.at_level(logging.INFO):
                uow.commit()

            assert "SQLite transaction committed" in caplog.text

    def test_logging_on_rollback(self, uow, mock_connection, caplog):
        """Test that rollbacks are logged"""
        with uow:
            with caplog.at_level(logging.INFO):
                uow.rollback()

            assert "SQLite transaction rolled back" in caplog.text

    def test_warning_on_auto_rollback(self, uow, mock_connection, caplog):
        """Test warning when auto-rollback occurs"""
        with caplog.at_level(logging.WARNING):
            with uow:
                pass  # No commit called

            assert "Auto-rollback: no commit called" in caplog.text


# Test configuration
pytestmark = pytest.mark.unit


def test_imports():
    """Test that all required imports are available"""
    # This test ensures the module can be imported without errors
    from src.services.uow.uowsqlite import AbstractUnitOfWork, SqliteUnitOfWork
    assert AbstractUnitOfWork is not None
    assert SqliteUnitOfWork is not None