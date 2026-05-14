from src.adapters.repositories.role_repository import RoleRepositorySQLite
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role


def test_role_repository_add_get_all_delete_admin_role(sqlite_schema):
    repo = RoleRepositorySQLite(conn=sqlite_schema, permission_cls=AdminPermission, is_admin=True)
    role = Role(
        role_id=0,
        name="ticket manager",
        permissions=frozenset({AdminPermission.CREATE_TICKET, AdminPermission.UPDATE_TICKET}),
        description="Can manage tickets",
    )

    saved = repo.add(role)
    loaded = repo.get(saved.role_id)

    assert saved.role_id > 0
    assert loaded.name == "ticket manager"
    assert loaded.has_permission(AdminPermission.CREATE_TICKET)
    assert any(r.role_id == saved.role_id and r.name == saved.name for r in repo.all())

    repo.delete(saved.role_id)
    assert saved.role_id not in [r.role_id for r in repo.all()]


def test_role_repository_separates_admin_and_user_realms(sqlite_schema):
    admin_repo = RoleRepositorySQLite(conn=sqlite_schema, permission_cls=AdminPermission, is_admin=True)
    user_repo = RoleRepositorySQLite(conn=sqlite_schema, permission_cls=UserPermission, is_admin=False)

    admin_repo.add(Role(role_id=0, name="admin role", permissions=frozenset({AdminPermission.CREATE_USER})))
    user_repo.add(Role(role_id=0, name="user role", permissions=frozenset({UserPermission.CREATE_TICKET})))

    assert [r.name for r in admin_repo.all()] == ["admin role"]
    assert [r.name for r in user_repo.all()] == ["user role"]
