class TicketUserStatusGateway:

    SELECT = """
    SELECT
        user_ticket_status_record_id,
        employee_id,
        status,
        date_created
    FROM user_tickets_status_record
    WHERE user_ticket_id = :ticket_id
    ORDER BY user_ticket_status_record_id
    """

    INSERT = """
    INSERT INTO user_tickets_status_record
    (
        employee_id,
        user_ticket_id,
        status,
        date_created
    )
    VALUES
    (
        :employee_id,
        :ticket_id,
        :status,
        :date_created
    )
    """

    DELETE_ALL = """
    DELETE FROM user_tickets_status_record
    WHERE user_ticket_id = :ticket_id
    """


    