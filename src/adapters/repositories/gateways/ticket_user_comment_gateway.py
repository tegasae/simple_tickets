class TicketUserCommentGateway:
    SELECT = """
    SELECT
    user_comment_ticket_id,
    employee_id,
    comment,
    date_created
    FROM user_tickets_comment
    WHERE user_ticket_id = :ticket_user_id
    ORDER BY user_comment_ticket_id
    """

    INSERT = """
    INSERT INTO user_tickets_comment (
        user_ticket_id,
        employee_id,
        comment,
        date_created
    )
    VALUES (
        :ticket_user_id,
        :employee_id,
        :comment,
        :date_created
    )
    """

    DELETE_ALL = """
    DELETE FROM user_tickets_comment
    WHERE ticket_user_id = :ticket_user_id
    """

    EXISTS_BY_EMPLOYEE_ID = """
    SELECT 1 AS one
    FROM user_tickets_comment
    WHERE employee_id = :employee_id
    LIMIT 1
    """