import pytest

from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import AdminRole, Role, RoleStore, UserRole


def test_role_checks_permission():
    role = Role(role_id=1, name="admin", permissions=frozenset({AdminPermission.TICKET_OPERATION}))

    assert role.has_permission(AdminPermission.TICKET_OPERATION) is True



#@pytest.mark.xfail(reason="AdminRole/UserRole subclasses are not dataclasses, so __post_init__ is not called in current code.")
def test_admin_role_rejects_user_permission():
    with pytest.raises(ValueError):
        AdminRole(role_id=1, name="bad", permissions=frozenset({UserPermission.TICKET_OPERATION}))


#@pytest.mark.xfail(reason="AdminRole/UserRole subclasses are not dataclasses, so __post_init__ is not called in current code.")
def test_user_role_rejects_admin_permission():
    with pytest.raises(ValueError):
        UserRole(role_id=1, name="bad", permissions=frozenset({AdminPermission.TICKET_OPERATION}))


def test_role_store_put_check_delete():
    role = Role(role_id=1, name="admin")
    store = RoleStore()

    store.put_role(role)
    assert store.check_role(role) is True

    store.delete_role(role)
    assert store.check_role(role) is False
