from src.application.assemblers.assembler import TicketUserAssembler
from src.application.dto.ticket_dto import TicketUserResponseDTO, TicketUserDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.exceptions import ItemNotFoundError
from src.domain.policy.ticket import TicketPolicy
from src.domain.policy.ticket_user_ticket import TicketUserTicketPolicy
from src.domain.rbac.permissions import UserPermission
from src.domain.ticket_components import Comment
from src.domain.ticket_user import TicketUser
from src.domain.uow.unit_of_work import UnitOfWork


class TicketUserApplicationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    def _save_and_to_dto(self, ticket_user: TicketUser) -> TicketUserResponseDTO:
        saved_ticket = self.uow.user_tickets.save(ticket=ticket_user)
        return TicketUserAssembler.to_dto(saved_ticket)

    def _validate_references(self,ticket_user_dto: TicketUserDTO):
        """
                Validates referenced entities and returns the effective admin_id.
                """

        client = self.uow.clients.get(ticket_user_dto.client_id)


        TicketPolicy.ensure_client_enabled(client)

        if ticket_user_dto.user_id:
            user = self.uow.users.get(ticket_user_dto.user_id)
            TicketPolicy.ensure_user_enabled(user)
            TicketPolicy.ensure_user_belongs_to_client(user, client)

        if ticket_user_dto.contact_user_id:
            contact_user = self.uow.users.get(ticket_user_dto.contact_user_id)
            TicketPolicy.ensure_user_enabled(contact_user)
            TicketPolicy.ensure_user_belongs_to_client(contact_user, client)


        if ticket_user_dto.ticket_id:
            user_ticket = self.uow.user_tickets.get(ticket_user_dto.ticket_id)
            TicketPolicy.ensure_ticket_user_belongs_to_client(user_ticket, client)

    def create_ticket(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:

        with self.uow:
            self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                           permission=UserPermission.TICKET_OPERATION)

            self._validate_references(ticket_user_dto)

            ticket_user = TicketUser.create(
                ticket_id=0,
                client_id=ticket_user_dto.client_id,
                description=ticket_user_dto.description,
                user_id=ticket_user_dto.user_id,
                contact_user_id=ticket_user_dto.contact_user_id,
            )

            return self._save_and_to_dto(ticket_user)


    def add_comment(self,*, ticket_user_dto: TicketUserDTO)->TicketUserResponseDTO:
        """Добавление комментария автором заявки или тем, кто имеет право делать"""
        with self.uow:
            self._validate_references(ticket_user_dto)
            ticket_user = self.uow.user_tickets.get(ticket_id=ticket_user_dto.ticket_id)
            if ticket_user.user_id==ticket_user_dto.user_id:
                self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                              permission=UserPermission.TICKET_OPERATION_ALL)
            else:
                self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                              permission=UserPermission.TICKET_OPERATION)
            commet=Comment(employee_id=ticket_user_dto.user_id,comment=ticket_user_dto.comment)
            ticket_user.add_comment(commet)
            return self._save_and_to_dto(ticket_user)



    def cancel(self,*,ticket_user_dto:TicketUserDTO)->TicketUserResponseDTO:
        """Снятие заявки либо автором, либо кто имеет право. Снятие заявки возможно, если нет связи с заявкой админа"""
        with self.uow:
            self._validate_references(ticket_user_dto)
            ticket_user = self.uow.user_tickets.get(ticket_id=ticket_user_dto.ticket_id)
            if ticket_user.user_id==ticket_user_dto.user_id:
                self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                              permission=UserPermission.TICKET_OPERATION)
            else:
                self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                              permission=UserPermission.TICKET_OPERATION_ALL)



            try:
                ticket=self.uow.tickets.get_by_user_ticket_id(user_ticket_id=ticket_user_dto.ticket_id)
            except ItemNotFoundError:
                ticket=None
            TicketUserTicketPolicy.can_cancel_user_ticket(ticket_user,ticket)
            ticket_user.cancel_by_client(actor_employee_id=ticket_user_dto.user_id)
            return self._save_and_to_dto(ticket_user)


    def delete(self,*,ticket_user_dto:TicketUserDTO)->None:
        """Заявку может удалить автор, либо кто имеет на это право. Удалить можно, если не привязана заявка админа"""
        self._validate_references(ticket_user_dto)
        ticket_user = self.uow.user_tickets.get(ticket_id=ticket_user_dto.ticket_id)
        if ticket_user.user_id == ticket_user_dto.user_id:
            self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                          permission=UserPermission.TICKET_OPERATION)
        else:
            self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                          permission=UserPermission.TICKET_OPERATION_ALL)


        try:
            ticket = self.uow.tickets.get_by_user_ticket_id(user_ticket_id=ticket_user_dto.ticket_id)
        except ItemNotFoundError:
            ticket = None
        TicketUserTicketPolicy.can_delete_user_ticket(ticket_user, ticket)


        self.uow.user_tickets.delete(ticket_user_dto.ticket_id)

    def get_by_ticket_id(self,*,ticket_user_dto:TicketUserDTO)->TicketUserResponseDTO:
        with self.uow:
            self._validate_references(ticket_user_dto)
            ticket_user = self.uow.user_tickets.get(ticket_id=ticket_user_dto.ticket_id)
            if ticket_user.user_id == ticket_user_dto.user_id:
                self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                              permission=UserPermission.TICKET_VIEW)
            else:
                self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                              permission=UserPermission.TICKET_VIEW_ALL)

            return TicketUserAssembler.to_dto(ticket_user)

    def get_all_own(self, *, ticket_user_dto: TicketUserDTO) -> list[TicketUserResponseDTO]:
        with self.uow:
            self._validate_references(ticket_user_dto)
            self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                              permission=UserPermission.TICKET_VIEW)
            tickets = self.uow.user_tickets.get_all()

            return [TicketUserAssembler.to_dto(ticket) for ticket in tickets if ticket.user_id == ticket_user_dto.user_id]

    def get_all(self, *, ticket_user_dto: TicketUserDTO) -> list[TicketUserResponseDTO]:
        with self.uow:
            self._validate_references(ticket_user_dto)
            self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                          permission=UserPermission.TICKET_VIEW_ALL)
            tickets = self.uow.user_tickets.get_all()

            return [TicketUserAssembler.to_dto(ticket) for ticket in tickets]



