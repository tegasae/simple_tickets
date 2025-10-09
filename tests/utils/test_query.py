# tests/unit/db/test_query.py
import pytest
from unittest.mock import Mock
from utils.db.query import Query
from utils.db.exceptions import DBOperationError


@pytest.fixture
def mock_cursor():
    """Mock database cursor"""
    cursor = Mock()
    cursor.execute = Mock()
    cursor.fetchall = Mock()
    cursor.fetchone = Mock()
    cursor.rowcount = 0
    cursor.lastrowid = None
    cursor.close = Mock()
    return cursor


class TestQuery:
    """Test suite for Query class"""


    @pytest.fixture
    def query(self, mock_cursor):
        """Query instance with mocked cursor"""
        return Query(
            sql="SELECT * FROM table",
            var=['id', 'name'],
            params={'limit': 10},
            cursor=mock_cursor
        )

    @pytest.fixture
    def query_no_params(self, mock_cursor):
        """Query instance without parameters"""
        return Query(
            sql="SELECT 1",
            cursor=mock_cursor
        )

    # Test Initialization
    def test_init_with_all_parameters(self, mock_cursor):
        """Test Query initialization with all parameters"""
        query = Query(
            sql="SELECT * FROM users",
            var=['id', 'name'],
            params={'active': True},
            cursor=mock_cursor
        )

        assert query.sql == "SELECT * FROM users"
        assert query.var == ['id', 'name']
        assert query.params == {'active': True}
        assert query.cur == mock_cursor
        assert query.last_row_id == 0
        assert query.result is None
        assert query.count == 0

    def test_init_with_minimal_parameters(self, mock_cursor):
        """Test Query initialization with minimal parameters"""
        query = Query(cursor=mock_cursor)

        assert query.sql == ""
        assert query.var is None
        assert query.params is None
        assert query.cur == mock_cursor
        assert query.last_row_id == 0
        assert query.result is None
        assert query.count == 0

    # Test _execute method
    def test_execute_with_params(self, query, mock_cursor):
        """Test _execute with parameters"""
        # Execute
        query._execute()

        # Assert
        mock_cursor.execute.assert_called_once_with("SELECT * FROM table", {'limit': 10})

    def test_execute_with_new_params(self, query, mock_cursor):
        """Test _execute with new parameters"""
        new_params = {'limit': 20, 'offset': 5}

        # Execute
        query._execute(params=new_params)

        # Assert
        assert query.params == new_params
        mock_cursor.execute.assert_called_once_with("SELECT * FROM table", new_params)

    def test_execute_without_params(self, query_no_params, mock_cursor):
        """Test _execute without parameters"""
        # Execute
        query_no_params._execute()

        # Assert
        mock_cursor.execute.assert_called_once_with("SELECT 1")

    def test_execute_database_error(self, query, mock_cursor):
        """Test _execute with database error"""
        mock_cursor.execute.side_effect = Exception("Database error")

        # Execute & Assert
        with pytest.raises(DBOperationError, match="Database error"):
            query._execute()

    # Test set_result method
    def test_set_result_success(self, query, mock_cursor):
        """Test successful set_result"""
        # Setup
        mock_cursor.rowcount = 5
        mock_cursor.lastrowid = 42

        # Execute
        result = query.set_result()

        # Assert
        assert result == 42
        assert query.last_row_id == 42
        assert query.count == 5
        mock_cursor.execute.assert_called_once()

    def test_set_result_with_new_params(self, query, mock_cursor):
        """Test set_result with new parameters"""
        new_params = {'limit': 15}
        mock_cursor.rowcount = 3
        mock_cursor.lastrowid = 100

        # Execute
        result = query.set_result(params=new_params)

        # Assert
        assert result == 100
        assert query.params == new_params
        assert query.count == 3

    def test_set_result_no_lastrowid(self, query, mock_cursor):
        """Test set_result when no lastrowid is available"""
        mock_cursor.rowcount = 2
        mock_cursor.lastrowid = None

        # Execute
        result = query.set_result()

        # Assert
        assert result == 0  # Should remain 0 when no lastrowid
        assert query.last_row_id == 0
        assert query.count == 2

    def test_set_result_zero_rowcount(self, query, mock_cursor):
        """Test set_result with zero rowcount"""
        mock_cursor.rowcount = 0
        mock_cursor.lastrowid = None

        # Execute
        result = query.set_result()

        # Assert
        assert result == 0
        assert query.count == 0

    def test_set_result_database_error(self, query, mock_cursor):
        """Test set_result with database error"""
        mock_cursor.execute.side_effect = Exception("Insert failed")

        # Execute & Assert
        with pytest.raises(DBOperationError, match="Insert failed"):
            query.set_result()

    def test_set_result_resets_state(self, query, mock_cursor):
        """Test that set_result resets state variables"""
        # Set some initial state
        query.last_row_id = 999
        query.count = 999
        query.result = ["some result"]

        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 50

        # Execute
        query.set_result()

        # Assert state was reset
        assert query.last_row_id == 50  # Updated from cursor
        assert query.count == 1  # Updated from cursor
        assert query.result == ["some result"]  # Result should NOT be reset

    # Test get_result method
    def test_get_result_with_vars(self, query, mock_cursor):
        """Test get_result with column variables"""
        # Setup
        mock_data = [(1, 'John'), (2, 'Jane')]
        mock_cursor.fetchall.return_value = mock_data

        # Execute
        result = query.get_result()

        # Assert
        expected = [
            {'id': 1, 'name': 'John'},
            {'id': 2, 'name': 'Jane'}
        ]
        assert result == expected
        assert query.result == mock_data
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()

    def test_get_result_without_vars(self, query_no_params, mock_cursor):
        """Test get_result without column variables"""
        # Setup
        mock_data = [('value1',), ('value2',)]
        mock_cursor.fetchall.return_value = mock_data

        # Execute
        result = query_no_params.get_result()

        # Assert
        assert result == mock_data
        mock_cursor.fetchall.assert_called_once()

    def test_get_result_empty(self, query, mock_cursor):
        """Test get_result with empty result"""
        mock_cursor.fetchall.return_value = []

        # Execute
        result = query.get_result()

        # Assert
        assert result == []
        assert query.result == []

    def test_get_result_with_new_params(self, query, mock_cursor):
        """Test get_result with new parameters"""
        new_params = {'active': True}
        mock_cursor.fetchall.return_value = [(1, 'Active User')]

        # Execute
        result = query.get_result(params=new_params)

        # Assert
        assert query.params == new_params
        mock_cursor.execute.assert_called_once_with("SELECT * FROM table", new_params)

    def test_get_result_database_error(self, query, mock_cursor):
        """Test get_result with database error"""
        mock_cursor.execute.side_effect = Exception("Query failed")

        # Execute & Assert
        with pytest.raises(DBOperationError, match="Query failed"):
            query.get_result()

    # Test get_one_result method
    def test_get_one_result_with_vars(self, query, mock_cursor):
        """Test get_one_result with column variables"""
        # Setup
        mock_data = (1, 'John Doe')
        mock_cursor.fetchone.return_value = mock_data

        # Execute
        result = query.get_one_result()

        # Assert
        expected = {'id': 1, 'name': 'John Doe'}
        assert result == expected
        assert query.result == mock_data
        mock_cursor.fetchone.assert_called_once()

    def test_get_one_result_without_vars(self, query_no_params, mock_cursor):
        """Test get_one_result without column variables"""
        # Setup
        mock_data = ('value1', 'value2')
        mock_cursor.fetchone.return_value = mock_data

        # Execute
        result = query_no_params.get_one_result()

        # Assert
        expected = {0: 'value1', 1: 'value2'}
        assert result == expected

    def test_get_one_result_empty(self, query, mock_cursor):
        """Test get_one_result with no results"""
        mock_cursor.fetchone.return_value = None

        # Execute
        result = query.get_one_result()

        # Assert
        assert result == {}

    def test_get_one_result_single_column(self, query_no_params, mock_cursor):
        """Test get_one_result with single column result"""
        mock_cursor.fetchone.return_value = ('single_value',)

        # Execute
        result = query_no_params.get_one_result()

        # Assert
        assert result == {0: 'single_value'}

    def test_get_one_result_with_new_params(self, query, mock_cursor):
        """Test get_one_result with new parameters"""
        new_params = {'id': 5}
        mock_cursor.fetchone.return_value = (5, 'Specific User')

        # Execute
        result = query.get_one_result(params=new_params)

        # Assert
        assert query.params == new_params

    # Test get_one_result_tuple method
    def test_get_one_result_tuple_success(self, query, mock_cursor):
        """Test get_one_result_tuple with data"""
        # Setup
        mock_data = (1, 'John', 'john@example.com')
        mock_cursor.fetchone.return_value = mock_data

        # Execute
        result = query.get_one_result_tuple()

        # Assert
        assert result == mock_data
        assert query.result == mock_data

    def test_get_one_result_tuple_empty(self, query, mock_cursor):
        """Test get_one_result_tuple with no results"""
        mock_cursor.fetchone.return_value = None

        # Execute
        result = query.get_one_result_tuple()

        # Assert
        assert result == ()

    def test_get_one_result_tuple_preserves_structure(self, query, mock_cursor):
        """Test get_one_result_tuple preserves tuple structure"""
        mock_data = (42,)  # Single value tuple
        mock_cursor.fetchone.return_value = mock_data

        # Execute
        result = query.get_one_result_tuple()

        # Assert
        assert result == (42,)
        assert isinstance(result, tuple)

    # Test close method
    def test_close_success(self, query, mock_cursor):
        """Test successful close"""
        # Execute
        query.close()

        # Assert
        mock_cursor.close.assert_called_once()

    def test_close_no_cursor(self):
        """Test close when no cursor exists"""
        query = Query()  # No cursor

        # Execute (should not raise)
        query.close()

    # Test context manager
    def test_context_manager_success(self, query, mock_cursor):
        """Test context manager functionality"""
        with query as q:
            assert q is query

        # Should close cursor on exit
        mock_cursor.close.assert_called_once()

    def test_context_manager_with_exception(self, query, mock_cursor):
        """Test context manager with exception"""
        with pytest.raises(ValueError):
            with query:
                raise ValueError("Test error")

        # Should still close cursor on exit
        mock_cursor.close.assert_called_once()

    # Test edge cases
    def test_multiple_operations_preserve_state(self, query, mock_cursor):
        """Test that multiple operations preserve appropriate state"""
        # First operation: set_result
        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 10
        query.set_result()

        assert query.last_row_id == 10
        assert query.count == 1

        # Second operation: get_result
        mock_cursor.fetchall.return_value = [(10, 'Test')]
        result = query.get_result()

        # set_result values should persist
        assert query.last_row_id == 10
        assert query.count == 1
        assert query.result == [(10, 'Test')]

    def test_empty_sql_query(self, mock_cursor):
        """Test query with empty SQL"""
        query = Query(sql="", cursor=mock_cursor)

        # Execute & Assert
        query._execute()
        mock_cursor.execute.assert_called_once_with("")

    def test_none_parameters(self, mock_cursor):
        """Test query with None parameters"""
        query = Query(sql="SELECT 1", params=None, cursor=mock_cursor)

        # Execute
        query._execute()

        # Assert - should call execute without parameters
        mock_cursor.execute.assert_called_once_with("SELECT 1")


class TestQueryErrorScenarios:
    """Test error scenarios and edge cases"""

    @pytest.fixture
    def mock_cursor(self):
        cursor = Mock()
        cursor.execute = Mock()
        cursor.fetchall = Mock()
        cursor.fetchone = Mock()
        cursor.rowcount = 0
        cursor.lastrowid = None
        return cursor

    def test_execute_with_cursor_error(self, mock_cursor):
        """Test _execute when cursor has issues"""
        query = Query(sql="SELECT 1", cursor=mock_cursor)
        mock_cursor.execute.side_effect = MemoryError("Out of memory")

        with pytest.raises(DBOperationError, match="Out of memory"):
            query._execute()

    def test_get_result_fetch_error(self, mock_cursor):
        """Test get_result when fetch fails"""
        query = Query(sql="SELECT 1", cursor=mock_cursor)
        mock_cursor.fetchall.side_effect = Exception("Fetch failed")

        with pytest.raises(DBOperationError, match="Fetch failed"):
            query.get_result()

    def test_get_one_result_fetch_error(self, mock_cursor):
        """Test get_one_result when fetch fails"""
        query = Query(sql="SELECT 1", cursor=mock_cursor)
        mock_cursor.fetchone.side_effect = Exception("Fetch one failed")

        with pytest.raises(DBOperationError, match="Fetch one failed"):
            query.get_one_result()

    def test_mixed_none_and_empty_results(self, mock_cursor):
        """Test behavior with mixed None and empty results"""
        query = Query(sql="SELECT 1", cursor=mock_cursor)

        # Test get_result with None
        mock_cursor.fetchall.return_value = None
        result = query.get_result()
        assert result == []

        # Test get_one_result with empty tuple (shouldn't happen but test anyway)
        mock_cursor.fetchone.return_value = ()
        result = query.get_one_result()
        assert result == {}  # Empty dict

    def test_vars_length_mismatch(self, mock_cursor):
        """Test when vars length doesn't match result columns"""
        query = Query(
            sql="SELECT id, name, email FROM users",
            var=['id', 'name'],  # Missing email var
            cursor=mock_cursor
        )

        mock_cursor.fetchone.return_value = (1, 'John', 'john@example.com')

        # Should still work, extra columns will be ignored in dict creation
        result = query.get_one_result()
        assert result == {'id': 1, 'name': 'John'}  # email is dropped


class TestQueryIntegration:
    """Integration tests with real database (if applicable)"""

    def test_query_lifecycle(self, mock_cursor):
        """Test complete query lifecycle"""
        query = Query(
            sql="INSERT INTO users (name) VALUES (?) RETURNING id",
            var=['id'],
            params={'name': 'Test User'},
            cursor=mock_cursor
        )

        # Mock the cursor responses
        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 100
        mock_cursor.fetchone.return_value = (100,)

        # Test set_result (for INSERT)
        row_id = query.set_result()
        assert row_id == 100
        assert query.count == 1

        # Test get_one_result (for SELECT)
        result = query.get_one_result()
        assert result == {'id': 100}

        # Test close
        query.close()
        mock_cursor.close.assert_called_once()