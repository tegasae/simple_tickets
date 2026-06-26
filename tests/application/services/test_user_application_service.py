import pytest

from src.application.dto.employee_dto import UserDTO
from src.application.services.user_service import UserApplicationService
from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role_new import Role


def prepare_actor_and_client(uow):
    admin = Admin.create(employee_id=1, first_name="Root")
    admin.grant_role(1)
    uow.admins.save(admin)
    uow.roles_admin.save(
        Role(
            role_id=1,
            name="user manager",
            permissions=frozenset(
                {
                    AdminPermission.USER_OPERATION,
                    AdminPermission.USER_OPERATION,
                    AdminPermission.ROLE_ASSIGN,
                    AdminPermission.ROLE_REVOKE,
                }
            ),
        )
    )
    uow.clients.save(Client.create(client_id=1, name="Acme"))
    return admin


def test_create_user_saves_user(uow):
    prepare_actor_and_client(uow)
    service = UserApplicationService(uow)  # type: ignore[arg-type]

    dto = service.create_user(
        user_dto=UserDTO(
            actor_admin_id=1,
            client_id=1,
            first_name="Alice",
            last_name="Brown",
            login="alice",
            password="Secret123!",
        )
    )

    assert dto.employee_id == 1
    assert dto.client_id == 1
    assert dto.login == "alice"


def test_create_user_rejects_duplicate_login(uow):
    prepare_actor_and_client(uow)
    uow.users.save(
        User.create(employee_id=10, first_name="Existing", client_id=1, login="alice", password="Secret123!")
    )
    service = UserApplicationService(uow)  # type: ignore[arg-type]

    with pytest.raises(DomainOperationError):
        service.create_user(
            user_dto=UserDTO(
                actor_admin_id=1,
                client_id=1,
                first_name="Alice",
                login="alice",
                password="Secret123!",
            )
        )


def test_attach_detach_and_change_password(uow):
    prepare_actor_and_client(uow)
    user = User.create(employee_id=2, first_name="Alice", client_id=1)
    uow.users.save(user)
    service = UserApplicationService(uow)  # type: ignore[arg-type]

    attached = service.attach_account(
        user_dto=UserDTO(actor_admin_id=1, employee_id=2, client_id=1, login="alice", password="Secret123!")
    )
    assert attached.login == "alice"

    service.change_password(
        user_dto=UserDTO(actor_admin_id=1, employee_id=2, client_id=1, password="NewSecret123!")
    )
    assert uow.users.get(2).account.verify_password("NewSecret123!") is True

    detached = service.detach_account(user_dto=UserDTO(actor_admin_id=1, employee_id=2, client_id=1))
    assert detached.login == ""


def test_disable_enable_user(uow):
    prepare_actor_and_client(uow)
    user = User.create(employee_id=2, first_name="Alice", client_id=1)
    uow.users.save(user)
    service = UserApplicationService(uow)  # type: ignore[arg-type]

    disabled = service.disable(user_dto=UserDTO(actor_admin_id=1, employee_id=2, client_id=1))
    enabled = service.enable(user_dto=UserDTO(actor_admin_id=1, employee_id=2, client_id=1))

    assert disabled.enabled is False
    assert enabled.enabled is True
