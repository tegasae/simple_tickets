"""Verify the common CAS participation; PostgreSQL interleaving is not claimed."""
import pytest

from conftest import transaction
from src.domain.employee import Admin


@pytest.mark.parametrize('assignment', ['self', 'other', 'remote_self'])
def test_new_assignment_advances_the_executor_guard_version(world, assignment):
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
        world.action(internal_id, 'start-remote-work')
    else:
        world.action(internal_id, 'executor', {'executor_id': executor_id})
    with transaction(world.path) as uow:
        assert uow.admins.get(executor_id).version == version + 1
        assert uow.tickets.get(internal_id).current_executor_id() == executor_id


@pytest.mark.parametrize('assignment', ['self', 'remote_self'])
def test_guard_failure_rolls_back_assignment_and_both_histories(world, monkeypatch, assignment):
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
