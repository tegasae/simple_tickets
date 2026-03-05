class UserRoleGateway:

    SELECT = """
    SELECT role_id
    FROM users_roles
    WHERE employee_id = :employee_id
    """

    INSERT = """
    INSERT INTO users_roles (employee_id, role_id)
    VALUES (:employee_id, :role_id)
    """

    DELETE_ALL = """
    DELETE FROM users_roles
    WHERE employee_id = :employee_id
    """