from __future__ import annotations

from datetime import datetime

from src.domain.account import Account, NoAccount, AccountType
from src.domain.employee import Admin


def _dt_from_sqlite(value: str | int | None) -> datetime:
    """
    You said date_created INTEGER. But some parts of your code used ISO strings.
    This supports:
      - ISO string
      - unix timestamp int
      - None
    """
    if value is None:
        return datetime.now()

    if isinstance(value, int):
        # interpret as unix timestamp seconds
        try:
            return datetime.fromtimestamp(value)
        except Exception:
            return datetime.now()

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            # try int-like string
            try:
                return datetime.fromtimestamp(int(value))
            except Exception:
                return datetime.now()

    return datetime.now()


def _dt_to_sqlite_iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


class AdminMapper:
    """
    Converts DB rows <-> Admin aggregate params.
    """

    @staticmethod
    def row_to_admin(row: dict) -> Admin:
        admin = Admin.create(
            employee_id=int(row["employee_id"]),
            job_title=str(row.get("job_title") or ""),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            email=row.get("email"),
            phone=row.get("phone"),
        )

        admin.enabled = bool(row.get("enabled", 1))
        admin.version = int(row.get("version", 0))
        admin.date_created = _dt_from_sqlite(row.get("date_created"))

        # Optional account: account_id present => build Account
        admin.account = AdminMapper.row_to_account(row)

        return admin

    @staticmethod
    def row_to_account(row: dict) -> AccountType:
        acc_id = row.get("account_id")
        if not acc_id:
            return NoAccount()

        # Account.from_database expects hash already stored
        return Account.from_database(
            account_id=int(acc_id),
            login=str(row.get("login") or ""),
            password_hash=str(row.get("password") or ""),
            enabled=bool(row.get("account_enabled", 1)),
            date_created=_dt_from_sqlite(row.get("account_date_created")),
        )

    @staticmethod
    def employee_params(admin: Admin) -> dict:
        """
        Params used for INSERT/UPDATE employees.
        Note: 'is_admin' is provided by repository for INSERT.
        """
        return {
            "employee_id": int(admin.employee_id),
            "first_name": str(admin.first_name) if admin.first_name is not None else "",
            "last_name": str(admin.last_name) if admin.last_name is not None else "",
            "email": str(admin.email) if admin.email is not None else "",
            "phone": str(admin.phone) if admin.phone is not None else "",
            "date_created": _dt_to_sqlite_iso(admin.date_created),
            "enabled": 1 if admin.enabled else 0,
            "version": int(admin.version),
        }

    @staticmethod
    def admin_params(admin: Admin) -> dict:
        return {
            "employee_id": int(admin.employee_id),
            "job_title": str(admin.job_title or ""),
        }

    @staticmethod
    def account_params(admin: Admin) -> dict | None:
        """
        If admin.account is NoAccount -> None (caller deletes account row)
        If Account -> upsert params.
        """
        if isinstance(admin.account, NoAccount):
            return None

        # Account.password is a Password VO with hash in .value
        return {
            "employee_id": int(admin.employee_id),
            "login": str(admin.account.login),
            "password": admin.account.password.value,
            "enabled": 1 if admin.account.enabled else 0,
            "date_created": _dt_to_sqlite_iso(admin.account.date_created),
        }

