class TicketUserGateway:
    SELECT_BY_ID = """
    SELECT
        user_ticket_id AS ticket_id,
        client_id,
        user_id,
        user_ticket_contact_user_id AS contact_user_id,
        text_of_ticket AS description,
        date_created,
        version,
        date_closed,
        is_closed
    FROM user_tickets
    WHERE user_ticket_id = :ticket_id
    """

    SELECT_ALL = """
    SELECT user_ticket_id AS ticket_id,
    client_id,
        user_id,
        user_ticket_contact_user_id AS contact_user_id,
        text_of_ticket AS description,
        date_created,
        version,
        date_closed,
        is_closed
    FROM user_tickets
    """

    INSERT = """
    INSERT INTO user_tickets
    (
        client_id,
        user_id,
        user_ticket_contact_user_id,
        text_of_ticket,
        date_created,
        version,
        is_closed
    )
    VALUES
    (
        :client_id,
        :user_id,
        :contact_user_id,
        :description,
        :date_created,
        :version,
        :is_closed
    )
    """

    UPDATE = """
    UPDATE user_tickets
    SET
        version = :version + 1,
        is_closed = :is_closed,
        date_closed = :date_closed
    WHERE user_ticket_id = :ticket_id
    AND version = :version
    """

    DELETE = """
    DELETE FROM user_tickets
    WHERE user_ticket_id = :ticket_id
    """
    SELECT_BY_CLIENT_ID = """
    SELECT count(user_ticket_id) AS count
    FROM user_tickets
    WHERE client_id = :client_id
    """

