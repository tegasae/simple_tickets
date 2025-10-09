# tests/unit/db/test_connection.py
import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock
import logging

from utils.db.connect import Connection
from utils.db.exceptions import DBConnectError, DBOperationError
from utils.db.query import Query

@pytest.fixture
def mock_engine():
    """Mock database engine"""
    engine = Mock()
    engine.connect = Mock()
    engine.paramstyle = "named"
    return engine

@pytest.fixture
def mock_connect():
    """Mock database connection"""
    connect = Mock()
    connect.cursor = Mock()
    connect.execute = Mock()
    connect.commit = Mock()
    connect.rollback = Mock()
    connect.close = Mock()
    return connect

@pytest.fixture
def connection(mock_engine, mock_connect):
    """Connection instance with mocked dependencies"""
    mock_engine.connect.return_value = mock_connect
    return Connection(connect=mock_connect, engine=mock_engine)

@pytest.fixture
def in_memory_connection():
    """Real SQLite in-memory connection for integration tests"""
    conn = Connection.create_connection(url=":memory:", engine=sqlite3)
    yield conn
    if conn.is_connected():
        conn.close()


class TestConnection:
    """Test suite for Connection class"""



    # Test Initialization
    def test_init(self, mock_engine, mock_connect):
        """Test Connection initialization"""
        conn = Connection(connect=mock_connect, engine=mock_engine)

        assert conn.connect == mock_connect
        assert conn.engine == mock_engine
        assert conn._in_transaction is False
        assert conn._is_closed is False

    def test_init_default_values(self,mock_engine):
        """Test Connection initialization with default values"""

        conn = Connection(engine=mock_engine)

        assert conn.connect is None
        assert conn.engine is mock_engine
        assert conn._in_transaction is False
        assert conn._is_closed is False

    # Test create_connection class method
    def test_create_connection_success(self, mock_engine, mock_connect):
        """Test successful connection creation"""
        mock_engine.connect.return_value = mock_connect

        # Execute
        conn = Connection.create_connection(url=":memory:", engine=mock_engine)

        # Assert
        assert isinstance(conn, Connection)
        assert conn.connect == mock_connect
        assert conn.engine == mock_engine
        mock_engine.connect.assert_called_once_with(":memory:")

    def test_create_connection_missing_url(self, mock_engine):
        """Test connection creation with missing URL"""
        with pytest.raises(DBConnectError, match="URL and engine must be provided"):
            Connection.create_connection(url="", engine=mock_engine)

    def test_create_connection_missing_engine(self):
        """Test connection creation with missing engine"""
        with pytest.raises(DBConnectError, match="URL and engine must be provided"):
            Connection.create_connection(url=":memory:", engine=None)

    def test_create_connection_invalid_engine(self):
        """Test connection creation with invalid engine"""
        invalid_engine = Mock()
        delattr(invalid_engine, 'connect')  # Remove connect method

        with pytest.raises(DBConnectError, match="Engine must have a connect method"):
            Connection.create_connection(url=":memory:", engine=invalid_engine)

    def test_create_connection_engine_error(self, mock_engine):
        """Test connection creation when engine fails"""
        mock_engine.connect.side_effect = Exception("Connection failed")

        with pytest.raises(DBConnectError, match="Failed to connect to :memory:"):
            Connection.create_connection(url=":memory:", engine=mock_engine)

    def test_create_connection_sets_paramstyle(self, mock_engine, mock_connect):
        """Test that paramstyle is set to named"""
        mock_engine.connect.return_value = mock_connect

        conn = Connection.create_connection(url=":memory:", engine=mock_engine)

        assert conn.engine.paramstyle == "named"

    # Test create_query method
    def test_create_query_success(self, connection, mock_connect):
        """Test successful query creation"""
        mock_cursor = Mock()
        mock_connect.cursor.return_value = mock_cursor

        # Execute
        query = connection.create_query(sql="SELECT * FROM table", var=['col1'], params={'key': 'value'})

        # Assert
        assert isinstance(query, Query)
        mock_connect.cursor.assert_called_once()

    def test_create_query_closed_connection(self, connection):
        """Test query creation with closed connection"""
        connection._is_closed = True

        with pytest.raises(DBConnectError, match="Connection is closed"):
            connection.create_query()

    def test_create_query_no_connection(self,mock_engine):
        """Test query creation without active connection"""
        conn = Connection(engine=mock_engine)  # No connect set

        with pytest.raises(DBConnectError, match="No active connection"):
            conn.create_query()

    # Test begin_transaction method
    def test_begin_transaction_success(self, connection, mock_connect):
        """Test successful transaction start"""
        # Execute
        result = connection.begin_transaction()

        # Assert
        assert result is True
        assert connection._in_transaction is True
        mock_connect.execute.assert_called_once_with("BEGIN TRANSACTION")

    def test_begin_transaction_already_active(self, connection, mock_connect):
        """Test transaction start when already in transaction"""
        connection._in_transaction = True

        # Execute
        result = connection.begin_transaction()

        # Assert
        assert result is False
        mock_connect.execute.assert_not_called()

    def test_begin_transaction_closed_connection(self, connection):
        """Test transaction start with closed connection"""
        connection._is_closed = True

        with pytest.raises(DBConnectError, match="Connection is closed"):
            connection.begin_transaction()

    def test_begin_transaction_error(self, connection, mock_connect):
        """Test transaction start with error"""
        mock_connect.execute.side_effect = Exception("Transaction error")

        with pytest.raises(DBOperationError, match="Failed to begin transaction"):
            connection.begin_transaction()

    # Test commit method
    def test_commit_success(self, connection, mock_connect):
        """Test successful commit"""
        connection._in_transaction = True

        # Execute
        result = connection.commit()

        # Assert
        assert result is True
        assert connection._in_transaction is False
        mock_connect.commit.assert_called_once()

    def test_commit_no_transaction(self, connection, mock_connect, caplog):
        """Test commit without active transaction"""
        caplog.set_level(logging.WARNING)
        connection._in_transaction = False

        # Execute
        result = connection.commit()

        # Assert
        assert result is False
        mock_connect.commit.assert_not_called()
        assert "No active transaction to commit" in caplog.text

    def test_commit_closed_connection(self, connection):
        """Test commit with closed connection"""
        connection._is_closed = True

        with pytest.raises(DBConnectError, match="Connection is closed"):
            connection.commit()

    def test_commit_error(self, connection, mock_connect):
        """Test commit with error"""
        connection._in_transaction = True
        mock_connect.commit.side_effect = Exception("Commit error")

        with pytest.raises(DBOperationError, match="Failed to commit transaction"):
            connection.commit()

    # Test rollback method
    def test_rollback_success(self, connection, mock_connect):
        """Test successful rollback"""
        connection._in_transaction = True

        # Execute
        result = connection.rollback()

        # Assert
        assert result is True
        assert connection._in_transaction is False
        mock_connect.rollback.assert_called_once()

    def test_rollback_no_transaction(self, connection, mock_connect, caplog):
        """Test rollback without active transaction"""
        caplog.set_level(logging.WARNING)
        connection._in_transaction = False

        # Execute
        result = connection.rollback()

        # Assert
        assert result is False
        mock_connect.rollback.assert_not_called()
        assert "No active transaction to rollback" in caplog.text

    def test_rollback_closed_connection(self, connection):
        """Test rollback with closed connection"""
        connection._is_closed = True

        with pytest.raises(DBConnectError, match="Connection is closed"):
            connection.rollback()

    def test_rollback_error(self, connection, mock_connect):
        """Test rollback with error"""
        connection._in_transaction = True
        mock_connect.rollback.side_effect = Exception("Rollback error")

        with pytest.raises(DBOperationError, match="Failed to rollback transaction"):
            connection.rollback()

    # Test close method
    def test_close_success(self, connection, mock_connect):
        """Test successful connection close"""
        # Execute
        result = connection.close()

        # Assert
        assert result is True
        assert connection._is_closed is True
        mock_connect.close.assert_called_once()

    def test_close_with_active_transaction(self, connection, mock_connect):
        """Test close with active transaction (should rollback)"""
        connection._in_transaction = True

        # Execute
        result = connection.close()

        # Assert
        assert result is True
        mock_connect.rollback.assert_called_once()
        mock_connect.close.assert_called_once()

    def test_close_already_closed(self, connection):
        """Test close when already closed"""
        connection._is_closed = True

        # Execute
        result = connection.close()

        # Assert
        assert result is False

    def test_close_no_connection(self,mock_engine):
        """Test close without active connection"""
        conn = Connection(engine=mock_engine)  # No connect set

        # Execute
        result = conn.close()

        # Assert
        assert result is False

    def test_close_error(self, connection, mock_connect):
        """Test close with error"""
        mock_connect.close.side_effect = Exception("Close error")

        with pytest.raises(DBConnectError, match="Failed to close connection"):
            connection.close()

    # Test status methods
    def test_is_connected_true(self, connection):
        """Test is_connected returns True for active connection"""
        assert connection.is_connected() is True

    def test_is_connected_false_when_closed(self, connection):
        """Test is_connected returns False for closed connection"""
        connection._is_closed = True
        assert connection.is_connected() is False

    def test_is_connected_false_no_connection(self,mock_engine):
        """Test is_connected returns False when no connection"""
        conn = Connection(engine=mock_engine)  # No connect set
        assert conn.is_connected() is False

    def test_in_transaction_true(self, connection):
        """Test in_transaction returns True when in transaction"""
        connection._in_transaction = True
        assert connection.in_transaction() is True

    def test_in_transaction_false(self, connection):
        """Test in_transaction returns False when not in transaction"""
        assert connection.in_transaction() is False

    # Test context manager
    def test_context_manager_success(self, connection, mock_connect):
        """Test context manager with successful execution"""
        # Start a transaction first
        connection.begin_transaction()

        with connection as conn:
            assert conn is connection

        # Now commit should be called
        mock_connect.commit.assert_called_once()
        mock_connect.close.assert_called_once()

    def test_context_manager_with_exception(self, connection, mock_connect):
        """Test context manager with exception"""
        # Start a transaction first
        connection.begin_transaction()
        with pytest.raises(ValueError):
            with connection:
                raise ValueError("Test error")

        # Should rollback and close
        mock_connect.rollback.assert_called_once()
        mock_connect.close.assert_called_once()

    # Integration tests with real SQLite
    def test_integration_create_connection(self):
        """Integration test with real SQLite connection"""
        conn = Connection.create_connection(url=":memory:", engine=sqlite3)

        assert conn.is_connected() is True
        assert conn.in_transaction() is False

        # Test query creation
        query = conn.create_query("SELECT 1")
        assert isinstance(query, Query)

        conn.close()
        assert conn.is_connected() is False

    def test_integration_transaction_cycle(self):
        """Integration test for full transaction cycle"""
        conn = Connection.create_connection(url=":memory:", engine=sqlite3)

        # Start transaction
        assert conn.begin_transaction() is True
        assert conn.in_transaction() is True

        # Commit
        assert conn.commit() is True
        assert conn.in_transaction() is False

        conn.close()

    def test_integration_rollback_cycle(self):
        """Integration test for rollback scenario"""
        conn = Connection.create_connection(url=":memory:", engine=sqlite3)

        # Start transaction
        assert conn.begin_transaction() is True

        # Rollback
        assert conn.rollback() is True
        assert conn.in_transaction() is False

        conn.close()


class TestConnectionEdgeCases:
    """Test edge cases and error scenarios"""

    def test_multiple_operations_after_close(self, connection, mock_connect):
        """Test operations after connection is closed"""
        connection.close()

        # All operations should fail after close
        with pytest.raises(DBConnectError):
            connection.create_query()

        with pytest.raises(DBConnectError):
            connection.begin_transaction()

        with pytest.raises(DBConnectError):
            connection.commit()

        with pytest.raises(DBConnectError):
            connection.rollback()

    def test_transaction_flow_consistency(self, connection, mock_connect):
        """Test transaction state consistency"""
        # Begin transaction
        assert connection.begin_transaction() is True
        assert connection.in_transaction() is True

        # Try to begin again (should return False)
        assert connection.begin_transaction() is False
        assert connection.in_transaction() is True

        # Commit
        assert connection.commit() is True
        assert connection.in_transaction() is False

        # Try to commit again (should return False)
        assert connection.commit() is False
        assert connection.in_transaction() is False

    def test_rollback_after_commit(self, connection, mock_connect):
        """Test rollback after commit"""
        connection._in_transaction = True
        connection.commit()

        # Rollback should return False after commit
        assert connection.rollback() is False

    def test_close_during_transaction(self, connection, mock_connect):
        """Test close during active transaction"""
        connection._in_transaction = True

        connection.close()

        # Should have rolled back and closed
        mock_connect.rollback.assert_called_once()
        mock_connect.close.assert_called_once()
        assert connection._is_closed is True
        assert connection._in_transaction is False


# Test logging behavior
class TestConnectionLogging:
    """Test logging behavior"""

    def test_transaction_logging(self, connection, mock_connect, caplog):
        """Test transaction-related logging"""
        caplog.set_level(logging.DEBUG)

        # Test begin transaction logging
        connection.begin_transaction()
        assert "Transaction started" in caplog.text

        # Test commit logging
        connection.commit()
        assert "Transaction committed" in caplog.text

        # Test rollback logging
        connection.begin_transaction()
        connection.rollback()
        assert "Transaction rolled back" in caplog.text

        # Test close logging
        connection.close()
        assert "Connection closed" in caplog.text

    def test_warning_logging(self, connection, caplog):
        """Test warning messages"""
        caplog.set_level(logging.WARNING)

        # Commit without transaction
        connection.commit()
        assert "No active transaction to commit" in caplog.text

        # Rollback without transaction
        connection.rollback()
        assert "No active transaction to rollback" in caplog.text


# Test paramstyle behavior
class TestConnectionParamstyle:
    """Test parameter style handling"""

    def test_paramstyle_set_on_creation(self, mock_engine, mock_connect):
        """Test that paramstyle is set to named on connection creation"""
        mock_engine.connect.return_value = mock_connect

        conn = Connection.create_connection(url=":memory:", engine=mock_engine)

        assert conn.engine.paramstyle == "named"
        assert mock_engine.paramstyle == "named"

    def test_paramstyle_preserved_if_already_set(self, mock_engine, mock_connect):
        """Test that existing paramstyle is preserved"""
        mock_engine.paramstyle = "qmark"
        mock_engine.connect.return_value = mock_connect

        conn = Connection.create_connection(url=":memory:", engine=mock_engine)

        # Should be changed to "named"
        assert conn.engine.paramstyle == "named"