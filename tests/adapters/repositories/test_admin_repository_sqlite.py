from src.adapters.repositories.admin import AdminRepositorySQLite
from src.domain.employee import Admin


def test_admin_repository_save_get_update_roles_and_account(sqlite_schema):
    repo = AdminRepositorySQLite(sqlite_schema)
    admin = Admin.create(
        employee_id=0,
        first_name="John",
        last_name="Admin",
        login="john-admin",
        password="Secret123!",
        job_title="Engineer",
        roles=frozenset({1, 2}),
    )

    saved = repo.save(admin)
    loaded = repo.get(saved.employee_id)

    assert saved.employee_id > 0
    assert loaded.job_title == "Engineer"
    assert loaded.role_ids() == frozenset({1, 2})
    assert str(loaded.account.login) == "john-admin"

    loaded.update(job_title="Senior Engineer", first_name="John", last_name="Admin")
    updated = repo.save(loaded)
    assert updated.version == 1
    assert repo.get(updated.employee_id).job_title == "Senior Engineer"
