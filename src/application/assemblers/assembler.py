# src/application/assemblers/assembler.py
from src.application.dto.employee_dto import AdminResponseDTO, UserResponseDTO
from src.application.dto.ticket_dto import TicketResponseDTO, TicketUserResponseDTO
from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
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
            created_by_admin=client.created_by_admin_id,
            date_created=str(client.date_created)
        )

class TicketAssembler:
    @staticmethod
    def unwrap(value):
        return None if isinstance(value, Empty) else str(value)


    @staticmethod
    def to_dto(ticket: Ticket) -> TicketResponseDTO:
        statuses=[]
        for status in ticket.statuses:
             statuses.append({'id':status.status_id,'status':status.status.value,'actor_id':status.actor_employee_id,'date':str(status.date_created)})

        comments = []
        for comment in ticket.comments:
            comments.append({'id': comment.comment_id, 'comment': comment.comment, 'actor_id': comment.employee_id, 'date': str(comment.date_created)})


        executors=[]
        for executor in ticket.executors:
            executors.append({'id': executor.executor_id, 'admin_id':executor.admin_id,'date': str(executor.date_created)})


        return TicketResponseDTO(
            ticket_id=ticket.ticket_id,
            date_created=TicketAssembler.unwrap(ticket.date_created),
            description=TicketAssembler.unwrap(ticket.description),
            date_finished=TicketAssembler.unwrap(ticket.date_finished),
            contact_user_id=ticket.contact_user_id,
            text_of_ticket=ticket.text_of_ticket,
            is_remote=ticket.is_remote,
            urgency_level=ticket.urgency_level,
            client_id=ticket.client_id,
            user_id=ticket.user_id,
            user_ticket_id=ticket.user_ticket_id,
            statuses=statuses,
            comments=comments,
            executors=executors
        )



class TicketUserAssembler:
    @staticmethod
    def unwrap(value):
        return None if isinstance(value, Empty) else str(value)


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
            date_created=TicketAssembler.unwrap(ticket_user.date_created),
            description=TicketAssembler.unwrap(ticket_user.description),
            date_finished=TicketAssembler.unwrap(ticket_user.date_finished),
            contact_user_id=ticket_user.contact_user_id,
            user_id=ticket_user.user_id,
            statuses=statuses,
            comments=comments,
            is_closed=ticket_user.is_closed
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

