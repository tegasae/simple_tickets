class ClientGateway:
    """
    SQL queries for clients table
    """

    INSERT = """
    INSERT INTO clients
    (admin_id, name, address, email, phone, description, enabled, version, date_created)
    VALUES
    (:admin_id, :name, :address, :email, :phone, :description, :enabled, :version, :date_created)
    """

    UPDATE = """
    UPDATE clients SET
        name = :name,
        address = :address,
        email = :email,
        phone = :phone,
        description=:description,
        enabled = :enabled,
        version = version + 1
    WHERE client_id = :client_id
      AND version = :version
    """

    DELETE = """
    DELETE FROM clients
    WHERE client_id = :client_id
    """

    SELECT_BASE = """
    SELECT
        clients.client_id,
        clients.name,
        clients.address,
        clients.email,
        clients.phone,
        clients.description,
        clients.admin_id,
        clients.enabled,
        clients.version,
        clients.date_created
    FROM clients
    """

    SELECT_BY_ID = SELECT_BASE + " WHERE client_id = :client_id"
    SELECT_BY_USER_ID = SELECT_BASE + " LEFT JOIN users u ON clients.client_id = u.client_id WHERE u.employee_id = :employee_id"
    EXISTS = """
    SELECT 1 AS one
    FROM clients
    WHERE client_id = :client_id
    LIMIT 1
    """

    SELECT_BY_ADMIN = "SELECT count(client_id) FROM clients WHERE admin_id = :admin_id"

    TOUCH = """
        UPDATE clients
        SET version = version + 1
        WHERE client_id = :client_id
          AND version = :version
    """

