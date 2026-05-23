import sqlite3
from typing import Generator

from fastapi import Depends



from src.application.services.client_service import ClientApplicationService
from src.application.services.ticket_user_service import TicketUserApplicationService
from src.services.uow.uowsqlite import SQLiteUnitOfWork
from utils.db.connect import Connection

DB_URL = "../../db/admins.db"


def get_uow() -> Generator[SQLiteUnitOfWork, None, None]:
    conn = Connection.create_connection(
        url=DB_URL,
        engine=sqlite3,
    )

    try:
        yield SQLiteUnitOfWork(conn)
    finally:
        conn.close()


def get_client_service(
    uow = Depends(get_uow),
) -> ClientApplicationService:
    return ClientApplicationService(uow)


def get_ticket_user_service(
    uow = Depends(get_uow),
) -> TicketUserApplicationService:
    return TicketUserApplicationService(uow)