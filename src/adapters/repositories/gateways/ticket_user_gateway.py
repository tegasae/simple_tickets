# src/adapters/repositories/gateways/ticket_user_gateway.py


class TicketUserGateway:
    SELECT_BY_ID = """
    SELECT
        user_ticket_id AS ticket_id,
        client_id,
        user_id,
        user_ticket_contact_user_id AS contact_user_id,
        text_of_ticket,
        description,
        date_created,
        version,
        urgency_level
    FROM user_tickets
    WHERE user_ticket_id = :ticket_id
    """

    SELECT_ALL = """
    SELECT
        user_ticket_id AS ticket_id,
        client_id,
        user_id,
        user_ticket_contact_user_id AS contact_user_id,
        text_of_ticket,
        description,
        date_created,
        version,
        urgency_level
    FROM user_tickets
    ORDER BY user_ticket_id
    """

    INSERT = """
    INSERT INTO user_tickets (
        client_id,
        user_id,
        user_ticket_contact_user_id,
        text_of_ticket,
        description,
        date_created,
        version,
        is_closed,
        date_closed,
        urgency_level
    )
    VALUES (
        :client_id,
        :user_id,
        :contact_user_id,
        :text_of_ticket,
        :description,
        :date_created,
        :version,
        :is_closed,
        :date_closed,
        :urgency_level
    )
    """

    UPDATE = """
    UPDATE user_tickets
    SET
        user_ticket_contact_user_id = :contact_user_id,
        description = :description,
        urgency_level = :urgency_level,
        is_closed = :is_closed,
        date_closed = :date_closed,
        version = version + 1
    WHERE user_ticket_id = :ticket_id
      AND version = :version
    """

    DELETE = """
    DELETE FROM user_tickets
    WHERE user_ticket_id = :ticket_id
    """

    COUNT_BY_CLIENT_ID = """
    SELECT COUNT(*) AS cnt
    FROM user_tickets
    WHERE client_id = :client_id
    """

    EXISTS_BY_USER_ID = """
    SELECT 1 AS one
    FROM user_tickets
    WHERE user_id = :user_id
       OR user_ticket_contact_user_id = :user_id
    LIMIT 1
    """