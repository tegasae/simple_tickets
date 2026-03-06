from __future__ import annotations


class AdminGateway:
    """
    admins table gateway (1:1 with employees).
    Schema assumed:
      admins(employee_id PK FK->employees, job_title)
    """

    INSERT = (
        "INSERT INTO admins (employee_id, job_title) "
        "VALUES (:employee_id, :job_title)"
    )

    UPDATE = (
        "UPDATE admins SET job_title = :job_title "
        "WHERE employee_id = :employee_id"
    )

    DELETE = (
        "DELETE FROM admins "
        "WHERE employee_id = :employee_id"
    )

    # IMPORTANT: include accounts via LEFT JOIN so get/get_all see account
    SELECT_BASE = (
        "SELECT "
        "e.employee_id, e.first_name, e.last_name, e.email, e.phone, e.date_created, "
        "e.enabled, e.version, "
        "a.job_title, "
        "acc.account_id, acc.login, acc.password, acc.enabled AS account_enabled, acc.date_created AS account_date_created "
        "FROM admins a "
        "JOIN employees e ON e.employee_id = a.employee_id "
        "LEFT JOIN accounts acc ON acc.employee_id = e.employee_id "
        "WHERE e.is_admin = 1"
    )

    SELECT_BY_ID = SELECT_BASE + " AND e.employee_id = :employee_id"

    SELECT_BY_LOGIN = (
        "SELECT "
        "e.employee_id, e.first_name, e.last_name, e.email, e.phone, e.date_created, "
        "e.enabled, e.version, "
        "a.job_title, "
        "acc.account_id, acc.login, acc.password, acc.enabled AS account_enabled, acc.date_created AS account_date_created "
        "FROM accounts acc "
        "JOIN employees e ON e.employee_id = acc.employee_id "
        "JOIN admins a ON a.employee_id = e.employee_id "
        "WHERE e.is_admin = 1 AND acc.login = :login"
    )

    EXISTS = "SELECT 1 AS one FROM admins WHERE employee_id = :employee_id LIMIT 1"

    EXISTS_LOGIN = """
        SELECT 1 AS one
        FROM accounts
        WHERE login = :login
        LIMIT 1
        """