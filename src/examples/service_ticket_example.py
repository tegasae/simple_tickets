import sqlite3
import time

from src.application.dto.ticket_dto import TicketDTO
from src.application.services.ticket_service import TicketApplicationService

from src.domain.exceptions import DomainOperationError
from src.services.uow.uowsqlite import SQLiteUnitOfWork
from utils.db.connect import Connection


def ticket_example() -> None:
    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    uow = SQLiteUnitOfWork(conn)
    service = TicketApplicationService(uow)

    try:
        # --------------------------------
        # Create a new ticket
        # --------------------------------
        create_dto = TicketDTO(
            ticket_id=0,
            actor_admin_id=4,  # existing admin
            client_id=4,       # existing client
            description=f"Printer issue {time.strftime('%Y%m%d%H%M%S')}",
            urgency_level=2,
        )

        created_ticket = service.create_ticket(
            ticket_dto=create_dto,
        )

        print("Created ticket:")
        print(created_ticket)

        # --------------------------------
        # Move ticket to AT_WORK
        # --------------------------------
        at_work_dto = TicketDTO(
            ticket_id=created_ticket.ticket_id,
            actor_admin_id=4,
            client_id=created_ticket.client_id,
            executor_id=4,
        )

        at_work_ticket = service.at_work(
            ticket_dto=at_work_dto,
        )

        print("\nTicket AT_WORK:")
        print(at_work_ticket)

        # --------------------------------
        # Execute the ticket
        # --------------------------------
        execute_dto = TicketDTO(
            ticket_id=created_ticket.ticket_id,
            actor_admin_id=4,
            admin_id=4,
            client_id=created_ticket.client_id,
            comment="Printer has been repaired successfully",
        )

        executed_ticket = service.execute(
            ticket_dto=execute_dto,
        )

        print("\nExecuted ticket:")
        print(executed_ticket)

        # --------------------------------
        # Load ticket by id
        # --------------------------------
        get_dto = TicketDTO(
            ticket_id=created_ticket.ticket_id,
            actor_admin_id=4,
            client_id=created_ticket.client_id,
        )

        loaded_ticket = service.get_by_id(
            ticket_dto=get_dto,
        )

        print("\nLoaded ticket:")
        print(loaded_ticket)

        # --------------------------------
        # Create and cancel another ticket
        # --------------------------------
        cancel_create_dto = TicketDTO(
            ticket_id=0,
            actor_admin_id=4,
            client_id=4,
            description="Temporary test ticket",
        )

        cancel_ticket = service.create_ticket(
            ticket_dto=cancel_create_dto,
        )

        cancel_dto = TicketDTO(
            ticket_id=cancel_ticket.ticket_id,
            actor_admin_id=4,
            client_id=cancel_ticket.client_id,
            comment="Issue is no longer актуальна",
        )

        cancelled_ticket = service.cancel(
            ticket_dto=cancel_dto,
        )

        print("\nCancelled ticket:")
        print(cancelled_ticket)

    except DomainOperationError as exc:
        print(f"Domain error: {exc}")
        raise
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        raise


if __name__ == "__main__":
    ticket_example()