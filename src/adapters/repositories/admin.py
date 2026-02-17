from src.domain.account import NoAccount
from src.domain.employee import Admin
from src.domain.repositories.admin_repository import AdminRepository
from utils.db.connect import Connection


class AdminRepositorySQLite(AdminRepository):

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
            query = self.conn.create_query(
                "SELECT admin_id,name,password_hash,email,enabled,date_created,roles FROM admins",
                var=['admin_id', 'name', 'password_hash', 'email', 'enabled',
                     'date_created', 'roles'])

            admins_data = query.get_result()

            admins = []


            for row in admins_data:
                # todo переделать это. Дата может быть не в формате, тогда выаодить значение по умолчанию



                admin = Admin(
                    admin_id=row['admin_id'],
                    name=row['name'],
                    password=row['password_hash'],  # Already hashed
                    email=row['email'],
                    enabled=bool(row['enabled']),
                    date_created=date_from_sqlite_iso(row['date_created']),
                    roles_ids=self._get_roles(row['roles'])
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

    def get_by_id(self, admin_id: int) -> Admin:


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
                ":enabled, :date_created,:roles)")
            query_exists_admin = self.conn.create_query(
                "INSERT INTO admins  (admin_id, name, email, password_hash, enabled, "
                "date_created,roles) VALUES (:admin_id, :name, :email, :password_hash, "
                ":enabled, :date_created,:roles)")
            # Insert all admins from aggregate
            for admin in aggregate.get_all_admins():
                params = {
                        'name': admin.name,
                        'email': admin.email,
                        'password_hash': admin.password,
                        'enabled': 1 if admin.enabled else 0,
                        'date_created': admin.date_created.isoformat(),
                        'roles': self._set_roles(admin.get_roles())
                    }

                if admin.admin_id == 0:
                    query_new_admin.set_result(params=params)
                else:
                    params['admin_id']= admin.admin_id
                    query_exists_admin.set_result(params=params)
        except Exception as e:
            raise DBOperationError(f"Failed to save admins: {str(e)}")

    def get(self, admin_id: int) -> Admin:
        query = self.conn.create_query("SELECT e.employee_id, e.first_name, e.last_name, e.email, e.phone, e.date_created, e.enabled, e.is_deleted, a.admin_id, a.job_title "
                                       "FROM admins a JOIN employees e  ON e.employee_id = a.employee_id WHERE a.admin_id = :admin_id",
            var=['employee_id', 'first_name', 'last_name', 'email', 'phone', 'enabled', 'is_deleted','admin_id', 'a.job_title'])

        admin_data = query.get_one_result(params={'admin_id': admin_id})
        if not len(admin_data):
            return Admin.create_empty()
        admin = Admin(employee_id=admin_data['employee_id'],first_name=admin_data['first_name'],last_name=admin_data['last_name'],
                      email=admin_data['email'],phone=admin_data['phone'],enabled=bool(admin_data['is_deleted']),
                      date_created=date_from_sqlite_iso(admin_data['date_created']),
                      is_deleted=bool(admin_data['is_deleted']),job_title=admin_data['job_title'],account=NoAccount())
            email=admin_data['email'],
            enabled=bool(admin_data['enabled']),
            date_created=date_from_sqlite_iso(admin_data['date_created']),
            roles_ids=self._get_roles(admin_data['roles'])
        )
        return admin

    def get_all(self) -> list[Admin]:
        pass

    def exists(self, admin_id: int) -> bool:
        pass

    def save(self, admin: Admin) -> Admin:
        pass

    def delete(self, admin_id: int):
        pass

    def find_by_login(self, *, login: str) -> Admin:
        pass

    def exist_login(self, login: str) -> bool:
        pass