from __future__ import annotations


class AccountGateway:
    """
    accounts table gateway.
    Schema assumed:
      accounts(account_id PK AUTOINCREMENT, employee_id UNIQUE FK->employees,
               login UNIQUE, password, enabled, date_created)
    """

    DELETE_BY_EMPLOYEE = "DELETE FROM accounts WHERE employee_id = :employee_id"

    UPSERT_BY_EMPLOYEE = (
        "INSERT INTO accounts (employee_id, login, password, enabled, date_created) "
        "VALUES (:employee_id, :login, :password, :enabled, :date_created) "
        "ON CONFLICT(employee_id) DO UPDATE SET "
        "login=excluded.login, password=excluded.password, enabled=excluded.enabled"
    )

