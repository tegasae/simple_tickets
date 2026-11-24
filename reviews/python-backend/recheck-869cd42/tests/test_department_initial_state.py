"""Acceptance for the owner's explicit initial Department state."""
import pytest

from conftest import transaction


@pytest.mark.parametrize(
    "fields, active",
    [({}, True), ({"enabled": True}, True), ({"enabled": False}, False)],
    ids=["default", "true", "false"],
)
def test_create_department_saves_requested_initial_state(world, fields, active):
    """201. Missing enabled defaults to true, explicit false is persisted."""
    name = "Synthetic initial department"
    created = world.api.post("/admin/departments/", headers=world.admin_headers,
                             json={"name": name, **fields})
    assert created.status_code == 201
    identity = created.json()["department_id"]
    actual = created.json()["enabled"]
    readback = world.api.get(f"/admin/departments/{identity}", headers=world.admin_headers)
    assert readback.status_code == 200
    with transaction(world.path) as uow:
        state = uow.departments.get(identity).enabled
    assert (actual, readback.json()["enabled"], state) == (active, active, active)


def test_null_initial_department_state_rejected(world):
    """Explicit null gives 422 and does not create a Department."""
    with transaction(world.path) as uow:
        before = len(uow.departments.get_all())
    answer = world.api.post("/admin/departments/", headers=world.admin_headers,
                            json={"name": "Synthetic null department", "enabled": None})
    assert answer.status_code == 422
    with transaction(world.path) as uow:
        assert len(uow.departments.get_all()) == before
