from datetime import datetime

from src.domain.account import Account, NoAccount
from src.domain.employee import Admin


class AdminMapper:

    @staticmethod
    def row_to_admin(row: dict) -> Admin:
        admin = Admin.create(
            employee_id=row["employee_id"],
            job_title=row["job_title"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row["phone"],
        )

        admin.enabled = bool(row["enabled"])
        admin.version = row["version"]
        admin.date_created = datetime.fromisoformat(row["date_created"])

        return admin

    @staticmethod
    def employee_params(admin: Admin) -> dict:
        return {
            "employee_id": admin.employee_id,
            "first_name": str(admin.first_name),
            "last_name": str(admin.last_name),
            "email": str(admin.email),
            "phone": str(admin.phone),
            "enabled": int(admin.enabled),
            "version": admin.version,
            "date_created": admin.date_created.isoformat(),
        }

    @staticmethod
    def admin_params(admin: Admin) -> dict:
        return {
            "employee_id": admin.employee_id,
            "job_title": admin.job_title,
        }

    @staticmethod
    def account_params(admin: Admin) -> dict | None:
        if isinstance(admin.account, NoAccount):
            return None

        account = admin.account

        return {
            "employee_id": admin.employee_id,
            "login": str(account.login),
            "password": account.password.value,
            "enabled": int(account.enabled),
            "date_created": account.date_created.isoformat(),
        }
    