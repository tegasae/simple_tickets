import sqlite3

from src.adapters.repositories.ticket_repository import TicketRepositorySQLite
from src.domain.services.ticket import TicketService
from utils.db.connect import Connection


def main():

    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    ticket_repo = TicketRepositorySQLite(conn)

    ticket_service = TicketService(ticket_repository=ticket_repo)

    conn.begin_transaction()

    try:

        # ---------------------------
        # 1️⃣ Create ticket
        # ---------------------------

        ticket = ticket_service.create_ticket(
            client_id=1,
            admin_id=1,
            description="Network problem",
            text_of_ticket="Internet does not work",
            urgency_level=1,
        )

        print("Ticket created:", ticket)

        # ---------------------------
        # 2️⃣ Assign executor
        # ---------------------------

        ticket = ticket_service.assign_executor(
            ticket_id=ticket.ticket_id,
            admin_id=2,
        )

        print("Executor assigned:", ticket.executors)

        # ---------------------------
        # 3️⃣ Add comment
        # ---------------------------

        ticket = ticket_service.add_comment(
            ticket_id=ticket.ticket_id,
            employee_id=2,
            comment="Investigating the issue",
        )

        print("Comment added:", ticket.comments)

        # ---------------------------
        # 4️⃣ Start work
        # ---------------------------

        ticket = ticket_service.start_work(
            ticket_id=ticket.ticket_id,
            actor_employee_id=2,
        )

        print("Ticket started:", ticket.current_status())

        # ---------------------------
        # 5️⃣ Execute ticket
        # ---------------------------

        ticket = ticket_service.execute(
            ticket_id=ticket.ticket_id,
            actor_employee_id=2,
        )

        print("Ticket executed:", ticket.current_status())

        # ---------------------------
        # 6️⃣ Get ticket
        # ---------------------------

        ticket_loaded = ticket_service.get_by_id(ticket.ticket_id)

        print("Loaded ticket:", ticket_loaded)

        # ---------------------------
        # 7️⃣ List all tickets
        # ---------------------------

        tickets = ticket_service.get_all()

        print("All tickets:", tickets)

        conn.commit()

    except Exception as e:

        conn.rollback()

        print("ERROR:", e)
        raise e

    finally:

        conn.close()


if __name__ == "__main__":
    main()