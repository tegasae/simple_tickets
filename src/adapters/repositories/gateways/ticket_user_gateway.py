# src/adapters/repositories/gateways/ticket_user_gateway.py

class TicketUserGateway:
    BASE_SELECT="""
    SELECT
        user_ticket_id,
        client_id,
        user_id,
        contact_user_id,
        text_of_ticket,
        description,
        date_created,
        version,
    FROM user_tickets 
    """


    SELECT_BY_ID = BASE_SELECT + """
    WHERE user_ticket_id = :user_ticket_id
    """

    SELECT_BY_USER_ID = BASE_SELECT + """
        WHERE user_id = :user_id
        """
    SELECT_BY_CLIENT_ID=BASE_SELECT+ """
    WHERE client_id = :client_id"""

    SELECT_BY_OPEN_USER_ID=BASE_SELECT +   """ 
    WHERE user_id=:user_id AND date_finished is NULL"""

    SELECT_BY_OPEN_CLIENT_ID = BASE_SELECT + """ 
        WHERE client_id=:client_id AND date_finished is NULL"""

    SELECT_BY_FINISHED_USER_ID=BASE_SELECT + """
    WHERE user_id=:user_id AND date_finished is not NULL"""
    SELECT_BY_FINISHED_CLIENT_ID = BASE_SELECT + """
    WHERE user_id=:user_id AND date_finished is NULL"""




    SELECT_ALL = BASE_SELECT + """
    
    ORDER BY user_ticket_id
    """

    INSERT = """
    INSERT INTO user_tickets (
        client_id,
        user_id,
        contact_user_id,
        text_of_ticket,
        description,
        date_created,
        version,
        is_closed,
        date_finished
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
        :date_finished,
        
    )
    """

    UPDATE = """
    UPDATE user_tickets
    SET
        contact_user_id = :contact_user_id,
        description = :description,
        date_finished = :date_finished,
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
       OR contact_user_id = :user_id
    LIMIT 1
    """


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


class TicketUserStatusGateway:
    SELECT = """
    SELECT
        user_ticket_status_record_id,
        actor_employee_id,
        status,
        comment,
        date_created
    FROM user_tickets_status_record
    WHERE user_ticket_id = :user_ticket_id
    ORDER BY user_ticket_status_record_id
    """

    INSERT = """
    INSERT INTO user_tickets_status_record (
        actor_employee_id,
        user_ticket_id,
        status,
        comment,
        date_created
    )
    VALUES (
        :actor_employee_id,
        :user_ticket_id,
        :status,
        :comment,
        :date_created
    )
    """

    DELETE_ALL = """
    DELETE FROM user_tickets_status_record
    WHERE user_ticket_id = :user_ticket_id
    """

    EXISTS_BY_EMPLOYEE_ID = """
    SELECT 1 AS one
    FROM user_tickets_status_record
    WHERE actor_employee_id = :actor_employee_id
    LIMIT 1
    """
