import sqlite3
import time

from src.application.dto.ticket_dto import TicketUserDTO
from src.application.services.ticket_user_service import (
    TicketUserApplicationService,
)

from src.domain.exceptions import DomainOperationError
from src.services.uow.uowsqlite import SQLiteUnitOfWork
from utils.db.connect import Connection


def ticket_user_example() -> None:
    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    uow = SQLiteUnitOfWork(conn)

    service = TicketUserApplicationService(uow)

    try:
        # --------------------------------
        # Create a new user ticket
        # --------------------------------

        description = (
            "Printer problem " + time.strftime("%Y%m%d%H%M%S")
        )

        create_dto = TicketUserDTO(
            ticket_id=0,
            user_id=67,            # ticket owner
            contact_user_id=67,
            client_id=4,          # existing client
            description=description,
        )

        created_ticket = service.create_ticket(
            ticket_user_dto=create_dto,
        )

        print("\nCreated ticket:")
        print(created_ticket)

        # --------------------------------
        # Get by id
        # --------------------------------

        get_dto = TicketUserDTO(
            ticket_id=created_ticket.ticket_id,
            user_id=67,
            client_id=4,
        )

        loaded_ticket = service.get_by_ticket_id(
            ticket_user_dto=get_dto,
        )

        print("\nLoaded ticket:")
        print(loaded_ticket)

        # --------------------------------
        # Cancel ticket
        # --------------------------------

        cancel_dto = TicketUserDTO(
            ticket_id=created_ticket.ticket_id,
            user_id=67,
            client_id=4,
            comment="Problem solved by restarting printer",
        )

        cancelled_ticket = service.cancel(
            ticket_user_dto=cancel_dto,
        )

        print("\nCancelled ticket:")
        print(cancelled_ticket)

    except DomainOperationError as exc:
        print(f"\nDomain error: {exc}")
        raise
    except Exception as exc:
        print(f"\nUnexpected error: {exc}")
        raise

if __name__ == "__main__":
    ticket_user_example()