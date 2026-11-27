class RefreshSessionGateway:
    """SQL statements for refresh sessions in the main SQLite database."""

    SELECT_BY_HASH = """
        SELECT account_id, subject_id, subject_type, username,
               created_at, expires_at, scope
        FROM auth_refresh_sessions
        WHERE token_hash = :token_hash
    """

    INSERT = """
        INSERT INTO auth_refresh_sessions
            (token_hash, account_id, subject_id, subject_type, username,
             created_at, expires_at, scope)
        VALUES (:token_hash, :account_id, :subject_id, :subject_type, :username,
                :created_at, :expires_at, :scope)
    """

    DELETE_BY_HASH = """
        DELETE FROM auth_refresh_sessions WHERE token_hash = :token_hash
    """

    DELETE_BY_SUBJECT = """
        DELETE FROM auth_refresh_sessions
        WHERE subject_type = :subject_type AND subject_id = :subject_id
    """

    DELETE_EXPIRED = """
        DELETE FROM auth_refresh_sessions WHERE expires_at <= :now
    """
