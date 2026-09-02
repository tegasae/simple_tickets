# src/adapters/repositories/gateways/ticket_gateway.py


class TicketGateway:
    SELECT_BASE = """
    SELECT
        ticket_id,
        client_id,
        admin_id,
        user_id,
        contact_user_id,
        user_ticket_id,
        department_id,
        text_of_ticket,
        description,
        date_created,
        is_remote,
        urgency_level,
        version
    FROM tickets
    """

    SELECT_BY_ID = SELECT_BASE + """
    WHERE ticket_id = :ticket_id
    """

    SELECT_ALL = SELECT_BASE + """
    ORDER BY ticket_id
    """

    SELECT_BY_USER_TICKET_ID = SELECT_BASE + """
    WHERE user_ticket_id = :user_ticket_id
    """

    SELECT_BY_CLIENT_ID_BATCH ="""
    SELECT
        t.ticket_id,
        t.client_id,
        t.admin_id,
        t.user_id,
        t.contact_user_id,
        t.user_ticket_id,
        t.department_id,
        t.text_of_ticket,
        t.description,
        t.date_created,
        t.is_remote,
        t.urgency_level,
        t.version
    FROM tickets AS t
    WHERE t.client_id = :client_id
      AND t.ticket_id > :last_id
    ORDER BY t.ticket_id
    LIMIT :limit
"""


    SELECT_ALL_BATCH = """
    SELECT
        t.ticket_id,
        t.client_id,
        t.admin_id,
        t.user_id,
        t.contact_user_id,
        t.user_ticket_id,
        t.department_id,
        t.text_of_ticket,
        t.description,
        t.date_created,
        t.is_remote,
        t.urgency_level,
        t.version
    FROM tickets AS t
    WHERE t.ticket_id > :last_id
    ORDER BY t.ticket_id
    LIMIT :limit
"""


    INSERT = """
    INSERT INTO tickets (
        client_id,
        admin_id,
        user_id,
        contact_user_id,
        user_ticket_id,
        department_id,
        text_of_ticket,
        description,
        date_created,
        is_remote,
        urgency_level,
        version
    )
    VALUES (
        :client_id,
        :admin_id,
        :user_id,
        :contact_user_id,
        :user_ticket_id,
        :department_id,
        :text_of_ticket,
        :description,
        :date_created,
        :is_remote,
        :urgency_level,
        :version
    )
    """

    UPDATE = """
    UPDATE tickets
    SET
    contact_user_id = :contact_user_id,
    department_id = :department_id,
    text_of_ticket = :text_of_ticket,
    description = :description,
    is_remote = :is_remote,
    urgency_level = :urgency_level,
    version = version + 1
WHERE ticket_id = :ticket_id
  AND version = :version
    """

    DELETE = """
    DELETE FROM tickets
    WHERE ticket_id = :ticket_id
    """

    COUNT_BY_CLIENT_ID = """
    SELECT COUNT(*) AS cnt
    FROM tickets
    WHERE client_id = :client_id
    """

    COUNT_BY_USER_TICKET_ID = """
    SELECT COUNT(*) AS cnt
    FROM tickets
    WHERE user_ticket_id = :user_ticket_id
    """

    EXISTS_BY_ADMIN_ID = """
    SELECT 1 AS one
    FROM tickets
    WHERE admin_id = :admin_id
    LIMIT 1
    """

    EXISTS_BY_DEPARTMENT_ID = """
    SELECT 1 AS one
    FROM tickets
    WHERE department_id = :department_id
    LIMIT 1
    """


class TicketCommentGateway:
    SELECT_BY_TICKET_ID = """
    SELECT
        ticket_comment_id,
        employee_id,
        comment,
        date_created
    FROM ticket_comments
    WHERE ticket_id = :ticket_id
    ORDER BY ticket_comment_id
    """

    INSERT = """
    INSERT INTO ticket_comments (
        ticket_id,
        employee_id,
        comment,
        date_created
    )
    VALUES (
        :ticket_id,
        :employee_id,
        :comment,
        :date_created
    )
    """

    EXISTS_BY_EMPLOYEE_ID = """
    SELECT 1 AS one
    FROM ticket_comments
    WHERE employee_id = :employee_id
    LIMIT 1
    """


class TicketStatusGateway:
    SELECT_BY_TICKET_ID = """
    SELECT
        status_id,
        actor_employee_id,
        status,
        date_created,
        executor_id,
        planned_start_at,
        planned_finish_at,
        actual_started_at,
        actual_finished_at,
        comment
    FROM ticket_status_records
    WHERE ticket_id = :ticket_id
    ORDER BY status_id
    """

    INSERT = """
    INSERT INTO ticket_status_records (
        ticket_id,
        actor_employee_id,
        status,
        date_created,
        executor_id,
        planned_start_at,
        planned_finish_at,
        actual_started_at,
        actual_finished_at,
        comment
    )
    VALUES (
        :ticket_id,
        :actor_employee_id,
        :status,
        :date_created,
        :executor_id,
        :planned_start_at,
        :planned_finish_at,
        :actual_started_at,
        :actual_finished_at,
        :comment
    )
    """

    COUNT_BY_TICKET_ID = """
    SELECT COUNT(*) AS cnt
    FROM ticket_status_records
    WHERE ticket_id = :ticket_id
    """

    EXISTS_BY_EMPLOYEE_ID = """
    SELECT 1 AS one
    FROM ticket_status_records
    WHERE actor_employee_id = :employee_id
       OR executor_id = :employee_id
    LIMIT 1
    """