class RoleGateway:
    INSERT_ROLE = """
    INSERT INTO roles
        (name, permissions, description,
         is_system_role, date_created, is_admin, version)
    VALUES
        (:name, :permissions, :description,
         :is_system_role, :date_created, :is_admin, :version)
    """

    SELECT_BASE = """
    SELECT role_id, name, permissions, description,
           is_system_role, date_created, is_admin, version
    FROM roles
    WHERE is_admin = :is_admin
    """

    SELECT_BY_ID = """
    SELECT role_id, name, permissions, description,
           is_system_role, date_created, is_admin, version
    FROM roles
    WHERE is_admin = :is_admin
    AND role_id = :role_id
    """

    DELETE_ROLE = """
    DELETE FROM roles
    WHERE role_id = :role_id
    AND is_admin = :is_admin
    """

    EXIST = """
    SELECT CASE
        WHEN EXISTS (
            SELECT 1 FROM admins_roles WHERE role_id = :role_id
        ) OR EXISTS (
            SELECT 1 FROM users_roles WHERE role_id = :role_id
        ) THEN 1
        ELSE 0
    END AS one
    """