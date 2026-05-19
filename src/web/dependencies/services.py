import os
import sqlite3

from fastapi import Depends

from src.application.services.client_service import ClientApplicationService
from src.application.services.ticket_user_service import TicketUserApplicationService
from src.services.uow.uowsqlite import SQLiteUnitOfWork
from utils.db.connect import Connection

DB_URL = os.getenv("SIMPLE_TICKETS_DB", "../../db/admins.db")


def get_uow():
    conn = Connection.create_connection(
        url=DB_URL,
        engine=sqlite3,
        check_same_thread=False,
    )
    try:
        yield SQLiteUnitOfWork(conn)
    finally:
        conn.close()


def get_client_service(uow = Depends(get_uow)):
    return ClientApplicationService(uow)


def get_ticket_user_service(uow = Depends(get_uow)):
    return TicketUserApplicationService(uow)
