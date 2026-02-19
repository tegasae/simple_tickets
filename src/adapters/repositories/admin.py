#src/adapters/repository/admin.py
from dataclasses import dataclass
from datetime import datetime

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

@dataclass(frozen=True)
class _QueryAdmin:
        ADMIN_SELECT=(
            "SELECT "
            "e.employee_id, e.first_name, e.last_name, e.email, e.phone, e.date_created, "
            "e.enabled, e.is_deleted, e.version, "
            "a.admin_id, a.job_title "
            "FROM admins a "
            "JOIN employees e ON e.employee_id = a.employee_id WHERE is_admin=1 "
        )

        ADMIN_VARS = [
            "employee_id", "first_name", "last_name", "email", "phone", "date_created",
            "enabled", "is_deleted", "version",
            "admin_id", "job_title"
        ]



class AdminRepositorySQLite(AdminRepository):

    def __init__(self, conn: Connection):
        self._saved_version=0
        self.conn = conn



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
        sql = _QueryAdmin.ADMIN_SELECT + " AND a.admin_id = :admin_id"

        with self.conn.create_query(sql, var=_QueryAdmin.ADMIN_VARS) as q:
            row = q.get_one_result(params={"admin_id": admin_id})
        if not row:
            raise ItemNotFoundError(item_name=f"Admin {admin_id} isn't found") # or raise NotFoundError (better)


        return self._row_to_admin(row)

    def get_all(self) -> list[Admin]:
        with self.conn.create_query(_QueryAdmin.ADMIN_SELECT, var=_QueryAdmin.ADMIN_VARS) as q:
            rows = q.get_result()

        return [self._row_to_admin(r) for r in rows]


    def exists(self, admin_id: int) -> bool:
        count_query=self.conn.create_query("SELECT count(admin_id) FROM admins WHERE employee_id = :employee_id")
        result=count_query.get_one_result(params={"employee_id": admin_id})
        return result[0]==1 or False

    def save(self, admin: Admin) -> Admin:
        """Save the entire aggregate to persistence"""
        try:
            # Clear existing admins
            insert_query_employee=self.conn.create_query("INSERT INTO employees (first_name, last_name, email,phone,date_created,enabled,version,is_admin) "
                                                         " VALUES (:first_name, :last_name, :email,:phone,:date_created,:enabled,:version,1)")

            insert_query_admin=self.conn.create_query("INSERT INTO admins (employee_id, job_title) VALUES (:employee_id, :job_title)")

            update_query_employee = self.conn.create_query(
                "UPDATE employees SET first_name=:first_name, last_name=:last_name, email=:email,phone=:phone,date_created=:date_created,enabled=:enabled,version = :version +1 "
                "WHERE employee_id=:employee_id AND version=:version AND is_admin=1")


            update_query_admin = self.conn.create_query(
                "UPDATE admins SET job_title=:job_title WHERE employee_id=:employee_id")

            if admin.employee_id == 0:
                admin.employee_id=insert_query_employee.set_result(params={'first_name': str(admin.first_name), 'last_name': str(admin.last_name), 'email': str(admin.email),
                                                                           'enabled':int(admin.enabled),
                                                         'phone': str(admin.phone), 'date_created': admin.date_created.isoformat(),'version': 0})
                insert_query_admin.set_result(params={'employee_id': admin.employee_id, 'job_title': admin.job_title})
            else:
                update_query_employee.set_result(params={'employee_id':admin.employee_id,'first_name': str(admin.first_name), 'last_name': str(admin.last_name),'phone': str(admin.phone),
                                                         'email': str(admin.email),'enabled':bool(admin.enabled),'date_created': admin.date_created.isoformat(),'version': admin.version})
                if not update_query_employee.count:
                    raise DBOperationError(f"The version is wrong")

                update_query_admin.set_result(params={'employee_id': admin.employee_id, 'job_title': admin.job_title})
            return admin
        except Exception as e:
            raise DBOperationError(f"Failed to save admins: {str(e)}")

    def delete(self, admin_id: int):
        try:
            delete_query_employee=self.conn.create_query("DELETE FROM employees WHERE employee_id = :employee_id")
            delete_query_admin=self.conn.create_query("DELETE FROM admins WHERE employee_id = :employee_id")
            delete_query_employee.set_result(params={'employee_id': admin_id})
            delete_query_admin.set_result(params={'employee_id': admin_id})
        except Exception as e:
            raise DBOperationError(f"Failed to delete admin: {str(e)} {admin_id}")




    def find_by_login(self, *, login: str) -> Admin:
        pass

    def exist_login(self, login: str) -> bool:
        pass

