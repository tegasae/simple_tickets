from src.application.assemblers.assembler import TicketUserAssembler
from src.application.dto.ticket_dto import TicketUserResponseDTO, TicketUserDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.rbac.permissions import UserPermission
from src.domain.ticket_user import TicketUser
from src.services.uow.uow import UnitOfWork


class TicketUserApplicationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    def _save_and_to_dto(self, ticket_user: TicketUser) -> TicketUserResponseDTO:
        saved_ticket = self.uow.user_tickets.save(ticket=ticket_user)
        return TicketUserAssembler.to_dto(saved_ticket)

    def _require_user_actor_for_create(self, ticket_user_dto: TicketUserDTO):
        user_actor = self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                               permission=UserPermission.CREATE_TICKET)
        return user_actor

    def _validate_references(self,ticket_user_dto: TicketUserDTO):
        raise NotImplementedError

    def create_ticket(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:

        with self.uow:
            self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                           permission=UserPermission.CREATE_TICKET)

            self._validate_references(ticket_user_dto)

            ticket_user = TicketUser.create(
                ticket_id=0,
                client_id=ticket_user_dto.client_id,
                description=ticket_user_dto.description,
                user_id=ticket_user_dto.user_id,
                contact_user_id=ticket_user_dto.contact_user_id,
            )

            return self._save_and_to_dto(ticket_user)

    # todo методы и вынести в доменный слой что нужно
    def cancel_by_client_user(self):
        """Метод позволяет снять заявку от любоого пользователя этого клиента если есть права.
        Надо добавить в домен эту логику, снятие там"""
        raise NotImplementedError


    def cancel_user(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
        """Пользотватель снимает свою заявку"""
        with self.uow:
            self.actor.require_actor_user(actor_user_id=ticket_user_dto.user_id,
                                           permission=UserPermission.UPDATE_OWN_TICKET)

            self._validate_references(ticket_user_dto)

            ticket_user = self.uow.user_tickets.get(ticket_user_dto.ticket_id)
            ticket_user.cancel(
                actor_employee_id=ticket_dto.admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(ticket)

    def cancel_admin(self):
        """Админ может снять заявку"""
        raise NotImplementedError

    def add_comment_user(self):
        """Метод добавляет комментарий к заявке от пользователя"""
        raise NotImplementedError

    def add_comment_admin(self):
        """Метод добавляет комментарий к заявкке от админма"""
        raise NotImplementedError

    def link_to_ticket(self):
        """Админ привязяывет заявку к обычной заявку. И ее статус будет CONFIRMED, проверить в доменной модели"""
        raise NotImplementedError

    def at_work(self):
        """Админ переводит заявку в состоянии AT_WORK. Ее уже невозможно удалить"""
        raise NotImplementedError

    def delete_admin(self):
        """Админ удалает заявку, проверка что нет привзяанной заявки"""
        raise NotImplementedError

    def delete_user(self):
        """Пользователь удаляет заявку. Проверка что нет привязанной заявку"""
        raise NotImplementedError


    def view_user_ticket_id(self):
        """Просмотр заявку"""
        raise NotImplementedError

    def view_all_user_tickets(self):
        """Просмор всех заявок пользователя"""
        raise NotImplementedError


    def view_all_user_ticket_client(self):
        """Просмотр всех заявок клиента. могут смотреть либо пользовятели с правами, либо админ"""
        raise NotImplementedError


    def view_all_user_tickets_admin(self):
        """Просмотр всех заявок админом"""
        raise NotImplementedError


