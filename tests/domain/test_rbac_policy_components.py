from __future__ import annotations

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.policies.ticket import TicketPolicy
from src.domain.policies.ticket_user_ticket import TicketUserTicketPolicy
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role import Authorizer, RoleManager
from src.domain.rbac.role_new import AdminRole, Role, RoleStore, UserRole
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment, CommentThread, ExecutorAssignment, ExecutorAssignments



def test_comment_thread_preserves_added_comments():
    thread = CommentThread()
    comment = Comment(employee_id=1, comment="Hello")

    thread.add(comment)

    assert thread.comments == [comment]


def test_executor_assignments_returns_current_assignment():
    assignments = ExecutorAssignments()
    first = ExecutorAssignment(admin_id=1, executor_id=2)
    second = ExecutorAssignment(admin_id=1, executor_id=3)

    assignments.add(first)
    assignments.add(second)

    assert assignments.current() == second


def test_executor_assignments_current_rejects_empty_history():
    with pytest.raises(DomainOperationError, match="No executor"):
        ExecutorAssignments().current()


def test_role_has_permission_and_role_store_membership():
    role = Role(
        role_id=1,
        name="operator",
        permissions=frozenset({AdminPermission.TICKET_OPERATION}),
    )
    store = RoleStore()

    assert role.has_permission(AdminPermission.TICKET_OPERATION) is True


    store.put_role(role)
    assert store.check_role(role) is True
    store.delete_role(role)
    assert store.check_role(role) is False


#@pytest.mark.xfail(reason="Current AdminRole is not a dataclass, so __post_init__ is not called yet.")
def test_admin_role_rejects_user_permission():
    with pytest.raises(ValueError, match="AdminRole"):
        AdminRole(
            role_id=1,
            name="bad",
            permissions=frozenset({UserPermission.TICKET_OPERATION}),
        )


#@pytest.mark.xfail(reason="Current UserRole is not a dataclass, so __post_init__ is not called yet.")
def test_user_role_rejects_admin_permission():
    with pytest.raises(ValueError, match="UserRole"):
        UserRole(
            role_id=1,
            name="bad",
            permissions=frozenset({AdminPermission.TICKET_OPERATION}),
        )


def test_authorizer_collects_permissions_from_subject_roles(admin_with_all_permissions):
    roles = {
        1: Role(
            role_id=1,
            name="creator",
            permissions=frozenset({AdminPermission.TICKET_OPERATION}),
        ),
        2: Role(
            role_id=2,
            name="viewer",
            permissions=frozenset({AdminPermission.TICKET_OPERATION}),
        ),
    }

    class Repo:
        def get(self, role_id: int):
            return roles[role_id]

    admin_with_all_permissions.grant_role(2)
    authorizer = Authorizer(Repo())

    assert authorizer.permissions_of(admin_with_all_permissions) == {
        AdminPermission.TICKET_OPERATION,

    }


def test_authorizer_requires_existing_permission(admin_with_all_permissions):
    role = Role(
        role_id=1,
        name="creator",
        permissions=frozenset({AdminPermission.TICKET_OPERATION}),
    )

    class Repo:
        def get(self, role_id: int):
            return role

    authorizer = Authorizer(Repo())

    authorizer.require(admin_with_all_permissions, AdminPermission.TICKET_OPERATION)

    with pytest.raises(PermissionError, match="lacks permission"):
        authorizer.require(admin_with_all_permissions, AdminPermission.TICKET_VIEW)


def test_role_manager_grants_and_revokes_roles_after_permission_check(admin_with_all_permissions, other_admin):
    roles = {
        1: Role(role_id=1, name="root", permissions=frozenset({AdminPermission.ROLE_ASSIGN, AdminPermission.ROLE_REVOKE})),
        2: Role(role_id=2, name="operator", permissions=frozenset({AdminPermission.TICKET_OPERATION})),
    }

    class Repo:
        def get(self, role_id: int):
            return roles[role_id]

    manager = RoleManager(Authorizer(Repo()), Repo())

    manager.grant_role(admin_with_all_permissions, other_admin, 2, required_permission=AdminPermission.ROLE_REVOKE)
    assert 2 in other_admin.role_ids()

    manager.revoke_role(admin_with_all_permissions, other_admin, 2, required_permission=AdminPermission.ROLE_REVOKE)
    assert 2 not in other_admin.role_ids()


def test_ticket_policy_rejects_disabled_entities(admin_with_all_permissions, client, user):
    client.disable()
    with pytest.raises(DomainOperationError, match="disabled client"):
        TicketPolicy.ensure_client_enabled(client)

    admin_with_all_permissions.disable()
    with pytest.raises(DomainOperationError, match="disabled admin"):
        TicketPolicy.ensure_admin_enabled(admin_with_all_permissions)

    user.disable()
    with pytest.raises(DomainOperationError, match="disabled"):
        TicketPolicy.ensure_user_enabled(user)


def test_ticket_policy_checks_user_and_ticket_user_client_relationship(client, user, user_ticket):
    other_client = type("OtherClient", (), {"client_id": client.client_id + 1})()

    with pytest.raises(DomainOperationError, match="does not belong"):
        TicketPolicy.ensure_user_belongs_to_client(user, other_client)

    with pytest.raises(DomainOperationError, match="does not belong"):
        TicketPolicy.ensure_ticket_user_belongs_to_client(user_ticket, other_client)


def test_ticket_policy_rejects_ticket_that_already_has_user_ticket(client, admin_with_all_permissions):
    ticket = Ticket.create(
        ticket_id=1,
        client_id=client.client_id,
        admin_id=admin_with_all_permissions.employee_id,
        text_of_ticket="Broken printer",
        user_ticket_id=99,
    )

    with pytest.raises(DomainOperationError, match="has a ticket user"):
        TicketPolicy.ensure_ticket_does_not_have_ticket_user(ticket)


def test_ticket_user_ticket_policy_allows_cancel_when_admin_ticket_is_cancelled(client, admin_with_all_permissions, user_ticket):
    ticket = Ticket.create(
        ticket_id=1,
        client_id=client.client_id,
        admin_id=admin_with_all_permissions.employee_id,
        text_of_ticket="Broken printer",
    )

    TicketManagementService.reject(ticket=ticket,actor_employee_id=admin_with_all_permissions.employee_id,comment="Duplicate")


def test_ticket_user_ticket_policy_rejects_cancel_when_admin_ticket_is_active(client, admin_with_all_permissions, user_ticket):
    ticket = Ticket.create(
        ticket_id=1,
        client_id=client.client_id,
        admin_id=admin_with_all_permissions.employee_id,
        text_of_ticket="Broken printer",
    )

    with pytest.raises(DomainOperationError, match="active ticket"):
        TicketUserTicketPolicy.can_cancel_user_ticket(user_ticket, ticket)


def test_ticket_user_ticket_policy_rejects_delete_when_admin_ticket_exists(client, admin_with_all_permissions, user_ticket):
    ticket = Ticket.create(
        ticket_id=1,
        client_id=client.client_id,
        admin_id=admin_with_all_permissions.employee_id,
        text_of_ticket="Broken printer",
    )

    with pytest.raises(DomainOperationError, match="active ticket"):
        TicketUserTicketPolicy.can_delete_user_ticket(user_ticket, ticket)
