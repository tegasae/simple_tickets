"""Verify the common CAS participation; PostgreSQL interleaving is not claimed."""
import pytest

from conftest import transaction
from src.domain.employee import Admin


@pytest.mark.parametrize('assignment', ['self', 'other', 'remote_self'])
def test_new_assignment_advances_the_executor_guard_version(world, assignment):
    """Valid assignment stores executor, synchronized state and one version increment."""
    external_id = world.user_ticket(remote_work_recommended=True)['ticket_user_id']
    with transaction(world.path) as uow:
        internal_id = uow.tickets.get_by_user_ticket_id(external_id).ticket_id
        if assignment == 'other':
            executor = uow.admins.save(Admin.create(first_name='Synthetic second executor',
                department_id=world.department_id))
            executor_id = executor.employee_id
        else:
            executor_id = world.admin_id
    world.action(internal_id, 'accept')
    world.action(internal_id, 'department', {'department_id': world.department_id})
    with transaction(world.path) as uow:
        version = uow.admins.get(executor_id).version
    if assignment == 'remote_self':
        response = world.action(internal_id, 'start-remote-work')
        assert response["statuses"][-1]["work_is_remote"] is True
    else:
        response = world.action(internal_id, 'executor', {'executor_id': executor_id})
    assert response["current_executor_id"] == executor_id
    with transaction(world.path) as uow:
        assert uow.admins.get(executor_id).version == version + 1
        ticket = uow.tickets.get(internal_id)
        assert ticket.current_executor_id() == executor_id
        assert ticket.current_status().value == ("at_work" if assignment == "remote_self" else "assigned")
        assert uow.user_tickets.get(external_id).current_status().value == "in_work"


@pytest.mark.parametrize('assignment', ['self', 'remote_self'])
def test_guard_failure_rolls_back_assignment_and_both_histories(world, monkeypatch, assignment):
    """409 from a stale executor leaves both histories and versions unchanged."""
    from src.adapters.repositories.admin import AdminRepositorySQLite
    from src.adapters.repositories.exceptions import OptimisticLockError
    external_id = world.user_ticket(remote_work_recommended=True)['ticket_user_id']
    with transaction(world.path) as uow:
        internal_id = uow.tickets.get_by_user_ticket_id(external_id).ticket_id
    world.action(internal_id, 'accept')
    world.action(internal_id, 'department', {'department_id': world.department_id})
    with transaction(world.path) as uow:
        internal, external = uow.tickets.get(internal_id), uow.user_tickets.get(external_id)
        before = (internal.version, external.version, len(internal.statuses), len(external.statuses),
                  internal.current_status(), external.current_status(), uow.admins.get(world.admin_id).version)
    touched = []
    def stale_guard(repository, admin):
        touched.append(admin.employee_id)
        raise OptimisticLockError('Synthetic stale executor')
    monkeypatch.setattr(AdminRepositorySQLite, 'touch', stale_guard)
    command = 'start-remote-work' if assignment == 'remote_self' else 'executor'
    body = {} if assignment == 'remote_self' else {'executor_id': world.admin_id}
    response = world.api.patch(f'/admin/tickets/{internal_id}/{command}',
                              headers=world.admin_headers, json=body)
    assert response.status_code == 409
    assert touched == [world.admin_id]
    with transaction(world.path) as uow:
        internal, external = uow.tickets.get(internal_id), uow.user_tickets.get(external_id)
        assert (internal.version, external.version, len(internal.statuses), len(external.statuses),
                internal.current_status(), external.current_status(), uow.admins.get(world.admin_id).version) == before


def accepted_pair(world, *, recommended=True, department=True):
    external_id = world.user_ticket(remote_work_recommended=recommended)["ticket_user_id"]
    with transaction(world.path) as uow:
        internal_id = uow.tickets.get_by_user_ticket_id(external_id).ticket_id
    world.action(internal_id, "accept")
    if department:
        world.action(internal_id, "department", {"department_id": world.department_id})
    return internal_id, external_id


def pair_state(world, internal_id, external_id):
    with transaction(world.path) as uow:
        ticket, external = uow.tickets.get(internal_id), uow.user_tickets.get(external_id)
        return (
            ticket.current_status().value, ticket.current_executor_id(), ticket.version,
            tuple((s.status.value, s.actor_employee_id, s.executor_id) for s in ticket.statuses),
            external.current_status().value, external.version,
            tuple((s.status.value, s.actor_employee_id) for s in external.statuses),
        )


def test_wrong_department_preserves_assigned_pair(world):
    """Same department gives 200; another department gives 400 with both histories intact."""
    from src.domain.department import Department
    internal_id, external_id = accepted_pair(world)
    assigned = world.action(internal_id, "executor", {"executor_id": world.admin_id})
    assert assigned["current_executor_id"] == world.admin_id
    before = pair_state(world, internal_id, external_id)
    assert before[:2] == ("assigned", world.admin_id)
    assert before[4] == "in_work"
    with transaction(world.path) as uow:
        dept = uow.departments.save(Department.create(name="Synthetic other department"))
        outsider = uow.admins.save(Admin.create(first_name="Synthetic outsider", department_id=dept.department_id))
        outsider_id, version = outsider.employee_id, outsider.version
    rejected = world.api.patch(
        f"/admin/tickets/{internal_id}/executor", json={"executor_id": outsider_id},
        headers=world.admin_headers,
    )
    assert rejected.status_code == 400
    assert pair_state(world, internal_id, external_id) == before
    with transaction(world.path) as uow:
        assert uow.admins.get(outsider_id).version == version


@pytest.mark.parametrize("edge", ["no-department", "not-recommended", "other-executor", "repeat"])
def test_remote_rejection_leaves_pair_and_guard_unchanged(world, edge):
    """Invalid remote start gives 400, preserving both statuses and executor version."""
    internal_id, external_id = accepted_pair(
        world, recommended=edge != "not-recommended", department=edge != "no-department",
    )
    if edge == "other-executor":
        with transaction(world.path) as uow:
            other = uow.admins.save(Admin.create(first_name="Synthetic remote executor", department_id=world.department_id))
        world.action(internal_id, "executor", {"executor_id": other.employee_id})
    elif edge == "repeat":
        result = world.action(internal_id, "start-remote-work")
        assert result["statuses"][-1]["status"] == "at_work"
        assert result["statuses"][-1]["work_is_remote"] is True
    before = pair_state(world, internal_id, external_id)
    with transaction(world.path) as uow:
        version = uow.admins.get(world.admin_id).version
    rejected = world.api.patch(f"/admin/tickets/{internal_id}/start-remote-work", json={}, headers=world.admin_headers)
    assert rejected.status_code == 400
    assert pair_state(world, internal_id, external_id) == before
    with transaction(world.path) as uow:
        assert uow.admins.get(world.admin_id).version == version


def test_remote_start_after_assignment_keeps_one_executor(world):
    """ASSIGNED → AT_WORK records remote work without a second assignment."""
    internal_id, external_id = accepted_pair(world)
    world.action(internal_id, "executor", {"executor_id": world.admin_id})
    before = pair_state(world, internal_id, external_id)
    with transaction(world.path) as uow:
        version = uow.admins.get(world.admin_id).version
    response = world.action(internal_id, "start-remote-work", {"comment": "Started remotely"})
    assert response["statuses"][-1]["work_is_remote"] is True
    after = pair_state(world, internal_id, external_id)
    assert after[:2] == ("at_work", world.admin_id)
    assert len(after[3]) == len(before[3]) + 1
    assert after[4] == "in_work"
    with transaction(world.path) as uow:
        assert uow.admins.get(world.admin_id).version == version


@pytest.mark.parametrize("branch", ["assign", "remote-self"])
def test_partial_ticket_save_rolls_back_pair_and_employee_version(world, monkeypatch, branch):
    """Failure after actual writes restores both tickets and the touched executor."""
    from src.adapters.repositories.ticket_repository import TicketRepositorySQLite
    internal_id, external_id = accepted_pair(world)
    before = pair_state(world, internal_id, external_id)
    with transaction(world.path) as uow:
        version = uow.admins.get(world.admin_id).version
    original = TicketRepositorySQLite.save

    def save_then_fail(self, ticket):
        original(self, ticket)
        raise RuntimeError("Synthetic error after persisting ticket")

    with monkeypatch.context() as patch:
        patch.setattr(TicketRepositorySQLite, "save", save_then_fail)
        step, body = (
            ("executor", {"executor_id": world.admin_id}) if branch == "assign" else ("start-remote-work", {})
        )
        response = world.api.patch(
            f"/admin/tickets/{internal_id}/{step}", headers=world.admin_headers, json=body,
        )
        assert response.status_code == 500
    assert pair_state(world, internal_id, external_id) == before
    with transaction(world.path) as uow:
        assert uow.admins.get(world.admin_id).version == version
