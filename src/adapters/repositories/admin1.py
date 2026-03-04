# src/adapters/repository/admin.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.employee import Admin
from src.domain.exceptions import ItemNotFoundError
from src.domain.repositories.admin_repository import AdminRepository
from utils.db.connect import Connection
from utils.db.exceptions import DBOperationError


def date_from_sqlite_iso(date_created: str | None) -> datetime:
    if not date_created:
        return datetime.now()
    try:
        return datetime.fromisoformat(date_created)
    except ValueError:
        return datetime.now()


@dataclass(frozen=True)
class _QueryAdmin:
    # NOTE: in the new schema, admins.employee_id is the PK (no admin_id column)
    ADMIN_SELECT = (
        "SELECT "
        "e.employee_id, e.first_name, e.last_name, e.email, e.phone, e.date_created, "
        "e.enabled, e.version, "
        "a.job_title "
        "FROM admins a "
        "JOIN employees e ON e.employee_id = a.employee_id"
    )

    ADMIN_SELECT_BY_EMPLOYEE_ID = ADMIN_SELECT + " WHERE e.employee_id = :employee_id"

    ADMIN_SELECT_BY_LOGIN = (
        ADMIN_SELECT
        + " JOIN accounts acc ON acc.employee_id = e.employee_id "
          "WHERE acc.login = :login"
    )

    ADMIN_VARS = [
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "date_created",
        "enabled",
        "version",
        "job_title",
    ]


class AdminRepositorySQLite(AdminRepository):
    def __init__(self, conn: Connection):
        self.conn = conn

    @staticmethod
    def _row_to_admin(row: dict) -> Admin:
        # Keep mapping simple; Admin.create() expects strings (your current model).
        # If your Admin.create() doesn't accept date_created/version, switch to Admin(...) init.
        admin = Admin.create(
            employee_id=row["employee_id"],
            job_title=row.get("job_title", "") or "",
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            email=row.get("email"),
            phone=row.get("phone"),
        )
        # Preserve persistence fields if they exist on the entity
        admin.enabled = bool(row.get("enabled", 1))
        admin.version = int(row.get("version", 0))
        admin.date_created = date_from_sqlite_iso(row.get("date_created"))
        return admin

    # -------- Reads --------

    def get(self, admin_id: int) -> Admin:
        # admin_id here is employee_id (aggregate id)
        with self.conn.create_query(
            _QueryAdmin.ADMIN_SELECT_BY_EMPLOYEE_ID,
            var=_QueryAdmin.ADMIN_VARS,
        ) as q:
            row = q.get_one_result(params={"employee_id": admin_id})

        if not row:
            raise ItemNotFoundError(item_name=f"Admin {admin_id} isn't found")

        return self._row_to_admin(row)

    def get_all(self) -> list[Admin]:
        with self.conn.create_query(_QueryAdmin.ADMIN_SELECT, var=_QueryAdmin.ADMIN_VARS) as q:
            rows = q.get_result()
        return [self._row_to_admin(r) for r in rows]

    def exists(self, admin_id: int) -> bool:
        sql = "SELECT 1 AS one FROM admins WHERE employee_id = :employee_id LIMIT 1"
        with self.conn.create_query(sql, var=["one"]) as q:
            row = q.get_one_result(params={"employee_id": admin_id})
        return bool(row)

    def find_by_login(self, *, login: str) -> Admin:
        with self.conn.create_query(_QueryAdmin.ADMIN_SELECT_BY_LOGIN, var=_QueryAdmin.ADMIN_VARS) as q:
            row = q.get_one_result(params={"login": login})

        if not row:
            raise ItemNotFoundError(item_name=f"Admin with login '{login}' isn't found")

        return self._row_to_admin(row)

    def exist_login(self, login: str) -> bool:
        sql = "SELECT 1 AS one FROM accounts WHERE login = :login LIMIT 1"
        with self.conn.create_query(sql, var=["one"]) as q:
            row = q.get_one_result(params={"login": login})
        return bool(row)

    def exist_role(self, role_id: int) -> bool:
        # New table name: admins_roles (not admin_roles / admins_role)
        sql = (
            "SELECT 1 AS one "
            "FROM admins_roles ar "
            "JOIN admins a ON a.employee_id = ar.employee_id "
            "WHERE ar.role_id = :role_id "
            "LIMIT 1"
        )
        with self.conn.create_query(sql, var=["one"]) as q:
            row = q.get_one_result(params={"role_id": role_id})
        return bool(row)

    # -------- Writes --------

    def save(self, admin: Admin) -> Admin:
        """
        Aggregate version is stored in employees.version and is updated with optimistic locking.
        """
        try:
            insert_employee = self.conn.create_query(
                "INSERT INTO employees (first_name, last_name, email, phone, date_created, enabled, version, is_admin) "
                "VALUES (:first_name, :last_name, :email, :phone, :date_created, :enabled, :version, 1)"
            )
            insert_admin = self.conn.create_query(
                "INSERT INTO admins (employee_id, job_title) VALUES (:employee_id, :job_title)"
            )

            update_employee = self.conn.create_query(
                "UPDATE employees SET "
                "first_name = :first_name, "
                "last_name  = :last_name, "
                "email      = :email, "
                "phone      = :phone, "
                "date_created = :date_created, "
                "enabled    = :enabled, "
                "version    = version + 1 "
                "WHERE employee_id = :employee_id AND version = :expected_version"
            )

            update_admin = self.conn.create_query(
                "UPDATE admins SET job_title = :job_title WHERE employee_id = :employee_id"
            )

            if admin.employee_id == 0:
                new_id = insert_employee.set_result(
                    params={
                        "first_name": str(admin.first_name) if admin.first_name else "",
                        "last_name": str(admin.last_name) if admin.last_name else "",
                        "email": str(admin.email) if admin.email else "",
                        "phone": str(admin.phone) if admin.phone else "",
                        "date_created": admin.date_created.isoformat(timespec="seconds"),
                        "enabled": 1 if admin.enabled else 0,
                        "version": 0,
                    }
                )
                admin.employee_id = int(new_id)
                insert_admin.set_result(params={"employee_id": admin.employee_id, "job_title": admin.job_title})
                admin.version = 0
                return admin

            # UPDATE (optimistic lock)
            update_employee.set_result(
                params={
                    "employee_id": admin.employee_id,
                    "first_name": str(admin.first_name) if admin.first_name else "",
                    "last_name": str(admin.last_name) if admin.last_name else "",
                    "email": str(admin.email) if admin.email else "",
                    "phone": str(admin.phone) if admin.phone else "",
                    "date_created": admin.date_created.isoformat(timespec="seconds"),
                    "enabled": 1 if admin.enabled else 0,
                    "expected_version": admin.version,
                }
            )
            if not update_employee.count:
                raise DBOperationError("Optimistic lock failed: version mismatch")

            update_admin.set_result(params={"employee_id": admin.employee_id, "job_title": admin.job_title})

            # bump in-memory version after successful save
            admin.version += 1
            return admin

        except Exception as e:
            raise DBOperationError(f"Failed to save admin: {e}")

    def delete(self, admin_id: int) -> None:
        """
        Hard delete admin aggregate (employees + admins + admins_roles).
        """
        try:
            delete_roles = self.conn.create_query(
                "DELETE FROM admins_roles WHERE employee_id = :employee_id"
            )
            delete_admin = self.conn.create_query(
                "DELETE FROM admins WHERE employee_id = :employee_id"
            )
            delete_employee = self.conn.create_query(
                "DELETE FROM employees WHERE employee_id = :employee_id"
            )

            delete_roles.set_result(params={"employee_id": admin_id})
            delete_admin.set_result(params={"employee_id": admin_id})
            delete_employee.set_result(params={"employee_id": admin_id})

        except Exception as e:
            raise DBOperationError(f"Failed to delete admin {admin_id}: {e}")