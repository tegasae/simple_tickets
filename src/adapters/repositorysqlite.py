# connection_manager.py
import sqlite3
from datetime import datetime

from src.adapters.repository import AdminRepositoryAbstract
from src.domain.model import AdminEmpty, AdminsAggregate, AdminAbstract, Admin
from utils.db.connect import Connection

import sqlite3
from datetime import datetime


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
    def __init__(self,conn:Connection):
        self.conn=conn

    def _get_admin_by_id(self, admin_id) -> AdminAbstract:


    def _add_admin(self, admin):


    def _get_admin_by_name(self, name) -> AdminAbstract:


    def _update_admin(self, admin):


    def _remove_admin(self, name):


    def _get_list_of_admins(self) -> AdminsAggregate:


    def _save_admins(self, aggregate):


    # Additional utility methods
    def get_current_version(self) -> int:
        """Get current version from database"""
        result = self.conn.create_query("SELECT version FROM admins_aggregate").get_one_result()[0]
        return result if result else 0






if __name__ == "__main__":
    conn = Connection.create_connection(
        url=":memory:",  # or "admins.db" for file-based
        engine=sqlite3
    )
    db_creator = CreateDB(conn)
    db_creator.init_data()
    db_creator.create_indexes()
