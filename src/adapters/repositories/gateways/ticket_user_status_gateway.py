# src/adapters/repositories/gateways/ticket_user_status_gateway.py


class TicketUserStatusGateway:
    SELECT = """
    SELECT
        user_ticket_status_record_id AS status_id,
        employee_id AS actor_employee_id,
        status,
        comment,
        date_created
    FROM user_tickets_status_record
    WHERE user_ticket_id = :ticket_id
    ORDER BY user_ticket_status_record_id
    """

    INSERT = """
    INSERT INTO user_tickets_status_record (
        employee_id,
        user_ticket_id,
        status,
        comment,
        date_created
    )
    VALUES (
        :actor_employee_id,
        :ticket_id,
        :status,
        :comment,
        :date_created
    )
    """

    DELETE_ALL = """
    DELETE FROM user_tickets_status_record
    WHERE user_ticket_id = :ticket_id
    """

    EXISTS_BY_EMPLOYEE_ID = """
    SELECT 1 AS one
    FROM user_tickets_status_record
    WHERE employee_id = :employee_id
    LIMIT 1
    """