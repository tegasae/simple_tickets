class ClientGateway:
    """
    SQL queries for clients table
    """

    INSERT = """
    INSERT INTO clients
    (admin_id, name, address, email, phone, enabled, version, date_created)
    VALUES
    (:admin_id, :name, :address, :email, :phone, :enabled, :version, :date_created)
    """

    UPDATE = """
    UPDATE clients SET
        name = :name,
        address = :address,
        email = :email,
        phone = :phone,
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
        client_id,
        name,
        address,
        email,
        phone,
        admin_id,
        enabled,
        version,
        date_created
    FROM clients
    """

    SELECT_BY_ID = SELECT_BASE + " WHERE client_id = :client_id"

    EXISTS = """
    SELECT 1 AS one
    FROM clients
    WHERE client_id = :client_id
    LIMIT 1
    """