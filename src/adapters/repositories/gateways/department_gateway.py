# src/adapters/repositories/gateways/department_gateway.py


class DepartmentGateway:
    """
    SQL queries for departments table.
    """

    INSERT = """
    INSERT INTO departments
    (name, enabled, version, date_created)
    VALUES
    (:name, :enabled, :version, :date_created)
    """

    UPDATE = """
    UPDATE departments SET
        name = :name,
        enabled = :enabled,
        version = version + 1
    WHERE department_id = :department_id
      AND version = :version
    """

    DELETE = """
    DELETE FROM departments
    WHERE department_id = :department_id
    """

    SELECT_BASE = """
    SELECT
        department_id,
        name,
        enabled,
        version,
        date_created
    FROM departments
    """

    SELECT_BY_ID = SELECT_BASE + """
    WHERE department_id = :department_id
    """

    EXISTS = """
    SELECT 1 AS one
    FROM departments
    WHERE department_id = :department_id
    LIMIT 1
    """