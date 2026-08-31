

from src.adapters.repositories.mappers.auxiliary import dt_from_sqlite
from src.domain.account import Account, NoAccount
from src.domain.employee import User




class UserMapper:
    VARS = [
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "date_created",
        "enabled",
        "version",
        "client_id",
        "account_id",
        "login",
        "password",
        "account_enabled",
        "account_date_created",
    ]

    @staticmethod
    def row_to_user(row: dict) -> User:
        user = User.create(
            employee_id=row["employee_id"],
            client_id=row["client_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row["phone"],
        )

        user.enabled = bool(row["enabled"])
        user.version = int(row["version"] or 0)
        user.date_created = dt_from_sqlite(row.get("date_created"))
        user.account = UserMapper.row_to_account(row)
        return user

    @staticmethod
    def employee_params(user: User) -> dict:
        return {
            "employee_id": user.employee_id,
            "first_name": str(user.first_name),
            "last_name": str(user.last_name),
            "email": str(user.email),
            "phone": str(user.phone),
            "enabled": int(user.enabled),
            "version": int(user.version),
            # you said you prefer INTEGER for date_created:
            "date_created":  dt_from_sqlite(user.date_created),
            # required by EmployeeGateway.UPDATE
            "is_admin": 0,
        }

    @staticmethod
    def user_params(user: User) -> dict:
        return {
            "employee_id": user.employee_id,
            "client_id": user.client_id,
        }

    @staticmethod
    def account_params(user: User) -> dict | None:
        # NoAccount should be falsy in your code
        if not user.account:
            return None

        return {
            "employee_id": user.employee_id,
            "login": str(user.account.login),
            "password": user.account.password.value,  # hash string
            "enabled": int(user.account.enabled),
            "date_created": dt_from_sqlite(user.account.date_created),
        }

    @staticmethod
    def row_to_account(row: dict) -> Account | NoAccount:
        acc_id = row.get("account_id")
        if not acc_id:
            return NoAccount()

        # Account.from_database expects hash already stored
        return Account.from_database(
            account_id=int(acc_id),
            login=str(row.get("login") or ""),
            password_hash=str(row.get("password") or ""),
            enabled=bool(row.get("account_enabled", 1)),
            date_created=dt_from_sqlite(row.get("account_date_created")),
        )