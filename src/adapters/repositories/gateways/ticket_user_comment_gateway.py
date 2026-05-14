class TicketUserCommentGateway:
    SELECT = """
    SELECT
        user_comment_ticket_id AS comment_id,
        employee_id,
        comment,
        date_created
    FROM user_tickets_comment
    WHERE user_ticket_id = :ticket_id
    ORDER BY user_comment_ticket_id
    """

    INSERT = """
    INSERT INTO user_tickets_comment
    (
        user_ticket_id,
        employee_id,
        comment,
        date_created
    )
    VALUES
    (
        :ticket_id,
        :employee_id,
        :comment,
        :date_created
    )
    """

    DELETE_ALL = """
    DELETE FROM user_tickets_comment
    WHERE user_ticket_id = :ticket_id
    """

    