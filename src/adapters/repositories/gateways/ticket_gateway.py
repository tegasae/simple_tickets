class TicketGateway:

    FIELD="""t.ticket_id,
        t.client_id,
        t.admin_id,
        t.user_id,
        t.user_ticket_contact_user_id,
        t.user_ticket_id,
        t.text_of_ticket,
        t.date_created,
        t.is_remote,
        t.is_closed,
        t.date_closed,
        t.urgency_level,
        t.version"""
    SELECT_BASE = f"""
    SELECT
    {FIELD}    
    FROM tickets t
    """

    SELECT_BY_ID=SELECT_BASE+" WHERE t.ticket_id = :ticket_id"
    SELECT_BY_USER_TICKET_ID = SELECT_BASE + " WHERE t.user_ticket_id = :user_ticket_id"
    SELECT_ACTIVE_BY_CLIENT_ID_BATCH=SELECT_BASE + " WHERE t.client_id = :client_id AND t.ticket_id > :last_id ORDER BY t.ticket_id LIMIT :limit"
    SELECT_BY_CURRENT_EXECUTOR_ID_BATCH=SELECT_BASE+ """    JOIN (
        SELECT
            ticket_id,
            MAX(executor_assignment_id) AS last_executor_assignment_id
        FROM tickets_executor_assignment
        GROUP BY ticket_id
    ) AS last_assignment
        ON last_assignment.ticket_id = t.ticket_id
    JOIN tickets_executor_assignment AS current_assignment
        ON current_assignment.executor_assignment_id =
           last_assignment.last_executor_assignment_id
    WHERE current_assignment.admin_id = :executor_employee_id
      AND t.ticket_id > :last_ticket_id
    ORDER BY t.ticket_id
    LIMIT :limit
    """



    SELECT_BY_CLIENT_ID = "SELECT count(ticket_id) AS one FROM tickets WHERE client_id = :client_id"
    SELECT_BY_TICKET_USER_ID = "SELECT count(ticket_id) AS one FROM tickets WHERE user_ticket_id=:user_ticket_id"

    INSERT = """
    INSERT INTO tickets (
        client_id,
        admin_id,
        user_id,
        user_ticket_contact_user_id,
        user_ticket_id,
        text_of_ticket,
        date_created,
        is_remote,
        is_closed,
        date_closed,
        urgency_level,
        version
    )
    VALUES (
        :client_id,
        :admin_id,
        :user_id,
        :contact_user_id,
        :user_ticket_id,
        :text_of_ticket,
        :date_created,
        :is_remote,
        :is_closed,
        :date_closed,
        :urgency_level,
        :version
    )
    """

    UPDATE = """
    UPDATE tickets
    SET
        text_of_ticket = :text_of_ticket,
        is_remote = :is_remote,
        is_closed = :is_closed,
        date_closed = :date_closed,
        urgency_level = :urgency_level,
        version = version + 1
    WHERE ticket_id = :ticket_id
      AND version = :version
    """

    DELETE = """
    DELETE FROM tickets
    WHERE ticket_id = :ticket_id
    """




class TicketCommentGateway:
    SELECT = """
    SELECT comment_ticket_id, admin_id, comment, date_created
    FROM tickets_comment
    WHERE ticket_id = :ticket_id
    ORDER BY comment_ticket_id
    """

    INSERT = """
    INSERT INTO tickets_comment (
        ticket_id,
        admin_id,
        comment,
        date_created
    )
    VALUES (
        :ticket_id,
        :admin_id,
        :comment,
        :date_created
    )
    """


    DELETE_ALL = """
    DELETE FROM tickets_comment
    WHERE ticket_id = :ticket_id
    """


class TicketExecutorGateway:
    SELECT = """
    SELECT executor_assignment_id, admin_id, date_assignment
    FROM tickets_executor_assignment
    WHERE ticket_id = :ticket_id
    ORDER BY executor_assignment_id
    """

    INSERT = """
    INSERT INTO tickets_executor_assignment (
        ticket_id,
        admin_id,
        date_assignment
    )
    VALUES (
        :ticket_id,
        :admin_id,
        :date_assignment
    )
    """


    DELETE_ALL = """
    DELETE FROM tickets_executor_assignment
    WHERE ticket_id = :ticket_id
    """


class TicketStatusGateway:
    SELECT = """
    SELECT ticket_status_record_id, admin_id, status, date_created
    FROM tickets_status_record
    WHERE ticket_id = :ticket_id
    ORDER BY ticket_status_record_id
    """

    INSERT = """
    INSERT INTO tickets_status_record (
        ticket_id,
        admin_id,
        status,
        date_created
    )
    VALUES (
        :ticket_id,
        :admin_id,
        :status,
        :date_created
    )
    """

    COUNT1 = """
    SELECT COUNT(*) AS cnt
    FROM tickets_status_record
    WHERE ticket_id = :ticket_id
    """

    DELETE_ALL = """
    DELETE FROM tickets_status_record
    WHERE ticket_id = :ticket_id
    """