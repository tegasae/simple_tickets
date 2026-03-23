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
                                 first_name=admin.first_name.value,
                                 email=admin.email.value,
                                 job_title=admin.job_title,
                                 last_name=admin.last_name.value,
                                 login=admin.account.login,
                                 phone=str(admin.phone),
                                 roles=admin.role_ids())