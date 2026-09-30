# src/adapters/repositories/gateways/ticket_gateway.py


class TicketGateway:

    SELECT_BASE = """
    SELECT
        ticket_id,
        client_id,
        text_of_ticket,
        user_id,
        contact_user_id,
        user_ticket_id,
        date_created,
        planned_at,
        department_id,
        remote_work_recommended,
        urgency_level,
        description,
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

    SELECT_BY_CLIENT_ID = SELECT_BASE + """
        WHERE client_id=:client_id
        """

    SELECT_BY_USER_ID = SELECT_BASE + """
            WHERE user_id=:user_id
            """

    SELECT_BY_CONTACT_USER_ID = SELECT_BASE + """
                WHERE contact_user_id=:contact_user_id
                """

    SELECT_BY_DEPARTMENT_ID = SELECT_BASE + """
                WHERE department_id=:department_id
                """

    SELECT_BY_EXECUTOR_ID = SELECT_BASE + """
    WHERE current_executor_id=:current_executor_id
    """



    SELECT_BY_OPEN = SELECT_BASE + """
                WHERE date_finished is NULL
            """

    SELECT_BY_FINISHED = SELECT_BASE + """
        WHERE date_finished is NOT  NULL
    """




    SELECT_BY_CLIENT_ID_BATCH ="""
    SELECT
        t.ticket_id,
        t.client_id,
        t.text_of_ticket,
        t.user_id,
        t.contact_user_id,
        t.user_ticket_id,
        t.date_created,
        t.planned_at,
        t.department_id,
        t.remote_work_recommended,
        t.description,
        t.urgency_level,
        t.user_ticket_id,
        t.description,
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
        t.text_of_ticket,
        t.user_id,
        t.contact_user_id,
        t.user_ticket_id,
        t.date_created,
        t.planned_at,
        t.department_id,
        t.remote_work_recommended,
        t.description,
        t.urgency_level,
        t.user_ticket_id,
        t.description,
        t.version
    FROM tickets AS t
    WHERE t.ticket_id > :last_id
    ORDER BY t.ticket_id
    LIMIT :limit
"""


    INSERT = """
    INSERT INTO tickets (
        client_id,
        user_id,
        contact_user_id,
        user_ticket_id,
        department_id,
        text_of_ticket,
        description,
        date_created,
        remote_work_recommended,
        planned_at, 
        urgency_level,
        version,
        current_executor_id,
        date_finished       
    )
    VALUES (
        :client_id,
        :user_id,
        :contact_user_id,
        :user_ticket_id,
        :department_id,
        :text_of_ticket,
        :description,
        :date_created,
        :remote_work_recommended,
        :planned_at,
        :urgency_level,
        :version,
        :current_executor_id,
        :date_finished
    )
    """





    UPDATE = """
    UPDATE tickets
    SET
    contact_user_id = :contact_user_id,
    department_id = :department_id,
    description = :description,
    work_is_remote = :work_is_remote,
    planned_at = :planned_at,
    urgency_level = :urgency_level,
    current_executor_id = :current_executor_id,
    date_finished = :date_finished
    version = version + 1
    WHERE ticket_id = :ticket_id
    AND version = :version
    """

    DELETE = """
    DELETE FROM tickets
    WHERE ticket_id = :ticket_id
    """

    #
    COUNT_BY_CLIENT_ID = """
    SELECT COUNT(*) AS cnt
    FROM tickets
    WHERE client_id = :client_id
    """
    #
    COUNT_BY_USER_TICKET_ID = """
    SELECT COUNT(*) AS cnt
    FROM tickets
    WHERE user_ticket_id = :user_ticket_id
    """

    #
    EXISTS_BY_ADMIN_ID = """
    SELECT 1 AS one
    FROM tickets
    WHERE admin_id = :admin_id
    LIMIT 1
    """

    EXISTS_BY_EXECUTOR_ID = """
    SELECT 1 AS one
    FROM tickets
    WHERE current_executor_id = :current_executor_id
    LIMIT 1
    """

    EXISTS_BY_DEPARTMENT_ID = """
    SELECT 1 AS one
    FROM tickets
    WHERE department_id = :department_id
    LIMIT 1
    """

    TOUCH = """
        UPDATE tickets
        SET version = version + 1
        WHERE ticket_id = :ticket_id
          AND version = :version
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
        status,
        actor_employee_id,
        work_is_remote,
        date_created,
        executor_id,
        actual_started_at,
        actual_finished_at,
        duration,
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
        actual_started_at,
        actual_finished_at,
        work_is_remote,
        duration,
        comment
    )
    VALUES (
        :ticket_id,
        :actor_employee_id,
        :status,
        :date_created,
        :executor_id,
        :actual_started_at,
        :actual_finished_at,
        :work_is_remote,
        :duration,
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