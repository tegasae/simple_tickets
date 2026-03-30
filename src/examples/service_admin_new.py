# src/examples/admin_service_example.py

import sqlite3
import time

from src.application.dto.admin_dto import AdminDTO
from src.application.services.admin_service import AdminApplicationService
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


    admin_service = AdminApplicationService(uow=uow)



    try:
        admin_dto=AdminDTO(actor_admin_id=1,first_name="John",last_name="Smith",email="11@11.fgerg",phone="12345",login="login"+str(time.time()),password="Password1234567890@@@",roles=frozenset({60,62}))
        admin_response_dto=admin_service.create_admin(admin_dto=admin_dto)
        print("Created admin:", admin_response_dto)
        admin_dto=AdminDTO(actor_admin_id=1,admin_id=admin_response_dto.admin_id,first_name="first name1")
        admin_response_dto=admin_service.update_admin(admin_dto=admin_dto)
        print("Update admin:", admin_response_dto)
        admin_response_dto=admin_service.disable(actor_admin_id=1, admin_id=admin_response_dto.admin_id)
        print("Disable admin:", admin_response_dto)
        admin_response_dto = admin_service.enable(actor_admin_id=1, admin_id=admin_response_dto.admin_id)
        print("Enable admin:", admin_response_dto)

        admin_dto = AdminDTO(actor_admin_id=1, first_name="John", last_name="Smith", email="11@11.fgerg", phone="12345",
                             roles=frozenset({60, 62}))
        admin_response_dto = admin_service.create_admin(admin_dto=admin_dto)
        print("Created admin:", admin_response_dto)


        admin_dto = AdminDTO(actor_admin_id=1, admin_id=admin_response_dto.admin_id,
                             login="login" + str(time.time()), password="Password1234567890@@@")
        login=admin_dto.login
        admin_response_dto=admin_service.attach_account(admin_dto=admin_dto)
        print("Attach account:", admin_response_dto)
        admin_response_dto = admin_service.detach_account(admin_dto=admin_dto)
        print("Detach account:", admin_response_dto)

        admin_dto = AdminDTO(actor_admin_id=1, first_name="John", last_name="Smith", email="11@11.fgerg", phone="12345",
                             login="login" + str(time.time()), password="Password1234567890@@@",
                             roles=frozenset({60, 62}))
        admin_response_dto = admin_service.create_admin(admin_dto=admin_dto)
        print("Created new admin:", admin_response_dto)
        admin_dto = AdminDTO(actor_admin_id=1, admin_id=admin_response_dto.admin_id,password="Password1234567890@@@@@@@@@@@@")
        result=admin_service.change_password(admin_dto=admin_dto)
        print("Change password:", result)

        admin_dto=AdminDTO(actor_admin_id=1,admin_id=admin_response_dto.admin_id,roles=frozenset({60}))
        admin_response_dto = admin_service.grant_role(admin_dto=admin_dto)
        print("Grant roles", admin_response_dto)

        admin_dto=AdminDTO(actor_admin_id=1,admin_id=admin_response_dto.admin_id,roles=frozenset({60}))
        admin_response_dto = admin_service.revoke_role(admin_dto=admin_dto)
        print("Revoke roles", admin_response_dto)

        admin_dto = AdminDTO(actor_admin_id=1, admin_id=admin_response_dto.admin_id, roles=frozenset({60}))
        admin_service.delete(admin_dto=admin_dto)

        admin_response_dto = admin_service.find_by_login(login='login1774364689.0212348')
        print("Found admin login:", admin_response_dto)
        admin_response_dto=admin_service.get_by_id(actor_admin_id=1,admin_id=71)
        print("Found admin:", admin_response_dto)

        list_admin_response_dto = admin_service.get_all(actor_admin_id=1)
        print("Found admins:", list_admin_response_dto)

    except Exception as e:

        conn.rollback()
        raise e
        #print("ERROR:", e)

    finally:

        conn.close()


if __name__ == "__main__":
    main()