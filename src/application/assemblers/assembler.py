# src/application/assemblers/assembler.py
from src.application.dto.department_dto import DepartmentResponseDTO
from src.application.dto.employee_dto import AdminResponseDTO, UserResponseDTO
from src.application.dto.ticket_dto import TicketResponseDTO, TicketUserResponseDTO
from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from src.application.dto.client_dto import ClientResponseDTO




class ClientAssembler:

    @staticmethod
    def to_dto(client: Client) -> ClientResponseDTO:



        return ClientResponseDTO(
            client_id=client.client_id,
            name=str(client.name),
            email=str(client.email),
            address=str(client.address),
            phone=str(client.phone),
            enabled=client.enabled,
            created_by_admin=client.created_by_admin_id,
            date_created=str(client.date_created)
        )


class TicketAssembler:
    @staticmethod
    def to_dto(ticket: Ticket) -> TicketResponseDTO:
        statuses = [
            {
                "id": record.status_id,
                "status": record.status.value,
                "actor_id": record.actor_employee_id,
                "executor_id": record.executor_id,
                "date_created": str(record.date_created),
                "planned_start_at": (
                    str(record.planned_start_at)
                    if record.planned_start_at is not None
                    else None
                ),
                "planned_finish_at": (
                    str(record.planned_finish_at)
                    if record.planned_finish_at is not None
                    else None
                ),
                "actual_started_at": (
                    str(record.actual_started_at)
                    if record.actual_started_at is not None
                    else None
                ),
                "actual_finished_at": (
                    str(record.actual_finished_at)
                    if record.actual_finished_at is not None
                    else None
                ),
                "comment": record.comment,
            }
            for record in ticket.statuses
        ]

        comments = [
            {
                "id": comment.comment_id,
                "actor_id": comment.employee_id,
                "comment": comment.comment,
                "date_created": str(comment.date_created),
            }
            for comment in ticket.comments
        ]

        return TicketResponseDTO(
            ticket_id=ticket.ticket_id,
            client_id=ticket.client_id,
            admin_id=ticket.admin_id,
            user_id=ticket.user_id,
            contact_user_id=ticket.contact_user_id,
            user_ticket_id=ticket.user_ticket_id,
            department_id=ticket.department_id,
            text_of_ticket=ticket.text_of_ticket,
            description=ticket.description,
            date_created=str(ticket.date_created),
            date_finished=(
                str(ticket.date_finished)
                if ticket.date_finished is not None
                else None
            ),
            is_remote=ticket.is_remote,
            urgency_level=ticket.urgency_level,
            version=ticket.version,
            is_closed=ticket.is_closed,
            statuses=statuses,
            comments=comments,
        )



class TicketUserAssembler:

    @staticmethod
    def to_dto(ticket_user: TicketUser) -> TicketUserResponseDTO:
        statuses=[]
        for status in ticket_user.statuses:
             statuses.append({'id':status.status_id,'status':status.status.value,'actor_id':status.actor_employee_id,'date':str(status.date_created)})

        comments = []
        for comment in ticket_user.comments:
            comments.append({'id': comment.comment_id, 'comment': comment.comment, 'actor_id': comment.employee_id, 'date': str(comment.date_created)})




        return TicketUserResponseDTO(
            ticket_id=ticket_user.ticket_id,
            date_created=str(ticket_user.date_created),
            description=str(ticket_user.description),
            date_finished=str(ticket_user.date_finished),
            contact_user_id=ticket_user.contact_user_id,
            user_id=ticket_user.user_id,
            statuses=statuses,
            comments=comments,
            is_closed=ticket_user.is_closed,
            current_status=ticket_user.current_status(),
            client_id=ticket_user.client_id,
            text_of_ticket=ticket_user.text_of_ticket,
            urgency_level=ticket_user.urgency_level
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
                                 date_created=str(admin.date_created))

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
                                 date_created=str(user.date_created))




class DepartmentAssembler:
    @staticmethod
    def to_dto(department: Department) -> DepartmentResponseDTO:
        return DepartmentResponseDTO(
            department_id=department.department_id,
            name=str(department.name),
            enabled=department.enabled,
            date_created=department.date_created,
        )