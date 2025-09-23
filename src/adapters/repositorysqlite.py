# connection_manager.py
import sqlite3
from datetime import datetime

from src.adapters.repository import AdminRepositoryAbstract
from src.domain.model import AdminEmpty, AdminsAggregate, Admin, AdminAbstract
from utils.db.connect import Connection



from utils.db.exceptions import DBOperationError


class CreateDB:
    def __init__(self, conn: Connection):
        self.conn = conn

    def init_data(self):
        try:
            self.conn.begin_transaction()

            # Create admins_aggregate table
            query = self.conn.create_query("""
                CREATE TABLE IF NOT EXISTS admins_aggregate (
                    version INTEGER DEFAULT 0
                )
            """)
            query.set_result()

            # Create admins table
            query = self.conn.create_query("""
                CREATE TABLE IF NOT EXISTS admins (
                    admin_id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    date_created TEXT NOT NULL
                )
            """)
            query.set_result()

            # Insert initial aggregate row if it doesn't exist
            query = self.conn.create_query("SELECT COUNT(*) FROM admins_aggregate")
            count = query.get_one_result()

            if count and count[0] == 0:  # Check if table is empty
                query = self.conn.create_query("INSERT INTO admins_aggregate (version) VALUES (0)")
                query.set_result()

            self.conn.commit()
            print("Database initialized successfully")

        except Exception as e:
            self.conn.rollback()
            print(f"Failed to initialize database: {e}")
            raise

    def create_indexes(self):
        """Create necessary indexes"""
        try:
            self.conn.begin_transaction()

            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_admins_name ON admins(name)",
                "CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email)",
                "CREATE INDEX IF NOT EXISTS idx_admins_enabled ON admins(enabled)"
            ]

            for sql in indexes:
                query = self.conn.create_query(sql)
                query.set_result()

            self.conn.commit()
            print("Indexes created successfully")

        except Exception as e:
            self.conn.rollback()
            print(f"Failed to create indexes: {e}")
            raise



class SQLiteAdminRepository(AdminRepositoryAbstract):
    def __init__(self, conn: Connection):
        self.conn = conn
        self._empty_admin = AdminEmpty()


    def _get_list_of_admins(self) -> AdminsAggregate:
        """Load the entire aggregate from persistence"""
        try:
            # Get current version
            query = self.conn.create_query("SELECT version FROM admins_aggregate")
            version_result = query.get_one_result()
            version = version_result.get('version', 0) if version_result else 0

            # Get all admins
            query = self.conn.create_query("SELECT * FROM admins")
            admins_data = query.get_result()

            admins = []
            for row in admins_data:
                admin = Admin(
                    admin_id=row['admin_id'],
                    name=row['name'],
                    password=row['password_hash'],  # Already hashed
                    email=row['email'],
                    enabled=bool(row['enabled']),
                    date_created=datetime.fromisoformat(row['date_created'])
                )
                # Set date from database
                admin._password_hash=row['password_hash']
                admins.append(admin)

            return AdminsAggregate(admins, version=version)

        except Exception as e:
            raise DBOperationError(f"Failed to get admin list: {str(e)}")

    def _save_admins(self, aggregate: AdminsAggregate) -> None:
        """Save the entire aggregate to persistence"""
        try:
            # Update aggregate version
            query = self.conn.create_query(
                "UPDATE admins_aggregate SET version = ?",
                params={'version': aggregate.version}
            )
            query.set_result()

            # Clear existing admins
            query = self.conn.create_query("DELETE FROM admins")
            query.set_result()

            # Insert all admins from aggregate
            for admin in aggregate.get_all_admins():
                query = self.conn.create_query(
                    """INSERT INTO admins 
                       (admin_id, name, email, password_hash, enabled, date_created)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    params={
                        'admin_id': admin.admin_id,
                        'name': admin.name,
                        'email': admin.email,
                        'password_hash': admin.password,
                        'enabled': 1 if admin.enabled else 0,
                        'date_created': admin.date_created.isoformat()
                    }
                )
                query.set_result()

        except Exception as e:
            raise DBOperationError(f"Failed to save admins: {str(e)}")

    def _get_admin_by_id(self, admin_id: int) -> AdminAbstract:
        """Get individual admin by ID"""
        try:
            query = self.conn.create_query(
                "SELECT * FROM admins WHERE admin_id = ?",
                params={'admin_id': admin_id},
                var=['admin_id', 'name', 'email', 'password_hash', 'enabled', 'date_created']
            )
            result = query.get_one_result()

            if result:
                admin = Admin(
                    admin_id=result['admin_id'],
                    name=result['name'],
                    password=result['password_hash'],
                    email=result['email'],
                    enabled=bool(result['enabled']),
                    date_created=datetime.fromisoformat(result['date_created'])
                )
                admin._password_hash = result['password_hash']
                return admin
            else:
                return self._empty_admin

        except Exception as e:
            raise DBOperationError(f"Failed to get admin by ID {admin_id}: {str(e)}")

    def _get_admin_by_name(self, name: str) -> AdminAbstract:
        """Get individual admin by name"""
        try:
            query = self.conn.create_query(
                "SELECT * FROM admins WHERE name = ?",
                params={'name': name},
                var=['admin_id', 'name', 'email', 'password_hash', 'enabled', 'date_created']
            )
            result = query.get_one_result()

            if result:
                admin = Admin(
                    admin_id=result['admin_id'],
                    name=result['name'],
                    password=result['password_hash'],
                    email=result['email'],
                    enabled=bool(result['enabled']),
                    date_created=datetime.fromisoformat(result['date_created'])
                )
                admin._password_hash = result['password_hash']
                return admin
            else:
                return self._empty_admin

        except Exception as e:
            raise DBOperationError(f"Failed to get admin by name '{name}': {str(e)}")

    def _add_admin(self, admin: Admin) -> None:
        """Add a new admin"""
        try:
            query = self.conn.create_query(
                """INSERT INTO admins 
                   (admin_id, name, email, password_hash, enabled, date_created)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                params={
                    'admin_id': admin.admin_id,
                    'name': admin.name,
                    'email': admin.email,
                    'password_hash': admin.password,
                    'enabled': 1 if admin.enabled else 0,
                    'date_created': admin.date_created.isoformat()
                }
            )
            query.set_result()

            # Increment version
            query = self.conn.create_query(
                "UPDATE admins_aggregate SET version = version + 1"
            )
            query.set_result()

        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                if "admin_id" in str(e):
                    raise DBOperationError(f"Admin with ID {admin.admin_id} already exists")
                elif "name" in str(e):
                    raise DBOperationError(f"Admin with name '{admin.name}' already exists")
            raise DBOperationError(f"Failed to add admin: {str(e)}")

    def _update_admin(self, admin: Admin) -> None:
        """Update an existing admin"""
        try:
            query = self.conn.create_query(
                """UPDATE admins 
                   SET email = ?, password_hash = ?, enabled = ?
                   WHERE admin_id = ?""",
                params={
                    'email': admin.email,
                    'password_hash': admin.password,
                    'enabled': 1 if admin.enabled else 0,
                    'admin_id': admin.admin_id
                }
            )
            rows_affected = query.set_result()

            if rows_affected == 0:
                raise DBOperationError(f"Admin with ID {admin.admin_id} not found")

            # Increment version
            query = self.conn.create_query(
                "UPDATE admins_aggregate SET version = version + 1"
            )
            query.set_result()

        except Exception as e:
            raise DBOperationError(f"Failed to update admin: {str(e)}")

    def _remove_admin(self, name: str) -> None:
        """Remove admin by name"""
        try:
            query = self.conn.create_query(
                "DELETE FROM admins WHERE name = ?",
                params={'name': name}
            )
            rows_affected = query.set_result()

            if rows_affected == 0:
                raise DBOperationError(f"Admin with name '{name}' not found")

            # Increment version
            query = self.conn.create_query(
                "UPDATE admins_aggregate SET version = version + 1"
            )
            query.set_result()

        except Exception as e:
            raise DBOperationError(f"Failed to remove admin '{name}': {str(e)}")

    # Additional utility methods
    def get_current_version(self) -> int:
        """Get current version from database"""
        try:
            query = self.conn.create_query("SELECT version FROM admins_aggregate")
            result = query.get_one_result()
            return result.get('version', 0) if result else 0
        except Exception as e:
            raise DBOperationError(f"Failed to get current version: {str(e)}")

    def admin_exists_by_id(self, admin_id: int) -> bool:
        """Check if admin with given ID exists"""
        try:
            query = self.conn.create_query(
                "SELECT 1 FROM admins WHERE admin_id = ?",
                params={'admin_id': admin_id}
            )
            result = query.get_one_result_tuple()
            return bool(result)  # Returns True if admin exists
        except Exception as e:
            raise DBOperationError(f"Failed to check admin existence by ID: {str(e)}")

    def admin_exists_by_name(self, name: str) -> bool:
        """Check if admin with given name exists"""
        try:
            query = self.conn.create_query(
                "SELECT 1 FROM admins WHERE name = ?",
                params={'name': name}
            )
            result = query.get_one_result_tuple()
            return bool(result)  # Returns True if admin exists
        except Exception as e:
            raise DBOperationError(f"Failed to check admin existence by name: {str(e)}")

    def get_admin_count(self) -> int:
        """Get total number of admins"""
        try:
            query = self.conn.create_query("SELECT COUNT(*) as count FROM admins")
            result = query.get_one_result()
            return result.get('count', 0) if result else 0
        except Exception as e:
            raise DBOperationError(f"Failed to get admin count: {str(e)}")



if __name__ == "__main__":
    conn1 = Connection.create_connection(
        url=":memory:",  # or "admins.db" for file-based
        engine=sqlite3
    )
    db_creator = CreateDB(conn1)
    db_creator.init_data()
    db_creator.create_indexes()
