class UserGateway:

    SELECT_BY_ID = """
    SELECT
        e.employee_id,
        e.first_name,
        e.last_name,
        e.email,
        e.phone,
        e.date_created,
        e.enabled,
        e.version,
        u.client_id
    FROM users u
    JOIN employees e ON e.employee_id = u.employee_id
    WHERE u.employee_id = :employee_id
    """

    SELECT_ALL = """
    SELECT
        e.employee_id,
        e.first_name,
        e.last_name,
        e.email,
        e.phone,
        e.date_created,
        e.enabled,
        e.version,
        u.client_id
    FROM users u
    JOIN employees e ON e.employee_id = u.employee_id
    """

    EXISTS = """
    SELECT 1 AS one
    FROM users
    WHERE employee_id = :employee_id
    LIMIT 1
    """

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

    SELECT_BY_LOGIN = """
    SELECT
        e.employee_id,
        e.first_name,
        e.last_name,
        e.email,
        e.phone,
        e.date_created,
        e.enabled,
        e.version,
        u.client_id
    FROM accounts a
    JOIN employees e ON e.employee_id = a.employee_id
    JOIN users u ON u.employee_id = e.employee_id
    WHERE a.login = :login
    LIMIT 1
    """