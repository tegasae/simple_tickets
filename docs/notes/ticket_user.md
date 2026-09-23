
## TicketUser

### Состояния

| TicketUser | Ticket                                      |   |
|------------|---------------------------------------------|---|
| CREATED    | CREATED_FROM_TICKET_USER                    |   |
| IN_WORK    | ACCEPTED, DEFERRED, ASSIGNED,AT_WORK,PAUSED |   |
|            |                                             |   |






CREATED создана заявка, создается User, соответсвующий статус в Ticket CREATED_FROM_TICKET_USER
IN_WORK заявка активна, в Ticket все статусы, кроме 
WAITING_FOR_CONFIRMATION в Ticket статусы
DEFERRED отложена в Ticket статус DEFERRED но попадиние сюда при   

    EXECUTION_CONFIRMED_BY_USER = "execution_confirmed_by_user"
    EXECUTION_CONFIRMED_BY_ADMIN = "execution_confirmed_by_admin"

    CANCELLED_BY_USER = "cancelled_by_user"
    CANCELLED_BY_ADMIN = "cancelled_by_admin"


Нужен новый статус в Ticket DEFEREED по причине отключения пользователя или клиента, к ней не нужен комментрай
Тогда будет DEFERRED в TicketUser будет соотствоавать именно этому DEFERRED



class TicketStatus(StrEnum):
    CREATED = "created"
    CREATED_FROM_TICKET_USER = "created_from_ticket_user"

    REJECTED = "rejected"
    ACCEPTED = "accepted"

    DEFERRED = "deferred"
    SCHEDULED = "scheduled"
    ASSIGNED = "assigned"
    READY_TO_WORK = "ready_to_work"

    AT_WORK = "at_work"
    PAUSED = "paused"
    READY_FOR_REVIEW = "ready_for_review"

    EXECUTED = "executed"
    CANCELLED = "cancelled"
    CANCELLED_BY_USER = "cancelled_by_user"


