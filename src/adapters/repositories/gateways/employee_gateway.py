from __future__ import annotations


class EmployeeGateway:
    """
    employees table gateway

    Schema assumed:
      employees(employee_id PK AUTOINCREMENT, first_name, last_name, email, phone,
                date_created TEXT/INTEGER, enabled INTEGER, version INTEGER, is_admin INTEGER)
    """

    INSERT = (
        "INSERT INTO employees "
        "(first_name, last_name, email, phone, date_created, enabled, version, is_admin) "
        "VALUES "
        "(:first_name, :last_name, :email, :phone, :date_created, :enabled, :version, :is_admin)"
    )

    # Optimistic lock: WHERE version=:version, and bump version in DB
    UPDATE = (
        "UPDATE employees SET "
        "first_name = :first_name, "
        "last_name  = :last_name, "
        "email      = :email, "
        "phone      = :phone, "
        "enabled    = :enabled, "
        "version    = version + 1 "
        "WHERE employee_id = :employee_id "
        "  AND version = :version "
        "  AND is_admin = 1"
    )

    DELETE_ADMIN_EMPLOYEE = (
        "DELETE FROM employees "
        "WHERE employee_id = :employee_id "
        "  AND is_admin = 1"
    )

