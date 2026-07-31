# src/application/services/service_factory.py
from src.application.services.department_service import DepartmentApplicationService
from src.application.services.role_service import AdminRoleService, UserRoleService
from src.application.services.ticket_search_service import TicketSearchService

from src.services.uow.uow import UnitOfWork

from src.application.services.admin_service import AdminApplicationService
from src.application.services.user_service import UserApplicationService
from src.application.services.client_service import ClientApplicationService
from src.application.services.ticket_service import TicketApplicationService
from src.application.services.ticket_user_service import TicketUserApplicationService


class ApplicationServiceFactory:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def admin_service(self) -> AdminApplicationService:
        return AdminApplicationService(self.uow)

    def user_service(self) -> UserApplicationService:
        return UserApplicationService(self.uow)

    def client_service(self) -> ClientApplicationService:
        return ClientApplicationService(self.uow)

    def ticket_service(self) -> TicketApplicationService:
        return TicketApplicationService(self.uow)

    def ticket_search_service(self)->TicketSearchService:
        return TicketSearchService(uow=self.uow)

    def ticket_user_service(self) -> TicketUserApplicationService:
        return TicketUserApplicationService(self.uow)

    def role_admin_service(self) -> AdminRoleService:
        return AdminRoleService(self.uow)

    def role_user_service(self) -> UserRoleService:
        return UserRoleService(self.uow)

    def department_service(self) -> DepartmentApplicationService:
        return DepartmentApplicationService(self.uow)

    def admin_role_service(self) -> AdminRoleService:
        return AdminRoleService(self.uow)

    def user_role_service(self) -> UserRoleService:
        return UserRoleService(self.uow)
