class TicketGateway:


    SELECT_BASE = """
    SELECT
        ticket_id,
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
    FROM tickets
    """

    SELECT_BY_ID=SELECT_BASE+" WHERE ticket_id = :ticket_id"

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

    COUNT = """
    SELECT COUNT(*) AS cnt
    FROM tickets_comment
    WHERE ticket_id = :ticket_id
    """

    DELETE_ALL = """
    DELETE FROM tickets_comment
    WHERE ticket_id = :ticket_id
    """


class TicketExecutorGateway:
    SELECT = """
    SELECT admin_id, date_assignment
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

    COUNT = """
    SELECT COUNT(*) AS cnt
    FROM tickets_executor_assignment
    WHERE ticket_id = :ticket_id
    """

    DELETE_ALL = """
    DELETE FROM tickets_executor_assignment
    WHERE ticket_id = :ticket_id
    """


class TicketStatusGateway:
    SELECT = """
    SELECT admin_id, status, date_created
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

    COUNT = """
    SELECT COUNT(*) AS cnt
    FROM tickets_status_record
    WHERE ticket_id = :ticket_id
    """

    DELETE_ALL = """
    DELETE FROM tickets_status_record
    WHERE ticket_id = :ticket_id
    """