from datetime import datetime

from src.domain.account import NoAccount
from src.domain.employee import Admin
from src.domain.exceptions import ItemNotFoundError
from src.domain.repositories.admin_repository import AdminRepository
from utils.db.connect import Connection
from utils.db.exceptions import DBOperationError


# admin_repo.py (or wherever your repository is)







def date_from_sqlite_iso(date_created: str) -> datetime:
    try:
        date = datetime.fromisoformat(date_created)
    except ValueError:
        date = datetime.now()
    return date


class AdminRepositorySQLite(AdminRepository):

    def __init__(self, conn: Connection):
        self._saved_version=0
        self.ADMIN_SELECT = (
            "SELECT "
            "e.employee_id, e.first_name, e.last_name, e.email, e.phone, e.date_created, "
            "e.enabled, e.is_deleted, e.version, "
            "a.admin_id, a.job_title "
            "FROM admins a "
            "JOIN employees e ON e.employee_id = a.employee_id"
        )

        self.ADMIN_VARS = [
            "employee_id", "first_name", "last_name", "email", "phone", "date_created",
            "enabled", "is_deleted", "version",
            "admin_id", "job_title"
        ]

        self.conn = conn

        self.saved_version = 0

    @staticmethod
    def _row_to_admin(row: dict) -> Admin:
        return Admin.create(
            employee_id=row["employee_id"],
            first_name=row["first_name"],  # if these are Name objects already, OK; if strings, wrap
            last_name=row["last_name"],
            email=row["email"],
            phone=row["phone"],
            enabled=bool(row["enabled"]),  # ✅ fixed
            date_created=date_from_sqlite_iso(row["date_created"]),
            version=row["version"],
            job_title=row["job_title"],
            # account_id=row.get("account_id")  # if you add it to SELECT later
        )

    def get(self, admin_id: int) -> Admin:
        sql = self.ADMIN_SELECT + " WHERE a.admin_id = :admin_id"
        with self.conn.create_query(sql, var=self.ADMIN_VARS) as q:
            row = q.get_one_result(params={"admin_id": admin_id})

        if not row:
            raise ItemNotFoundError(item_name=f"Admin {admin_id} isn't found") # or raise NotFoundError (better)
        return self._row_to_admin(row)

    def get_all(self) -> list[Admin]:
        with self.conn.create_query(self.ADMIN_SELECT, var=self.ADMIN_VARS) as q:
            rows = q.get_result()

        return [self._row_to_admin(r) for r in rows]

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


    def exists(self, admin_id: int) -> bool:
        pass

    def save(self, admin: Admin) -> Admin:
        """Save the entire aggregate to persistence"""
        try:
            # Clear existing admins
            insert_query_employee=self.conn.create_query("INSERT INTO employees (first_name, last_name, email,phone,date_created,address,enabled,version) "
                                                         " VALUES (:first_name, :last_name, :email,:phone,:date_created,:address,:enabled,:version)")

            insert_query_admin=self.conn.create_query("INSERT INTO admins (employee_id, job_title) VALUES (:employee_id, :job_title)")


            if admin.employee_id == 0:
                insert_query_employee.set_result(params={'first_name': admin.first_name, 'last_name': admin.last_name, 'email': admin.email,})
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
                    params['admin_id'] = admin.admin_id
                    query_exists_admin.set_result(params=params)
        except Exception as e:
            raise DBOperationError(f"Failed to save admins: {str(e)}")

    def delete(self, admin_id: int):
        pass

    def find_by_login(self, *, login: str) -> Admin:
        pass

    def exist_login(self, login: str) -> bool:
        pass