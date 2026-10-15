import os
import sqlite3
from collections.abc import Generator

from fastapi import Depends, Request

from config import Settings
from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.factory import ApplicationServiceFactory
from src.application.services.ticket_user_service import TicketUserApplicationService


from utils.db.connect import Connection





def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_uow(settings: Settings = Depends(get_settings)) -> Generator[SQLiteUnitOfWork, None, None]:
    conn = Connection.create_connection(
        url=settings.DATABASE_URL,
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


def get_application_ticket_user_service(
    factory=Depends(get_application_service_factory),
) -> TicketUserApplicationService:
    return factory.ticket_user_service()







