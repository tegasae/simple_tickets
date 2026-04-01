# src/examples/admin_service_example.py

import sqlite3
import time


from src.application.dto.user_dto import UserDTO

from src.application.services.user_service import UserApplicationService
from src.services.uow.uowsqlite import SQLiteUnitOfWork

from utils.db.connect import Connection


def main():

    # ---------------------------
    # Create DB connection
    # ---------------------------

    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    uow = SQLiteUnitOfWork(conn)


    user_service = UserApplicationService(uow=uow)



    try:
        user_dto=UserDTO(actor_admin_id=4,client_id=4,first_name="John",last_name="Smith",email="11@11.fgerg",phone="12345",login="login"+str(time.time()),password="Password1234567890@@@",roles=frozenset({6}))
        user_response_dto = user_service.create_user(user_dto=user_dto)
        print("Created user:", user_response_dto)

    except Exception as e:

        conn.rollback()
        raise e
        #print("ERROR:", e)

    finally:

        conn.close()


if __name__ == "__main__":
    main()