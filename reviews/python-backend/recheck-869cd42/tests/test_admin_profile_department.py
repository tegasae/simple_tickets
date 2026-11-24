"""Preserve optional Department on profile updates."""
import pytest

from conftest import transaction
from src.domain.department import Department
from test_executor_guard import accepted_pair, pair_state


def operator_state(world):
    with transaction(world.path) as uow:
        operator = uow.admins.get(world.admin_id)
        return (operator.first_name.value, operator.department_id)


def assign_operator(world):
    internal_id, external_id = accepted_pair(world)
    world.action(internal_id, "executor", {"executor_id": world.admin_id})
    return internal_id, external_id


@pytest.mark.parametrize("assigned", [False, True], ids=["idle", "current-executor"])
def test_omitted_department_preserves_department_during_profile_update(world, assigned):
    """200 and a changed name with the original department and assignment."""
    pair = assign_operator(world) if assigned else None
    before = pair_state(world, *pair) if pair else None
    answer = world.api.put(
        f"/admin/admins/{world.admin_id}",
        json={"first_name": "Updated operator"}, headers=world.admin_headers,
    )
    assert answer.status_code == 200
    assert answer.json()["department_id"] == world.department_id
    assert operator_state(world) == ("Updated operator", world.department_id)
    if pair:
        assert pair_state(world, *pair) == before


@pytest.mark.parametrize("assigned", [False, True], ids=["idle", "current-executor"])
def test_explicit_zero_respects_the_assignment_guard(world, assigned):
    """Explicit zero clears only an idle Admin's department."""
    pair = assign_operator(world) if assigned else None
    before = pair_state(world, *pair) if pair else None
    prior = operator_state(world)
    answer = world.api.put(
        f"/admin/admins/{world.admin_id}",
        json={"first_name": "Updated operator", "department_id": 0}, headers=world.admin_headers,
    )
    if assigned:
        assert answer.status_code == 400
        assert operator_state(world) == prior
        assert pair_state(world, *pair) == before
    else:
        assert answer.status_code == 200
        assert answer.json()["department_id"] == 0
        assert operator_state(world) == ("Updated operator", 0)


def test_explicit_other_department_for_idle_admin(world):
    """A positive enabled target preserves the ordinary department update."""
    with transaction(world.path) as uow:
        dept = uow.departments.save(Department.create(name="Synthetic new department"))
    response = world.api.put(
        f"/admin/admins/{world.admin_id}",
        json={"first_name": "Moved operator", "department_id": dept.department_id}, headers=world.admin_headers,
    )
    assert response.status_code == 200
    assert operator_state(world) == ("Moved operator", dept.department_id)


@pytest.mark.parametrize("invalid, status", [(None, 422), (999999, 404)], ids=["null", "unknown-id"])
def test_invalid_department_value_preserves_profile(world, invalid, status):
    """NULL and unknown targets leave the old profile and department intact."""
    before = operator_state(world)
    response = world.api.put(
        f"/admin/admins/{world.admin_id}",
        json={"first_name": "Synthetic rejected update", "department_id": invalid}, headers=world.admin_headers,
    )
    assert response.status_code == status
    assert operator_state(world) == before
