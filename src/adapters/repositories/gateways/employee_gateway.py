class EmployeeGateway:
    # Insert: employee_id is autoincrement
    INSERT = """
    INSERT INTO employees
        (first_name, last_name, email, phone, date_created, enabled, version, is_admin)
    VALUES
        (:first_name, :last_name, :email, :phone, :date_created, :enabled, :version, :is_admin)
    """

    # Optimistic lock: match version; increment version in DB
    UPDATE = """
    UPDATE employees SET
        first_name = :first_name,
        last_name  = :last_name,
        email      = :email,
        phone      = :phone,
        enabled    = :enabled,
        date_created = :date_created,
        version    = version + 1
    WHERE employee_id = :employee_id
      AND version     = :version
      AND is_admin    = :is_admin
    """

    DELETE = """
    DELETE FROM employees
    WHERE employee_id = :employee_id
    """

    DELETE_ADMIN_EMPLOYEE = (
        "DELETE FROM employees "
        "WHERE employee_id = :employee_id "
        "  AND is_admin = 1"
    )
