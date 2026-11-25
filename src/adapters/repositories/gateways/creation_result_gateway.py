class CreationResultGateway:
    _KEY_FILTER = "employee_id = :employee_id AND idempotency_key = :key"

    SELECT_BY_KEY = f"""
        SELECT fingerprint, status_code, body, expires_at
        FROM creation_results WHERE {_KEY_FILTER}
    """

    INSERT_RESERVATION = """
        INSERT INTO creation_results (employee_id, idempotency_key, fingerprint)
        VALUES (:employee_id, :key, :fingerprint)
    """

    COMPLETE = f"""
        UPDATE creation_results SET status_code = :status_code, body = :body
        WHERE {_KEY_FILTER} AND status_code IS NULL
    """

    DELETE_EXPIRED_BY_KEY = f"""
        DELETE FROM creation_results WHERE {_KEY_FILTER} AND expires_at <= :now
    """

    SELECT_PENDING_DEADLINES = """
        SELECT employee_id, idempotency_key
        FROM creation_results WHERE expires_at IS NULL AND status_code IS NOT NULL
    """

    SET_DEADLINE = f"""
        UPDATE creation_results SET expires_at = :expires_at
        WHERE {_KEY_FILTER} AND expires_at IS NULL AND status_code IS NOT NULL
    """

    DELETE_EXPIRED = """
        DELETE FROM creation_results WHERE expires_at <= :now
    """
