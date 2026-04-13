from src.domain.ticket import Ticket


class TicketDomainService:
    @staticmethod
    def create_ticket(*,
                      ticket_id: int,
                      client_id: int,
                      admin_id: int,
                      description: str,
                      text_of_ticket: str = "",
                      user_id: int = 0,
                      contact_user_id: int = 0,
                      is_remote: bool = False,
                      urgency_level: int = 0,
                      user_ticket_id: int = 0,
                      executor_id:int=0,
                      comment:str="")->Ticket:
        """Создание заявки без заявки пользователя"""
        ticket = Ticket.create(
            ticket_id=ticket_id,
            client_id=client_id,
            admin_id=admin_id,
            description=description,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=contact_user_id,
            is_remote=is_remote,
            urgency_level=urgency_level,
            user_ticket_id=user_ticket_id,
            executor_id=executor_id,
            comment=comment
        )

        return ticket

    def to_at_work(self):
        """Перевод заявки в работу без заявки пользователя"""
        raise NotImplementedError

    def to_deferred(self):
        """Перевод заявки в отложено без заявки пользователя"""
        raise NotImplementedError

    def to_executed(self):
        """Перевод заявки в выполнено без заявки пользователя"""
        raise NotImplementedError

    def to_cancelled(self):
        """Перевод заявки в снято без заявки пользователя"""
        raise NotImplementedError

    def add_comment(self):
        """Добавление комментария без заявки пользователя"""
        raise NotImplementedError

    def add_executed(self):
        """Добавление исполнителя без заявки пользователя"""
        raise NotImplementedError
