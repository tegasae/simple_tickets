from src.domain.ticket_user import TicketUser, StatusTicketOfClient
from src.domain.ticket_components import Comment
from src.domain.repositories.ticket_user_repository import TicketUserRepository


class TicketUserService:

    def __init__(self, repo: TicketUserRepository):
        self._repo = repo

    def create_ticket(
        self,
        *,
        client_id: int,
        user_id: int,
        contact_user_id: int,
        description: str,
    ) -> TicketUser:

        ticket = TicketUser.create(ticket_id=0,
            client_id=client_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            description=description,)

        return self._repo.save(ticket)

    def change_status(
        self,
        *,
        ticket_id: int,
        new_status: StatusTicketOfClient,
        actor_employee_id: int,
    ) -> TicketUser:

        ticket = self._repo.get(ticket_id)

        ticket.change_status(new_status, actor_employee_id)

        return self._repo.save(ticket)

    def add_comment(
        self,
        *,
        ticket_id: int,
        employee_id: int,
        comment: str,
    ) -> TicketUser:

        ticket = self._repo.get(ticket_id)

        ticket.add_comment(Comment(employee_id=employee_id, comment=comment))

        return self._repo.save(ticket)

    def get_by_id(self, ticket_id: int) -> TicketUser:
        return self._repo.get(ticket_id)

    def get_all(self) -> list[TicketUser]:
        return self._repo.get_all()

    def delete(self, ticket_id: int):
        self._repo.delete(ticket_id)

