import pytest

from src.application.dto.client_dto import ClientDTO
from src.application.services.client_service import ClientApplicationService
from src.domain.client import Client
from src.domain.employee import Admin
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role_new import Role


def prepare_actor(uow):
    admin = Admin.create(employee_id=1, first_name="Root")
    admin.grant_role(1)
    uow.admins.save(admin)
    uow.roles_admin.save(Role(role_id=1, name="operator", permissions=frozenset({AdminPermission.OPERATION_CLIENT})))
    return admin


def test_create_client_saves_and_returns_dto(uow):
    prepare_actor(uow)
    service = ClientApplicationService(uow)  # type: ignore[arg-type]

    dto = service.create_client(
        ClientDTO(actor_admin_id=1, name="Acme", email="info@acme.com", address="Main", phone="123")
    )

    assert dto.client_id == 1
    assert dto.name == "Acme"
    assert dto.email == "info@acme.com"

    saved_client = uow.clients.get(dto.client_id)

    assert saved_client.client_id == dto.client_id
    assert saved_client.name.value == "Acme"
    assert saved_client.email.value == "info@acme.com"


def test_update_contact_changes_client(uow):
    prepare_actor(uow)
    client = Client.create(client_id=1, name="Acme")
    uow.clients.save(client)
    service = ClientApplicationService(uow)  # type: ignore[arg-type]

    dto = service.update_contact(ClientDTO(actor_admin_id=1, client_id=1, name="ignored", email="new@acme.com"))

    assert dto.email == "new@acme.com"


def test_disable_and_enable_client(uow):
    prepare_actor(uow)
    client = Client.create(client_id=1, name="Acme")
    uow.clients.save(client)
    service = ClientApplicationService(uow)  # type: ignore[arg-type]

    disabled = service.disable(ClientDTO(actor_admin_id=1, client_id=1, name="Acme"))
    enabled = service.enable(ClientDTO(actor_admin_id=1, client_id=1, name="Acme"))

    assert disabled.enabled is False
    assert enabled.enabled is True


def test_client_service_rejects_actor_without_permission(uow):
    admin = Admin.create(employee_id=1, first_name="Root")
    uow.admins.save(admin)
    service = ClientApplicationService(uow)  # type: ignore[arg-type]

    with pytest.raises(PermissionError):
        service.create_client(ClientDTO(actor_admin_id=1, name="Acme"))
