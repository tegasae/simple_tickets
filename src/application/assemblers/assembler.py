# src/application/assemblers/client_assembler.py
from src.application.dto.admin_dto import AdminResponseDTO
from src.domain.client import Client
from src.domain.employee import Admin
from src.domain.value_objects import Empty
from src.application.dto.client_dto import ClientResponseDTO


class ClientAssembler:

    @staticmethod
    def to_dto(client: Client) -> ClientResponseDTO:

        def unwrap(value):
            return None if isinstance(value, Empty) else str(value)

        return ClientResponseDTO(
            client_id=client.client_id,
            name=str(client.name),
            email=unwrap(client.email),
            address=unwrap(client.address),
            phone=unwrap(client.phone),
            enabled=client.enabled,
        )

class AdminAssembler:
    @staticmethod
    def to_dto(admin: Admin) -> AdminResponseDTO:
        return  AdminResponseDTO(admin_id=admin.employee_id,
                                 first_name=str(admin.first_name),
                                 email=str(admin.email),
                                 enable=admin.enabled,
                                 job_title=admin.job_title,
                                 last_name=str(admin.last_name),
                                 login=str(admin.account.login),
                                 enable_login=admin.account.enabled,
                                 phone=str(admin.phone),
                                 roles=admin.role_ids())