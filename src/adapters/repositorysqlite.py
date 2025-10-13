# connection_manager.py
import sqlite3

from datetime import datetime

from src.adapters.repository import AdminRepositoryAbstract
from src.domain.model import AdminEmpty, AdminsAggregate, Admin
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
                    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        self.saved_version = 0

    def get_list_of_admins(self) -> AdminsAggregate:

        try:

            # Get current version
            query = self.conn.create_query("SELECT version FROM admins_aggregate", var=['version'])
            version_result = query.get_one_result()
            self.saved_version = version_result.get('version', 0) if version_result else 0

            # Get all admins
            query = self.conn.create_query("SELECT admin_id,name,password_hash,email,enabled,date_created FROM admins",
                                           var=['admin_id', 'name', 'password_hash', 'email', 'enabled',
                                                'date_created'])

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
                # todo убрать эту порнографию.
                # Связано с тем, что при установке пароля в admin, он автоматически хешируется.
                # убрать надо в src/domain/models/Admin

                admin._password_hash = row['password_hash']

                admins.append(admin)

            return AdminsAggregate(admins, version=self.saved_version)

        except Exception as e:
            raise DBOperationError(f"Failed to get admin list: {str(e)}")

    def save_admins(self, aggregate: AdminsAggregate) -> None:
        """Save the entire aggregate to persistence"""
        try:
            # Update aggregate version
            query = self.conn.create_query(
                "UPDATE admins_aggregate SET version = :new_version WHERE version=:saved_version",
                var=['new_version', 'saved_version'],
                params={'new_version': aggregate.version, 'saved_version': self.saved_version}
            )
            query.set_result()

            # Clear existing admins
            query = self.conn.create_query("DELETE FROM admins")
            query.set_result()
            query_new_admin = self.conn.create_query(
                "INSERT INTO admins  (name, email, password_hash, enabled, "
                "date_created) VALUES (:name, :email, :password_hash, "
                ":enabled, :date_created)")
            query_exists_admin = self.conn.create_query(
                "INSERT INTO admins  (admin_id, name, email, password_hash, enabled, "
                "date_created) VALUES (:admin_id, :name, :email, :password_hash, "
                ":enabled, :date_created)")
            # Insert all admins from aggregate
            for admin in aggregate.get_all_admins():
                if admin.admin_id == 0:
                    query_new_admin.set_result(params={
                        'name': admin.name,
                        'email': admin.email,
                        'password_hash': admin.password,
                        'enabled': 1 if admin.enabled else 0,
                        'date_created': admin.date_created.isoformat()
                    })

                else:

                    query_exists_admin.set_result(params={
                        'admin_id': admin.admin_id,
                        'name': admin.name,
                        'email': admin.email,
                        'password_hash': admin.password,
                        'enabled': 1 if admin.enabled else 0,
                        'date_created': admin.date_created.isoformat()
                    })

        except Exception as e:
            raise DBOperationError(f"Failed to save admins: {str(e)}")


if __name__ == "__main__":
    # conn1 = Connection.create_connection(url=":memory:", engine=sqlite3)

    conn1 = Connection.create_connection(
        url='../../db/admins.db',  # or "admins.db" for file-based
        engine=sqlite3
    )
    db_creator = CreateDB(conn1)
    db_creator.init_data()
    db_creator.create_indexes()
    # admins=AdminsAggregate()
    # admins.add_admin(Admin(admin_id=1,name='name',password='1',email='1',enabled=True))
    conn1.begin_transaction()
    repository = SQLiteAdminRepository(conn=conn1)
    admins1 = repository.get_list_of_admins()
    print(admins1.get_all_admins())

    admins1.change_admin_email(name='name', new_email='123@111.ru')
    admins1.add_admin(Admin(admin_id=0, name='new', email='<EMAIL>', password='1', enabled=True))
    # admin.email='12345'

    # admins1.change_admin(admin)
    repository.save_admins(admins1)
    admins1 = repository.get_list_of_admins()
    print(admins1.get_all_admins())

    conn1.commit()
    conn1.close()
