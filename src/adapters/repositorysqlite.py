# connection_manager.py
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Callable, Any

from src.adapters.repository import AdminRepositoryAbstract
from src.domain.model import AdminEmpty, AdminsAggregate, AdminAbstract, Admin

# connection_manager.py


class SQLiteConnectionManager:
    """Manages SQLite database connections"""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path

    @contextmanager
    def get_connection(self,*args, **kwargs) -> Generator[sqlite3.Connection, None, None]:
        """Get a managed database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute_in_transaction(self, operation: Callable[[sqlite3.Connection], Any]) -> Any:
        """Execute operation in a transaction with automatic commit/rollback"""
        with self.get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION")
                result = operation(conn)
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise


# transaction_manager.py
# transaction_manager.py


class TransactionManager:
    """Manages database transactions"""

    def __init__(self, connection_manager: SQLiteConnectionManager):
        self.connection_manager = connection_manager

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database transactions"""
        with self.connection_manager.get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION")
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def execute_in_transaction(self, func: Callable[[sqlite3.Connection], Any]) -> Any:
        """Execute a function within a transaction"""
        with self.transaction() as conn:
            return func(conn)

# sqlite_admin_repository.py


class SQLiteAdminRepository(AdminRepositoryAbstract):
    """SQLite implementation using separate connection and transaction managers"""

    def __init__(self, connection_manager: SQLiteConnectionManager,
                 transaction_manager: TransactionManager = None):
        self.connection_manager = connection_manager
        self.transaction_manager = transaction_manager or TransactionManager(connection_manager)
        self._empty_admin = AdminEmpty()
        self._ensure_tables_exist()
        self._ensure_aggregate_exists()

    def _ensure_tables_exist(self) -> None:
        """Create tables if they don't exist"""

        def create_tables(conn):
            # Create aggregate table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admins_aggregate (
                    version INTEGER DEFAULT 0
                )
            """)

            # Create admins table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    admin_id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    date_created TEXT NOT NULL
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_admins_name ON admins(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email)")

        self.connection_manager.execute_in_transaction(create_tables)

    def _ensure_aggregate_exists(self) -> None:
        """Ensure the aggregate row exists"""

        def ensure_aggregate(conn):
            result = conn.execute("SELECT COUNT(*) FROM admins_aggregate").fetchone()[0]
            if result == 0:
                conn.execute("INSERT INTO admins_aggregate (version) VALUES (0)")

        self.connection_manager.execute_in_transaction(ensure_aggregate)

    def _get_list_of_admins(self) -> AdminsAggregate:
        """Load all admins from database and create aggregate"""

        def load_aggregate(conn):
            # Get current version
            version_result = conn.execute("SELECT version FROM admins_aggregate").fetchone()
            version = version_result["version"] if version_result else 0

            # Get all admins
            cursor = conn.execute("SELECT * FROM admins")
            admins = []

            for row in cursor:
                admin = self._row_to_admin(row)
                admins.append(admin)

            return AdminsAggregate(admins, version)

        return self.connection_manager.execute_in_transaction(load_aggregate)

    def _save_admins(self, aggregate: AdminsAggregate) -> None:
        """Save all admins to database and update aggregate version"""

        def save_aggregate(conn):
            # Update aggregate version
            conn.execute("UPDATE admins_aggregate SET version = ?", (aggregate.version,))

            # Clear existing admins
            conn.execute("DELETE FROM admins")

            # Insert all admins from aggregate
            for admin in aggregate.get_all_admins():
                self._insert_admin(conn, admin)

        self.connection_manager.execute_in_transaction(save_aggregate)

    def _get_admin_by_id(self, admin_id: int) -> AdminAbstract:
        """Get individual admin by ID"""

        def get_admin(conn):
            row = conn.execute(
                "SELECT * FROM admins WHERE admin_id = ?", (admin_id,)
            ).fetchone()
            return self._row_to_admin(row) if row else self._empty_admin

        return self.connection_manager.execute_in_transaction(get_admin)

    def _get_admin_by_name(self, name: str) -> AdminAbstract:
        """Get individual admin by name"""

        def get_admin(conn):
            row = conn.execute(
                "SELECT * FROM admins WHERE name = ?", (name,)
            ).fetchone()
            return self._row_to_admin(row) if row else self._empty_admin

        return self.connection_manager.execute_in_transaction(get_admin)

    def _add_admin(self, admin: Admin) -> None:
        """Add a new admin to the database"""

        def add_admin(conn):
            self._insert_admin(conn, admin)
            self._increment_version(conn)

        self.transaction_manager.execute_in_transaction(add_admin)

    def _update_admin(self, admin: Admin) -> None:
        """Update an existing admin in the database"""

        def update_admin(conn):
            result = conn.execute(
                """UPDATE admins 
                   SET email = ?, password_hash = ?, enabled = ?
                   WHERE admin_id = ?""",
                (admin.email, admin._password_hash, 1 if admin.enabled else 0, admin.admin_id)
            )

            if result.rowcount == 0:
                raise ValueError(f"Admin with ID {admin.admin_id} not found")

            self._increment_version(conn)

        self.transaction_manager.execute_in_transaction(update_admin)

    def _remove_admin(self, name: str) -> None:
        """Remove admin by name from the database"""

        def remove_admin(conn):
            result = conn.execute("DELETE FROM admins WHERE name = ?", (name,))

            if result.rowcount == 0:
                raise ValueError(f"Admin '{name}' not found")

            self._increment_version(conn)

        self.transaction_manager.execute_in_transaction(remove_admin)

    # Helper methods
    def _insert_admin(self, conn, admin: Admin) -> None:
        """Insert a single admin into the database"""
        try:
            conn.execute(
                """INSERT INTO admins 
                   (admin_id, name, email, password_hash, enabled, date_created)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    admin.admin_id,
                    admin.name,
                    admin.email,
                    admin._password_hash,
                    1 if admin.enabled else 0,
                    admin.date_created.isoformat()
                )
            )
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                if "admin_id" in str(e):
                    raise ValueError(f"Admin with ID {admin.admin_id} already exists")
                elif "name" in str(e):
                    raise ValueError(f"Admin with name '{admin.name}' already exists")
            raise e

    def _increment_version(self, conn) -> None:
        """Increment the aggregate version"""
        conn.execute("UPDATE admins_aggregate SET version = version + 1")

    def _row_to_admin(self, row) -> Admin:
        """Convert database row to Admin object"""
        admin = Admin(
            admin_id=row["admin_id"],
            name=row["name"],
            password=row["password_hash"],  # Already hashed
            email=row["email"],
            enabled=bool(row["enabled"])
        )
        admin.date_created = datetime.fromisoformat(row["date_created"])
        return admin

    # Additional utility methods
    def get_current_version(self) -> int:
        """Get current version from database"""

        def get_version(conn):
            result = conn.execute("SELECT version FROM admins_aggregate").fetchone()
            return result["version"] if result else 0

        return self.connection_manager.execute_in_transaction(get_version)
