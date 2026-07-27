# src/application/services/ticket_search_service.py
from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import TicketResponseDTO
from src.application.dto.ticket_search_dto import TicketSearchDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.exceptions import DomainOperationError
from src.domain.repositories.ticket_repository import TicketSearchCriteria
from src.domain.uow.unit_of_work import UnitOfWork




class TicketSearchService:
    def __init__(
            self,
            *,
            uow: UnitOfWork,
    ) -> None:
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    def search(
            self,
            *,
            search_dto: TicketSearchDTO,
    ) -> list[TicketResponseDTO]:


        self._validate(search_dto)

        criteria = TicketSearchCriteria(
            client_id=search_dto.client_id,
            user_id=search_dto.user_id,
            admin_id=search_dto.admin_id,
            executor_id=search_dto.executor_id,
            department_id=search_dto.department_id,
            status=search_dto.status.strip(),
            is_closed=search_dto.is_closed,
            date_from=search_dto.date_from,
            date_to=search_dto.date_to,
            text=search_dto.text.strip(),
            limit=search_dto.limit,
            offset=search_dto.offset,
        )

        tickets = self.uow.tickets.search(criteria)

        return [
            TicketAssembler.to_dto(ticket)
            for ticket in tickets
        ]

    @staticmethod
    def _validate(
            search_dto: TicketSearchDTO,
    ) -> None:
        if search_dto.actor_admin_id <= 0:
            raise DomainOperationError(
                "actor_admin_id must be positive",
            )

        if search_dto.client_id < 0:
            raise DomainOperationError(
                "client_id cannot be negative",
            )

        if search_dto.user_id < 0:
            raise DomainOperationError(
                "user_id cannot be negative",
            )

        if search_dto.admin_id < 0:
            raise DomainOperationError(
                "admin_id cannot be negative",
            )

        if search_dto.executor_id < 0:
            raise DomainOperationError(
                "executor_id cannot be negative",
            )

        if search_dto.department_id < 0:
            raise DomainOperationError(
                "department_id cannot be negative",
            )

        if search_dto.limit <= 0:
            raise DomainOperationError(
                "limit must be positive",
            )

        if search_dto.limit > 500:
            raise DomainOperationError(
                "limit must be <= 500",
            )

        if search_dto.offset < 0:
            raise DomainOperationError(
                "offset cannot be negative",
            )

        if (
            search_dto.date_from is not None
            and search_dto.date_to is not None
            and search_dto.date_from >= search_dto.date_to
        ):
            raise DomainOperationError(
                "date_from must be earlier than date_to",
            )