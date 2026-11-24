"""Admin refresh is permanently revoked by another authorised Admin."""
import secrets

import pytest


@pytest.mark.parametrize('world', ['memory', 'sqlite'], indirect=True)
@pytest.mark.parametrize('event', ['password', 'employee_disable_enable'])
def test_admin_lifecycle_permanently_rejects_old_refresh(world, event):
    login = 'target' + secrets.token_hex(8)
    password = 'Aa1!' + secrets.token_hex(12)
    created = world.api.post('/admin/admins/', headers=world.admin_headers, json={
        'first_name': 'Synthetic target operator', 'login': login, 'password': password,
    })
    assert created.status_code == 201
    target_id = created.json()['employee_id']
    assert target_id != world.admin_id
    authenticated = world.api.post('/auth/admin/login',
                                    data={'username': login, 'password': password})
    assert authenticated.status_code == 200
    old_refresh = authenticated.json()['refresh_token']
    root = f'/admin/admins/{target_id}'
    if event == 'password':
        response = world.api.patch(root + '/password', headers=world.admin_headers,
                                  json={'password': 'Aa1!' + secrets.token_hex(12)})
        assert response.status_code == 200
    else:
        disabled = world.api.patch(root + '/disable', headers=world.admin_headers)
        assert disabled.status_code == 200
        while_disabled = world.api.post('/auth/admin/refresh',
                                         json={'refresh_token': old_refresh})
        assert while_disabled.status_code == 401
        enabled = world.api.patch(root + '/enable', headers=world.admin_headers)
        assert enabled.status_code == 200
    refreshed = world.api.post('/auth/admin/refresh', json={'refresh_token': old_refresh})
    assert refreshed.status_code == 401
