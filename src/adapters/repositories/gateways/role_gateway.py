class RoleGateway:
    # ---------- admin roles ----------
    SELECT_ADMIN_ROLES = """
    SELECT role_id
    FROM admins_roles
    WHERE employee_id = :employee_id
    """

    DELETE_ALL_ADMIN_ROLES = """
    DELETE FROM admins_roles
    WHERE employee_id = :employee_id
    """

    INSERT_ADMIN_ROLE = """
    INSERT INTO admins_roles (employee_id, role_id)
    VALUES (:employee_id, :role_id)
    """

    # ---------- user roles ----------
    SELECT_USER_ROLES = """
    SELECT role_id
    FROM users_roles
    WHERE employee_id = :employee_id
    """

    DELETE_ALL_USER_ROLES = """
    DELETE FROM users_roles
    WHERE employee_id = :employee_id
    """

    INSERT_USER_ROLE = """
    INSERT INTO users_roles (employee_id, role_id)
    VALUES (:employee_id, :role_id)
    """

    SELECT_ADMIN_ROLE_IDS = (
        "SELECT role_id "
        "FROM admins_roles "
        "WHERE employee_id = :employee_id"
    )

    DELETE_ALL_FOR_ADMIN = (
        "DELETE FROM admins_roles "
        "WHERE employee_id = :employee_id"
    )


    DELETE_ONE = (
        "DELETE FROM admins_roles "
        "WHERE employee_id = :employee_id AND role_id = :role_id"
    )

    EXISTS_ONE = (
        "SELECT 1 AS one FROM admins_roles "
        "WHERE employee_id = :employee_id AND role_id = :role_id LIMIT 1"
    )
