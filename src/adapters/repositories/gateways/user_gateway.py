class UserGateway:
    INSERT = """
        INSERT INTO users (employee_id, client_id)
        VALUES (:employee_id, :client_id)
        """

    UPDATE = """
       UPDATE users
       SET client_id = :client_id
       WHERE employee_id = :employee_id
       """

    DELETE = """
        DELETE FROM users
        WHERE employee_id = :employee_id
        """

   # SELECT_BY_ID = """
   # SELECT
   #     e.employee_id,
   #     e.first_name,
   #     e.last_name,
   #     e.email,
   #     e.phone,
   #     e.date_created,
   #     e.enabled,
   #     e.version,
   #     u.client_id
   # FROM users u
   # JOIN employees e ON e.employee_id = u.employee_id
   # WHERE u.employee_id = :employee_id
   # """

    SELECT_BASE = (
        "SELECT "
        "e.employee_id, e.first_name, e.last_name, e.email, e.phone, e.date_created, "
        "e.enabled, e.version, "
        "u.client_id, "
        "acc.account_id, acc.login, acc.password, acc.enabled AS account_enabled, acc.date_created AS account_date_created "
        "FROM users u "
        "JOIN employees e ON e.employee_id = u.employee_id "
        "LEFT JOIN accounts acc ON acc.employee_id = e.employee_id "
        "WHERE e.is_admin = 0"
    )
    SELECT_BY_ID = SELECT_BASE + " AND e.employee_id = :employee_id"

    SELECT_BY_LOGIN = (
        "SELECT "
        "e.employee_id, e.first_name, e.last_name, e.email, e.phone, e.date_created, "
        "e.enabled, e.version, "
        "u.client_id, "
        "acc.account_id, acc.login, acc.password, acc.enabled AS account_enabled, acc.date_created AS account_date_created "
        "FROM accounts acc "
        "JOIN employees e ON e.employee_id = acc.employee_id "
        "JOIN users u ON a.employee_id = e.employee_id "
        "WHERE e.is_admin = 0 AND acc.login = :login"
    )


    EXISTS = """
    SELECT 1 AS one
    FROM users
    WHERE employee_id = :employee_id
    LIMIT 1
    """







    EXISTS_LOGIN = """
    SELECT 1 AS one
    FROM accounts
    WHERE login = :login
    LIMIT 1
    """