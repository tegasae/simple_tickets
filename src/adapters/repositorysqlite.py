# connection_manager.py
import sqlite3

from datetime import datetime

from src.adapters.repository import AdminRepositoryAbstract, ClientRepositoryAbstract
from src.domain.clients import Client
from src.domain.model import AdminsAggregate, Admin
from src.domain.value_objects import Emails, Address, Phones, ClientName
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
                    date_created TEXT NOT NULL,
                    roles text default ""
                )
            """)
            query.set_result()

            # Create admins table
            query = self.conn.create_query("""
                            CREATE TABLE IF NOT EXISTS admins_roles (
                                admin_id INTEGER,
                                role_id INTEGER
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

        self.saved_version = 0

    def get_list_of_admins(self) -> AdminsAggregate:

        try:

            # Get current version
            query = self.conn.create_query("SELECT version FROM admins_aggregate", var=['version'])
            version_result = query.get_one_result()
            self.saved_version = version_result.get('version', 0) if version_result else 0

            # Get all admins
            query = self.conn.create_query("SELECT admin_id,name,password_hash,email,enabled,date_created,roles FROM admins",
                                           var=['admin_id', 'name', 'password_hash', 'email', 'enabled',
                                                'date_created','roles'])

            admins_data = query.get_result()

            admins = []

            for row in admins_data:
                #todo переделать это. Дата может быть не в формате, тогда выаодить значение по умолчанию
                try:
                    roles=set(map(int,row['roles'].split(',')))
                except (ValueError,AttributeError):
                    roles=set()

                try:
                    date_created=datetime.fromisoformat(row['date_created'])
                except ValueError:
                    date_created=datetime.now()
                admin = Admin(
                    admin_id=row['admin_id'],
                    name=row['name'],
                    password=row['password_hash'],  # Already hashed
                    email=row['email'],
                    enabled=bool(row['enabled']),
                    date_created=date_created,
                    roles_ids=roles
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
            if not query.count:
                raise DBOperationError(f"The version is wrong")
            # Clear existing admins
            query = self.conn.create_query("DELETE FROM admins")
            query.set_result()
            query_new_admin = self.conn.create_query(
                "INSERT INTO admins  (name, email, password_hash, enabled, "
                "date_created,roles) VALUES (:name, :email, :password_hash, "
                ":enabled, :date_created,roles)")
            query_exists_admin = self.conn.create_query(
                "INSERT INTO admins  (admin_id, name, email, password_hash, enabled, "
                "date_created,roles) VALUES (:admin_id, :name, :email, :password_hash, "
                ":enabled, :date_created,:roles)")
            # Insert all admins from aggregate
            for admin in aggregate.get_all_admins():

                roles=",".join(map(str,admin.get_roles()))
                if admin.admin_id == 0:
                    query_new_admin.set_result(params={
                        'name': admin.name,
                        'email': admin.email,
                        'password_hash': admin.password,
                        'enabled': 1 if admin.enabled else 0,
                        'date_created': admin.date_created.isoformat(),
                        'roles': roles
                    })

                else:

                    query_exists_admin.set_result(params={
                        'admin_id': admin.admin_id,
                        'name': admin.name,
                        'email': admin.email,
                        'password_hash': admin.password,
                        'enabled': 1 if admin.enabled else 0,
                        'date_created': admin.date_created.isoformat(),
                        'roles': roles
                    })
        except Exception as e:
            raise DBOperationError(f"Failed to save admins: {str(e)}")


class SQLiteClientRepository(ClientRepositoryAbstract):

    def __init__(self, conn: Connection):
        self.conn = conn


    def get_all_clients(self) -> list[Client]:
        try:
            query = self.conn.create_query(
                "SELECT client_id,admin_id, client_name,emails,phones,address, enabled,date_created,version FROM clients",
                var=['client_id','admin_id', 'name', 'emails', 'phones', 'address', 'enabled','date_created','version'])

            clients_data = query.get_result()

            clients = []

            for row in clients_data:
                try:
                    date_created = datetime.fromisoformat(row['date_created'])
                except ValueError:
                    date_created = datetime.now()
                client = Client(
                    client_id=row['client_id'],
                    admin_id=row['admin_id'],
                    name=ClientName(row['name']),
                    emails=Emails(row['emails']),
                    phones=Phones(row['phones']),
                    address=Address(row['address']),
                    enabled=bool(row['enabled']),
                    date_created=date_created,
                    version=row['version']
                )

                clients.append(client)


        except Exception as e:
            raise DBOperationError(f"Failed to get admin list: {str(e)}")

        return clients

    def save_client(self, client: Client) -> None:
        """Save the entire aggregate to persistence"""
        try:
            query_new_client = self.conn.create_query(
                "INSERT INTO clients (admin_id,client_name, emails, address,phones, enabled, date_created,version) VALUES (:admin_id,:name, :emails, :address, :phones, :enabled, :date_created,0)")
            query_exists_client = self.conn.create_query(
                "UPDATE clients  "
                "SET client_name=:name,emails=:emails,address=:address,phones=:phones,enabled=:enabled,version=:version+1 "
                "WHERE client_id=:client_id AND version=:version")
            # Insert all admins from aggregate

            if client.client_id == 0:
                client.client_id=query_new_client.set_result(params={
                        'admin_id': client.admin_id,
                        'name': client.name.value,
                        'emails': client.emails.value,
                        'address': client.address.value,
                        'phones': client.phones.value,
                        'enabled': 1 if client.enabled else 0,
                        'date_created': client.date_created.isoformat()
                    })
            else:
                query_exists_client.set_result(params={
                        'name': client.name.value,
                        'emails': client.emails.value,
                        'address': client.address.value,
                        'phones': client.phones.value,
                        'enabled': 1 if client.enabled else 0,
                        'client_id': client.admin_id,
                        'version': client.version
                })
                if not query_exists_client.count:
                    raise DBOperationError(f"The version is wrong")
        except Exception as e:
            raise DBOperationError(f"Failed to save client: {str(e)}")

    def delete_client(self, client_id:int) -> None:
        try:
            query_delete_client = self.conn.create_query("DELETE FROM clients WHERE client_id=:client_id")
            query_delete_client.set_result(params={'client_id': client_id})
        except Exception as e:
            raise DBOperationError(f"Failed to delete client: {str(e)}")


if __name__ == "__main__":
    # conn1 = Connection.create_connection(url=":memory:", engine=sqlite3)

    conn1 = Connection.create_connection(
        url='../../db/admins.db',  # or "admins.db" for file-based
        engine=sqlite3
    )
    #db_creator = CreateDB(conn1)
   # db_creator.init_data()
   # db_creator.create_indexes()
    conn1.begin_transaction()
    admin1=Admin(name='admin', email='<EMAIL>', password='<PASSWORD>',admin_id=1,enabled=True)
    repository=SQLiteClientRepository(conn1)
    client1=Client.create(name="test",emails="<EMAIL>",phones="0123456789",address="test",enabled=True,admin_id=admin1.admin_id)
    repository.save_client(client=client1)
    print(client1)
    #clients1=repository.get_all_clients()
    #print(clients1)
    #clients1[0].phones=Phones("111111111122")
    #repository.save_client(clients1[0])
    #repository.delete_client(client_id=3)

    conn1.commit()
    conn1.close()

