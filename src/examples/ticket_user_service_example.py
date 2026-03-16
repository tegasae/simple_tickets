import sqlite3

from src.adapters.repositories.ticket_user_repository import TicketUserRepositorySQLite
from src.domain.services.ticket_user import TicketUserService

from src.domain.ticket_user import StatusTicketOfClient
from utils.db.connect import Connection



def main():

    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    repo = TicketUserRepositorySQLite(conn)

    service = TicketUserService(repo)

    conn.begin_transaction()

    try:

        ticket = service.create_ticket(
            client_id=1,
            user_id=10,
            contact_user_id=0,
            description="Printer does not work",
        )

        print("Created:", ticket)

        ticket = service.change_status(
            ticket_id=ticket.ticket_id,
            new_status=StatusTicketOfClient.CONFIRMED,
            actor_employee_id=10,
        )

        print("Confirmed:", ticket)

        ticket = service.add_comment(
            ticket_id=ticket.ticket_id,
            employee_id=10,
            comment="Please fix ASAP",
        )

        print("Comment added:", ticket)

        ticket = service.change_status(
            ticket_id=ticket.ticket_id,
            new_status=StatusTicketOfClient.AT_WORK,
            actor_employee_id=1,
        )

        ticket = service.change_status(
            ticket_id=ticket.ticket_id,
            new_status=StatusTicketOfClient.EXECUTED,
            actor_employee_id=1,
        )

        print("Executed:", ticket)

        conn.commit()

    except Exception as e:

        conn.rollback()

        print("ERROR:", e)
        raise e

    finally:

        conn.close()


if __name__ == "__main__":
    main()

