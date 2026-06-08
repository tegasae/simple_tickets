class TicketUserExecutorGateway:

    EXISTS_BY_ADMIN_ID = """
    SELECT 1 as one
    FROM user_tickets_executor_assignments
    WHERE admin_id = :admin_id
    LIMIT 1
    """