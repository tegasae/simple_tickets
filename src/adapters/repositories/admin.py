from dataclasses import dataclass

from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.mappers.admin_mapper import AdminMapper

from src.domain.employee import Admin
from src.domain.exceptions import ItemNotFoundError
from src.domain.repositories.admin_repository import AdminRepository
from src.domain.account import Account

from utils.db.exceptions import DBOperationError


@dataclass(frozen=True)
class _QueryAdmin:

    ADMIN_SELECT = (
        "SELECT "
        "e.employee_id, e.first_name, e.last_name, e.email, e.phone, "
        "e.date_created, e.enabled, e.version, "
        "a.job_title "
        "FROM admins a "
        "JOIN employees e ON e.employee_id = a.employee_id "
        "WHERE e.is_admin = 1 "
    )

    ADMIN_BY_ID = ADMIN_SELECT + "AND e.employee_id = :employee_id"

    ADMIN_BY_LOGIN = (
        "SELECT "
        "e.employee_id, e.first_name, e.last_name, e.email, e.phone, "
        "e.date_created, e.enabled, e.version, "
        "a.job_title "
        "FROM accounts acc "
        "JOIN employees e ON e.employee_id = acc.employee_id "
        "JOIN admins a ON a.employee_id = e.employee_id "
        "WHERE acc.login = :login AND e.is_admin = 1"
    )

    VARS = [
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

    ROLE_SELECT = "SELECT role_id FROM admins_roles WHERE employee_id=:employee_id"
    ROLE_INSERT = "INSERT INTO admins_roles (employee_id,role_id) VALUES (:employee_id,:role_id)"
    ROLE_DELETE_ALL = "DELETE FROM admins_roles WHERE employee_id=:employee_id"
    ROLE_DELETE_ONE = "DELETE FROM admins_roles WHERE employee_id=:employee_id AND role_id=:role_id"

    ACCOUNT_DELETE = "DELETE FROM accounts WHERE employee_id=:employee_id"

    ACCOUNT_UPSERT = (
        "INSERT INTO accounts (employee_id,login,password,enabled,date_created) "
        "VALUES (:employee_id,:login,:password,:enabled,:date_created) "
        "ON CONFLICT(employee_id) DO UPDATE SET "
        "login=excluded.login,password=excluded.password,enabled=excluded.enabled"
    )


class AdminRepositorySQLite(BaseRepository, AdminRepository):

    # -------------------------
    # Internal helpers
    # -------------------------

    def _load_roles(self, employee_id: int) -> set[int]:

        rows = self._get_many(
            _QueryAdmin.ROLE_SELECT,
            ["role_id"],
            {"employee_id": employee_id},
        )

        return {r["role_id"] for r in rows}

    def _replace_roles(self, admin: Admin):

        self._execute(
            _QueryAdmin.ROLE_DELETE_ALL,
            {"employee_id": admin.employee_id},
        )

        if not admin.role_ids():
            return

        for role_id in admin.role_ids():

            self._execute(
                _QueryAdmin.ROLE_INSERT,
                {
                    "employee_id": admin.employee_id,
                    "role_id": role_id,
                },
            )

    def _sync_account(self, admin: Admin):

        params = AdminMapper.account_params(admin)

        if params is None:

            self._execute(
                _QueryAdmin.ACCOUNT_DELETE,
                {"employee_id": admin.employee_id},
            )

        else:

            self._execute(
                _QueryAdmin.ACCOUNT_UPSERT,
                params,
            )

    # -------------------------
    # Reads
    # -------------------------

    def get(self, admin_id: int) -> Admin:

        row = self._get_one(
            _QueryAdmin.ADMIN_BY_ID,
            _QueryAdmin.VARS,
            {"employee_id": admin_id},
        )

        if not row:
            raise ItemNotFoundError(f"Admin {admin_id} not found")

        admin = AdminMapper.row_to_admin(row)

        admin._role_ids = self._load_roles(admin.employee_id)

        return admin

    def get_all(self) -> list[Admin]:

        rows = self._get_many(
            _QueryAdmin.ADMIN_SELECT,
            _QueryAdmin.VARS,
        )

        admins = []

        for row in rows:

            admin = AdminMapper.row_to_admin(row)

            admin._role_ids = self._load_roles(admin.employee_id)

            admins.append(admin)

        return admins

    def exists(self, admin_id: int) -> bool:

        return self._exists(
            "SELECT 1 FROM admins WHERE employee_id=:employee_id LIMIT 1",
            {"employee_id": admin_id},
        )

    def find_by_login(self, *, login: str) -> Admin:

        row = self._get_one(
            _QueryAdmin.ADMIN_BY_LOGIN,
            _QueryAdmin.VARS,
            {"login": login},
        )

        if not row:
            raise ItemNotFoundError(f"Admin with login '{login}' not found")

        admin = AdminMapper.row_to_admin(row)

        admin._role_ids = self._load_roles(admin.employee_id)

        return admin

    # -------------------------
    # Writes
    # -------------------------

    def save(self, admin: Admin) -> Admin:

        try:

            insert_employee_sql = (
                "INSERT INTO employees "
                "(first_name,last_name,email,phone,date_created,enabled,version,is_admin) "
                "VALUES "
                "(:first_name,:last_name,:email,:phone,:date_created,:enabled,:version,1)"
            )

            insert_admin_sql = (
                "INSERT INTO admins (employee_id,job_title) "
                "VALUES (:employee_id,:job_title)"
            )

            update_employee_sql = (
                "UPDATE employees SET "
                "first_name=:first_name, "
                "last_name=:last_name, "
                "email=:email, "
                "phone=:phone, "
                "enabled=:enabled, "
                "version=version+1 "
                "WHERE employee_id=:employee_id "
                "AND version=:version "
                "AND is_admin=1"
            )

            update_admin_sql = (
                "UPDATE admins SET job_title=:job_title "
                "WHERE employee_id=:employee_id"
            )

            # ---------- create ----------

            if admin.employee_id == 0:

                params = AdminMapper.employee_params(admin)

                admin.employee_id = self._execute(
                    insert_employee_sql,
                    params,
                )

                self._execute(
                    insert_admin_sql,
                    AdminMapper.admin_params(admin),
                )

                self._replace_roles(admin)

                self._sync_account(admin)

                return admin

            # ---------- update ----------

            params = AdminMapper.employee_params(admin)

            self._execute(update_employee_sql, params)

            if params["version"] == admin.version:
                pass
            else:
                raise DBOperationError("Optimistic lock failed")

            self._execute(
                update_admin_sql,
                AdminMapper.admin_params(admin),
            )

            self._replace_roles(admin)

            self._sync_account(admin)

            admin.version += 1

            return admin

        except Exception as e:

            raise DBOperationError(f"Failed to save admin: {e}")

    def delete(self, admin_id: int):

        try:

            self._execute(
                _QueryAdmin.ACCOUNT_DELETE,
                {"employee_id": admin_id},
            )

            self._execute(
                _QueryAdmin.ROLE_DELETE_ALL,
                {"employee_id": admin_id},
            )

            self._execute(
                "DELETE FROM admins WHERE employee_id=:employee_id",
                {"employee_id": admin_id},
            )

            self._execute(
                "DELETE FROM employees WHERE employee_id=:employee_id AND is_admin=1",
                {"employee_id": admin_id},
            )

        except Exception as e:

            raise DBOperationError(f"Failed to delete admin {admin_id}: {e}")

    # -------------------------
    # Role operations
    # -------------------------

    def grant_role(self, *, employee_id: int, role_id: int):

        self._execute(
            _QueryAdmin.ROLE_INSERT,
            {
                "employee_id": employee_id,
                "role_id": role_id,
            },
        )

    def revoke_role(self, *, employee_id: int, role_id: int):

        self._execute(
            _QueryAdmin.ROLE_DELETE_ONE,
            {
                "employee_id": employee_id,
                "role_id": role_id,
            },
        )

    def get_role_ids(self, *, employee_id: int) -> set[int]:

        return self._load_roles(employee_id)

    # -------------------------
    # Account operations
    # -------------------------

    def set_no_account(self, *, employee_id: int):

        self._execute(
            _QueryAdmin.ACCOUNT_DELETE,
            {"employee_id": employee_id},
        )

    def set_account_from_plain_password(
        self,
        *,
        employee_id: int,
        login: str,
        plain_password: str,
    ):

        account = Account.create(
            account_id=0,
            login=login,
            plain_password=plain_password,
        )

        params = {
            "employee_id": employee_id,
            "login": str(account.login),
            "password": account.password.value,
            "enabled": 1,
            "date_created": account.date_created.isoformat(),
        }

        self._execute(
            _QueryAdmin.ACCOUNT_UPSERT,
            params,
        )