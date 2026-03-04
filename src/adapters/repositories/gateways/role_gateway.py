from __future__ import annotations


class RoleGateway:
    """
    Admin roles link table gateway.
    Schema assumed:
      admins_roles(employee_id, role_id) PK(employee_id, role_id)
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

    INSERT_ADMIN_ROLE = (
        "INSERT INTO admins_roles (employee_id, role_id) "
        "VALUES (:employee_id, :role_id)"
    )

    DELETE_ONE = (
        "DELETE FROM admins_roles "
        "WHERE employee_id = :employee_id AND role_id = :role_id"
    )

    EXISTS_ONE = (
        "SELECT 1 AS one FROM admins_roles "
        "WHERE employee_id = :employee_id AND role_id = :role_id LIMIT 1"
    )


