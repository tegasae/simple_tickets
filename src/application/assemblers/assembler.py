# src/application/assemblers/assembler.py
from typing import TypeVar

from src.application.dto.department_dto import DepartmentResponseDTO
from src.application.dto.employee_dto import AdminResponseDTO, UserResponseDTO, PermissionsResponseDTO
from src.application.dto.roles_dto import RoleResponseDTO
from src.application.dto.ticket_dto import TicketResponseDTO, TicketUserResponseDTO
from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission, PermissionBase
from src.domain.rbac.role_new import Role
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from src.application.dto.client_dto import ClientResponseDTO
from src.domain.value_objects import CommonComment, Description


class ClientAssembler:

    @staticmethod
    def to_dto(client: Client) -> ClientResponseDTO:



        return ClientResponseDTO(
            client_id=client.client_id,
            name=str(client.name),
            email=str(client.email),
            address=str(client.address),
            phone=str(client.phone),
            description=str(client.description),
            enabled=client.enabled,
            created_by_admin=client.created_by_admin_id,
            date_created=str(client.date_created)
        )


class TicketAssembler:
    @staticmethod
    def to_dto(
        ticket: Ticket,
    ) -> TicketResponseDTO:
        statuses = [
            {
                "id": record.status_id,
                "status": record.status.value,
                "actor_id": record.actor_employee_id,
                "executor_id": record.executor_id,
                "date_created": record.date_created,

                "actual_started_at": record.actual_started_at,
                "actual_finished_at": record.actual_finished_at,

                "duration": record.duration,
                "work_is_remote": record.work_is_remote,

                "comment": record.comment,
            }
            for record in ticket.statuses
        ]

        comments = [
            {
                "id": comment.comment_id,
                "actor_id": comment.employee_id,
                "comment": comment.comment,
                "date_created": comment.date_created,
            }
            for comment in ticket.comments
        ]

        return TicketResponseDTO(
            ticket_id=ticket.ticket_id,

            client_id=ticket.client_id,

            user_id=ticket.user_id,
            contact_user_id=ticket.contact_user_id,
            user_ticket_id=ticket.user_ticket_id,

            department_id=ticket.department_id,

            text_of_ticket=ticket.text_of_ticket,
            description=ticket.description,

            date_created=ticket.date_created,
            date_finished=ticket.date_finished,

            planned_at=ticket.planned_at,

            remote_work_recommended=(
                ticket.remote_work_recommended
            ),

            urgency=ticket.urgency,
            current_executor_id=ticket.current_executor_id(),
            last_executor_id=ticket.last_executor_id(),

            is_closed=ticket.is_closed,

            time_spent=ticket.working_time(),

            statuses=statuses,
            comments=comments,
        )




class TicketUserAssembler:

    @staticmethod
    def to_dto(
        ticket_user: TicketUser,
    ) -> TicketUserResponseDTO:
        statuses = [
            {
                "id": record.ticket_user_status_id,
                "status": record.status.value,
                "actor_id": record.actor_employee_id,
                "comment": (
                    record.comment.value
                    if isinstance(record.comment, CommonComment)
                    else ""
                ),
                "date_created": record.date_created,
            }
            for record in ticket_user.statuses
        ]

        comments = [
            {
                "id": comment.comment_id,
                "actor_id": comment.employee_id,
                "comment": comment.comment.value,
                "date_created": comment.date_created,
            }
            for comment in ticket_user.comments
        ]

        description = (
            ticket_user.description.value
            if isinstance(ticket_user.description, Description)
            else ""
        )

        return TicketUserResponseDTO(
            ticket_user_id=ticket_user.ticket_user_id,
            client_id=ticket_user.client_id,
            user_id=ticket_user.user_id,
            contact_user_id=ticket_user.contact_user_id,
            text_of_ticket=ticket_user.text_of_ticket,
            description=description,
            current_status=str(ticket_user.current_status().value),
            date_created=ticket_user.date_created,
            date_finished=ticket_user.date_finished,
            is_closed=ticket_user.is_closed,
            statuses=statuses,
            comments=comments,
        )
class AdminAssembler:
    @staticmethod
    def to_dto(admin: Admin) -> AdminResponseDTO:
        return  AdminResponseDTO(employee_id=admin.employee_id,
                                 first_name=str(admin.first_name),
                                 email=str(admin.email),
                                 enabled=admin.enabled,
                                 job_title=admin.job_title,
                                 department_id=admin.department_id,
                                 last_name=str(admin.last_name),
                                 login=str(admin.account.login),
                                 enabled_login=admin.account.enabled,
                                 phone=str(admin.phone),
                                 roles=admin.role_ids(),
                                 date_created=str(admin.date_created),

                                 )

class UserAssembler:
    @staticmethod
    def to_dto(user: User) -> UserResponseDTO:
        return  UserResponseDTO(employee_id=user.employee_id,
                                client_id=user.client_id,
                                 first_name=str(user.first_name),
                                 email=str(user.email),
                                 enabled=user.enabled,
                                 last_name=str(user.last_name),
                                 login=str(user.account.login),
                                 enabled_login=user.account.enabled,
                                 phone=str(user.phone),
                                 roles=user.role_ids(),
                                 date_created=str(user.date_created),
                                 )



class PermissionAssembler:
    @staticmethod
    def to_admin_dto(permissions:frozenset[AdminPermission])->PermissionsResponseDTO:
        p = tuple(sorted(str(permission.value) for permission in permissions))
        return PermissionsResponseDTO(permissions=p)



class DepartmentAssembler:
    @staticmethod
    def to_dto(department: Department) -> DepartmentResponseDTO:
        return DepartmentResponseDTO(
            department_id=department.department_id,
            name=str(department.name),
            enabled=department.enabled,
            date_created=department.date_created,
        )





T = TypeVar("T", bound=PermissionBase)


class RoleAssembler:
    @staticmethod
    def to_dto(role: Role[T]) -> RoleResponseDTO[T]:
        return RoleResponseDTO[T](
            role_id=role.role_id,
            name=role.name,
            permissions=role.permissions,
            description=role.description,
            is_system_role=role.is_system_role,
        )