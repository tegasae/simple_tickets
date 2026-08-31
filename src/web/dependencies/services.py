import os
import sqlite3
from collections.abc import Generator

from fastapi import Depends

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.factory import ApplicationServiceFactory
from src.application.services.client_service import ClientApplicationService
from src.application.services.ticket_user_service import TicketUserApplicationService
from src.application.services.ticket_service import TicketApplicationService
from src.application.services.user_service import UserApplicationService
from src.application.services.admin_service import AdminApplicationService


from utils.db.connect import Connection


DB_URL = os.getenv("SIMPLE_TICKETS_DB", "../../db/admins.db")


def get_uow() -> Generator[SQLiteUnitOfWork, None, None]:
    conn = Connection.create_connection(
        url=DB_URL,
        engine=sqlite3,
        check_same_thread=False,
    )

    try:
        yield SQLiteUnitOfWork(conn)
    finally:
        conn.close()


def get_application_service_factory(
    uow=Depends(get_uow)
)->ApplicationServiceFactory:
    return ApplicationServiceFactory(uow)


def get_client_service(
    factory=Depends(get_application_service_factory),
) -> ClientApplicationService:
    return factory.client_service()


def get_ticket_user_service(
    factory=Depends(get_application_service_factory),
) -> TicketUserApplicationService:
    return factory.ticket_user_service()


def get_ticket_service(
    factory=Depends(get_application_service_factory),
) -> TicketApplicationService:
    return factory.ticket_service()


def get_user_service(
    factory=Depends(get_application_service_factory),
) -> UserApplicationService:
    return factory.user_service()


def get_admin_service(
    factory=Depends(get_application_service_factory),
) -> AdminApplicationService:
    return factory.admin_service()