from __future__ import annotations

import pytest

from src.application.factory import ApplicationServiceFactory
from src.application.services.admin_service import AdminApplicationService
from src.application.services.client_service import ClientApplicationService
from src.application.services.department_service import DepartmentApplicationService
from src.application.services.role_service import AdminRoleService, UserRoleService
from src.application.services.user_service import UserApplicationService
from tests_pyramid.support.fakes import FakeUnitOfWork
from tests_pyramid.support.service_imports import TicketApplicationService, TicketUserApplicationService

pytestmark = pytest.mark.unit


def test_application_service_factory_exposes_only_active_services() -> None:
    uow = FakeUnitOfWork(); factory = ApplicationServiceFactory(uow)
    assert isinstance(factory.admin_service(), AdminApplicationService)
    assert isinstance(factory.user_service(), UserApplicationService)
    assert isinstance(factory.client_service(), ClientApplicationService)
    assert isinstance(factory.department_service(), DepartmentApplicationService)
    assert isinstance(factory.ticket_service(), TicketApplicationService)
    assert isinstance(factory.ticket_user_service(), TicketUserApplicationService)
    assert isinstance(factory.admin_role_service(), AdminRoleService)
    assert isinstance(factory.user_role_service(), UserRoleService)
    assert not hasattr(factory, "ticket_search_service"), "search service is intentionally postponed"
