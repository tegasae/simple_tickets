# src/infrastructure/repositories/sqlite_account_repository.py
from __future__ import annotations

from datetime import datetime

from src.domain.account import Account, AccountType, NoAccount
from src.domain.exceptions import DomainOperationError
from src.domain.repositories.account_repository import AccountRepository

from utils.db.connect import Connection


def date_to_sqlite_iso(dt: datetime) -> str:
    # Store ISO8601 text
    return dt.isoformat(timespec="seconds")


def date_from_sqlite_iso(s: str | None) -> datetime:
    if not s:
        return datetime.min
    # sqlite stores text; assume isoformat
    return datetime.fromisoformat(s)


class AccountRepositorySQLite(AccountRepository):
    """
    SQLite implementation for AccountRepository using your Connection/Query wrapper.

    Table:
      accounts(account_id PK, employee_id FK, enabled, login UNIQUE, password, date_created)
    """

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    # ---------- Reads ----------

    def get(self, account_id: int) -> AccountType:
        sql = (
            "SELECT account_id, employee_id, enabled, login, password, date_created "
            "FROM accounts WHERE account_id = :account_id"
        )
        with self.conn.create_query(
            sql,
            var=["account_id", "employee_id", "enabled", "login", "password", "date_created"],
        ) as q:
            row = q.get_one_result(params={"account_id": account_id})

        if not row:
            # Your interface says AccountType, but comment says "never returns NoAccount".
            # So raise (recommended) rather than returning a Null object.
            raise DomainOperationError(f"Account {account_id} not found")

        return Account.from_database(
            account_id=row["account_id"],
            login=row["login"],
            password_hash=row["password"],
            enabled=bool(row["enabled"]),
            date_created=date_from_sqlite_iso(row["date_created"]),
        )

    def get_employee_id(self, employee_id: int) -> AccountType:
        sql = (
            "SELECT account_id, employee_id, enabled, login, password, date_created "
            "FROM accounts WHERE employee_id = :employee_id"
        )
        with self.conn.create_query(
            sql,
            var=["account_id", "employee_id", "enabled", "login", "password", "date_created"],
        ) as q:
            row = q.get_one_result(params={"employee_id": employee_id})

        if not row:
            # Your interface says AccountType, but comment says "never returns NoAccount".
            # So raise (recommended) rather than returning a Null object.
            #raise DomainOperationError(f"Account for employee_id {employee_id} not found")
            return NoAccount()

        return Account.from_database(
            account_id=row["account_id"],
            login=row["login"],
            password_hash=row["password"],
            enabled=bool(row["enabled"]),
            date_created=date_from_sqlite_iso(row["date_created"]),
        )



    def get_all(self) -> list[Account]:
        sql = "SELECT account_id, employee_id, enabled, login, password, date_created FROM accounts"
        with self.conn.create_query(
            sql,
            var=["account_id", "employee_id", "enabled", "login", "password", "date_created"],
        ) as q:
            rows = q.get_result()

        accounts: list[Account] = []
        for row in rows:
            accounts.append(
                Account.from_database(
                    account_id=row["account_id"],
                    login=row["login"],
                    password_hash=row["password"],
                    enabled=bool(row["enabled"]),
                    date_created=date_from_sqlite_iso(row["date_created"]),
                )
            )
        return accounts

    def exists(self, account_id: int) -> bool:
        sql = "SELECT 1 AS one FROM accounts WHERE account_id = :account_id LIMIT 1"
        with self.conn.create_query(sql, var=["one"]) as q:
            row = q.get_one_result(params={"account_id": account_id})
        return bool(row)

    def find_by_login(self, login: str) -> int:
        """
        Returns employee_id for account with given login.
        If not found -> 0 (since your signature returns int, not Optional[int]).
        """
        sql = "SELECT employee_id FROM accounts WHERE login = :login LIMIT 1"
        with self.conn.create_query(sql, var=["employee_id"]) as q:
            row = q.get_one_result(params={"login": login})
        if not row:
            return 0
        # employee_id may be NULL if you allow that; normalize to 0
        return int(row["employee_id"] or 0)

    def does_login_exist(self, login: str) -> bool:
        employee_id=self.find_by_login(login=login)
        return bool(employee_id)

    def account_is_enabled_by_login(self, login: str) -> bool:
        sql = "SELECT enabled FROM accounts WHERE login = :login LIMIT 1"
        with self.conn.create_query(sql, var=["enabled"]) as q:
            row = q.get_one_result(params={"login": login})
        if not row:
            return False
        return bool(row["enabled"])

    # ---------- Writes ----------

    def save(self, account: Account, employee_id: int = 0) -> Account:
        """
        Inserts new account if account_id == 0, otherwise updates existing.

        Returns the saved account (with new account_id if inserted).
        """
        # Normalize employee_id: store NULL if 0
        emp_fk = None if employee_id == 0 else employee_id
        if getattr(account, "account_id", 0) in (0, None):
            sql = (
                "INSERT INTO accounts (employee_id, enabled, login, password, date_created) "
                "VALUES (:employee_id, :enabled, :login, :password, :date_created)"
            )
            params = {
                "employee_id": emp_fk,
                "enabled": 1 if account.enabled else 0,
                "login": str(account.login),   # Login VO -> string
                "password": str(account.password.value) if hasattr(account.password, "value") else str(account.password),
                "date_created": date_to_sqlite_iso(account.date_created),

            }
            with self.conn.create_query(sql, params=params) as q:
                new_id = q.set_result()

            # Reconstitute account with the new id
            return Account.from_database(
                account_id=int(new_id),
                login=str(account.login),
                password_hash=params["password"],
                enabled=account.enabled,
                date_created=account.date_created,
            )

        # UPDATE
        sql = (
            "UPDATE accounts SET "
            "employee_id = :employee_id, "
            "enabled = :enabled, "
            "login = :login, "
            "password = :password "
            "WHERE account_id = :account_id"
        )
        params = {
            "account_id": account.account_id,
            "employee_id": emp_fk,
            "enabled": 1 if account.enabled else 0,
            "login": str(account.login),
            "password": str(account.password.value) if hasattr(account.password, "value") else str(account.password),
        }
        with self.conn.create_query(sql, params=params) as q:
            q.set_result()

        return account

    def delete(self, employee_id: int) -> None:
        """
        Deletes account row(s) for an employee.

        Note: because FK is (employee_id) -> employees(employee_id) RESTRICT,
        deleting employee first will fail if account exists; delete account first.
        """
        sql = "DELETE FROM accounts WHERE employee_id = :employee_id"
        with self.conn.create_query(sql, params={"employee_id": employee_id}) as q:
            q.set_result()

