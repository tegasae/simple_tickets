# src/application/assemblers/assembler.py
from src.application.dto.employee_dto import AdminResponseDTO, UserResponseDTO
from src.domain.client import Client
from src.domain.employee import Admin, User
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
        return  AdminResponseDTO(employee_id=admin.employee_id,
                                 first_name=str(admin.first_name),
                                 email=str(admin.email),
                                 enabled=admin.enabled,
                                 job_title=admin.job_title,
                                 last_name=str(admin.last_name),
                                 login=str(admin.account.login),
                                 enabled_login=admin.account.enabled,
                                 phone=str(admin.phone),
                                 roles=admin.role_ids())

class UserAssembler:
    @staticmethod
    def to_dto(user: User) -> UserResponseDTO:
        return  UserResponseDTO(employee_id=user.employee_id,
                                client_id=user.client_id,
                                 first_name=str(user.first_name),
                                 email=str(user.email),
                                 enable=user.enabled,
                                 last_name=str(user.last_name),
                                 login=str(user.account.login),
                                 enable_login=user.account.enabled,
                                 phone=str(user.phone),
                                 roles=user.role_ids())

