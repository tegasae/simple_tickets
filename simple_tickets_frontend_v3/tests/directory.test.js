import assert from 'node:assert/strict';
import test from 'node:test';

import { createDirectoryApi } from '../src/api/resources/directory.js';
import { ApiError, createApi } from '../src/api/transport.js';
import {
  DIRECTORIES, canDirectory, canDirectoryAction, directoryFormValues, directoryLabel, directoryPayload,
} from '../src/features/admin/directoryModel.js';

const EMPLOYEE = {
  employee_id: 3, first_name: 'Ирина', last_name: 'Иванова', email: '', phone: '',
  login: 'fixture', enabled: true, enabled_login: false, roles: [4],
};

const CLIENT = { client_id: 11, name: 'Клиент', email: '', phone: '', description: '', address: 'Адрес', enabled: true };
const USER = { ...EMPLOYEE, client_id: 11 };
const ADMIN = { ...EMPLOYEE, job_title: 'Оператор', department_id: 7 };
const DEPARTMENT = { department_id: 7, name: 'Поддержка', enabled: true };
const ROLE = { role_id: 4, name: 'Доступ', description: '', permissions: ['ticket.view'], is_system_role: false };

test('directory collections and details use the exact FastAPI paths, preserving realm and identity', async () => {
  const calls = [];
  const signal = new AbortController().signal;
  const paths = [
    ['clients', '/admin/clients', CLIENT, 11, true],
    ['users', '/admin/users', USER, 3, true],
    ['admins', '/admin/admins', ADMIN, 3, true],
    ['departments', '/admin/departments', DEPARTMENT, 7, true],
    ['adminRoles', '/admin/roles/admin', ROLE, 4, false],
    ['userRoles', '/admin/roles/user', ROLE, 4, false],
  ];
  const responses = new Map();
  for (const [, path, record, id, trailingSlash] of paths) {
    const collection = trailingSlash ? `${path}/` : path;
    responses.set(collection, [record]);
    responses.set(`${path}/${id}`, record);
  }
  responses.set('/admin/roles/user/permissions', ['ticket.view', 'ticket.view.all']);
  const api = createDirectoryApi({
    get: async (path, options) => { calls.push([path, options]); return responses.get(path); },
  });
  for (const [resource, path, row, id, trailingSlash] of paths) {
    assert.deepEqual(await api.list(resource, { signal }), [row]);
    assert.deepEqual(await api.get(resource, id, { signal }), row);
    assert.deepEqual(calls.at(-2), [trailingSlash ? `${path}/` : path, { signal }]);
    assert.deepEqual(calls.at(-1), [`${path}/${id}`, { signal }]);
  }
  assert.deepEqual(await api.permissions('userRoles', { signal }), ['ticket.view', 'ticket.view.all']);
  await assert.rejects(api.permissions('clients'), { code: 'invalid-request' });
  responses.set('/admin/users/3', { ...USER, employee_id: 4 });
  await assert.rejects(api.get('users', 3), { code: 'invalid-response' });
  responses.set('/admin/admins/', [{ ...ADMIN, roles: ['4'] }]);
  await assert.rejects(api.list('admins'), { code: 'invalid-response' });
});

test('directory create uses an idempotency key and profile PUT preserves a complete typed body', async () => {
  const calls = [];
  const api = createDirectoryApi({
    mutate: async (path, options) => {
      calls.push([path, options]);
      return path.includes('/clients/') ? CLIENT : path.includes('/roles/') ? ROLE : ADMIN;
    },
  });
  const body = directoryPayload('clients', 'create', { name: 'Клиент' });
  await api.create('clients', body, { idempotencyKey: 'one-create' });
  assert.deepEqual(calls[0], ['/admin/clients/', {
    method: 'POST', json: body, idempotencyKey: 'one-create', expectedStatus: 201, signal: undefined,
  }]);
  const profile = directoryPayload('clients', 'update', { name: 'Новое имя' }, CLIENT);
  await api.update('clients', 11, profile);
  assert.deepEqual(calls[1], ['/admin/clients/11/contact', {
    method: 'PUT', json: { name: 'Новое имя', email: '', phone: '', address: 'Адрес', description: '' },
    expectedStatus: 200, signal: undefined,
  }]);
  const adminDraft = { job_title: 'Инженер', department_id: 41, password: 'fixture-password', roles: [8] };
  await api.update('admins', 3, directoryPayload('admins', 'update', adminDraft, ADMIN));
  assert.deepEqual(calls[2], ['/admin/admins/3', {
    method: 'PUT', json: {
      first_name: 'Ирина', last_name: 'Иванова', email: '', phone: '',
      job_title: 'Инженер', department_id: 7,
    }, expectedStatus: 200, signal: undefined,
  }]);
  await api.create('adminRoles', { name: 'Доступ', permissions: ['ticket.view'] }, { idempotencyKey: 'one-role' });
  assert.equal(calls.at(-1)[0], '/admin/roles/admin');
  await assert.rejects(api.update('admins', 3, { first_name: 'Sparse' }), { status: 422 });
  await assert.rejects(api.update('adminRoles', 4, { name: 'Unsupported' }), { code: 'invalid-request' });
  assert.equal(calls.length, 4);
});

test('account, department and role commands retain distinct methods and JSON shapes', async () => {
  const calls = [];
  const api = createDirectoryApi({
    mutate: async (path, options) => {
      calls.push([path, options]);
      return path.startsWith('/admin/users/') ? USER : ADMIN;
    },
  });
  await api.action('users', 3, 'attachAccount', { login: ' fixture ', password: 'Test$Pass123', enable_account: false });
  await api.action('users', 3, 'enableAccount');
  await api.action('users', 3, 'disableAccount');
  await api.action('admins', 3, 'changePassword', { password: 'Test$Next123' });
  await api.action('admins', 3, 'detachAccount');
  await api.action('admins', 3, 'changeDepartment', { department_id: 8 });
  await api.action('admins', 3, 'removeDepartment');
  await api.action('admins', 3, 'disable');
  await api.action('admins', 3, 'enable');
  await api.action('users', 3, 'grantRoles', { roles: [6, 6, 7] });
  await api.action('users', 3, 'revokeRoles', { roles: [4] });

  assert.deepEqual(calls.map(([path, request]) => [path, request.method, request.json]), [
    ['/admin/users/3/account', 'POST', { login: 'fixture', password: 'Test$Pass123', enable_account: false }],
    ['/admin/users/3/account/enable', 'PATCH', undefined],
    ['/admin/users/3/account/disable', 'PATCH', undefined],
    ['/admin/admins/3/password', 'PATCH', { password: 'Test$Next123' }],
    ['/admin/admins/3/account', 'DELETE', undefined],
    ['/admin/admins/3/department', 'PATCH', { department_id: 8 }],
    ['/admin/admins/3/department', 'DELETE', undefined],
    ['/admin/admins/3/disable', 'PATCH', undefined],
    ['/admin/admins/3/enable', 'PATCH', undefined],
    ['/admin/users/3/roles', 'POST', { roles: [6, 7] }],
    ['/admin/users/3/roles', 'DELETE', { roles: [4] }],
  ]);
  assert.equal(calls.every(([, options]) => options.expectedStatus === 200 && !Object.hasOwn(options, 'idempotencyKey')), true);
  await assert.rejects(api.action('clients', 11, 'grantRoles', { roles: [1] }), { code: 'invalid-request' });
  await assert.rejects(api.action('users', 3, 'revokeRoles', { roles: [0] }), { fields: ['roles'] });
  await assert.rejects(api.action('admins', 3, 'disable', { password: 'Test$Pass123' }), { code: 'invalid-request' });
  assert.equal(calls.length, 11);
});

test('remove expects a bodyless 204 and never retries a denial or unexpected success response', async () => {
  let count = 0;
  const api = createDirectoryApi({
    mutate: async (path, options) => {
      count += 1;
      assert.equal(path, '/admin/roles/admin/4');
      assert.deepEqual(options, { method: 'DELETE', expectedStatus: 204, signal: undefined });
      if (count === 1) throw new ApiError(400);
      return count === 2 ? ROLE : null;
    },
  });
  await assert.rejects(api.remove('adminRoles', 4), { status: 400 });
  assert.equal(count, 1);
  await assert.rejects(api.remove('adminRoles', 4), { code: 'invalid-response' });
  assert.equal(count, 2);
  assert.equal(await api.remove('adminRoles', 4), null);
  assert.equal(count, 3);
});

test('transport sends PUT, bodyless PATCH and role DELETE JSON with the expected HTTP result', async () => {
  const requests = [];
  const transport = createApi({
    fetchImpl: async (path, options) => {
      requests.push(new Request(new URL(path, 'https://fixture.invalid'), options));
      if (path === '/api/admin/users/3' && options.method === 'DELETE') return new Response(null, { status: 204 });
      return Response.json(USER);
    },
  });
  const api = createDirectoryApi({
    mutate: (path, options) => transport.mutate(path, { ...options, accessToken: 'fixture-access' }),
  });
  await api.action('users', 3, 'revokeRoles', { roles: [4] });
  await api.action('users', 3, 'enableAccount');
  await api.update('users', 3, directoryPayload('users', 'update', {}, USER));
  assert.equal(await api.remove('users', 3), null);

  assert.deepEqual(await requests[0].json(), { roles: [4] });
  assert.equal(requests[0].method, 'DELETE');
  assert.equal(requests[0].headers.get('Authorization'), 'Bearer fixture-access');
  assert.equal(requests[1].method, 'PATCH');
  assert.equal(await requests[1].text(), '');
  assert.equal(requests[1].headers.get('Content-Type'), null);
  assert.equal(requests[2].method, 'PUT');
  assert.deepEqual(await requests[2].json(), { first_name: 'Ирина', last_name: 'Иванова', email: '', phone: '' });
  assert.equal(requests[3].method, 'DELETE');
  assert.equal(await requests[3].text(), '');
});

test('metadata separates read, profile, role assignment, and activation permission branches', () => {
  assert.equal(canDirectory('clients', 'read', ['client.create']), false);
  assert.equal(canDirectory('clients', 'create', ['client.create']), true);
  assert.equal(canDirectory('clients', 'create', ['client.decision']), true);
  assert.equal(canDirectory('clients', 'update', ['client.decision']), false);
  assert.equal(canDirectoryAction('clients', 'disable', ['client.operation']), false);
  assert.equal(canDirectoryAction('clients', 'disable', ['client.decision']), true);
  assert.equal(canDirectoryAction('users', 'attachAccount', ['user.view']), false);
  assert.equal(canDirectoryAction('users', 'attachAccount', ['user.operation']), true);
  assert.equal(canDirectoryAction('users', 'grantRoles', ['user.operation']), false);
  assert.equal(canDirectoryAction('users', 'grantRoles', ['role_user.assign']), true);
  assert.equal(canDirectoryAction('admins', 'revokeRoles', ['role_user.assign']), false);
  assert.equal(canDirectoryAction('admins', 'revokeRoles', ['role.assign']), true);
  assert.equal(canDirectoryAction('admins', 'changeDepartment', ['admin.operation']), true);
  assert.equal(canDirectoryAction('users', 'changeDepartment', ['user.operation']), false);
  assert.equal(canDirectory('adminRoles', 'read', ['role_user.assign']), false);
  assert.equal(canDirectory('adminRoles', 'read', ['role.assign']), true);
  assert.equal(canDirectory('adminRoles', 'update', ['role.assign']), false);
  assert.equal(canDirectory('userRoles', 'remove', ['role_user.assign']), true);
  assert.deepEqual(DIRECTORIES.adminRoles.fields.update, []);
});

test('directory forms preserve field types and never put roles, password or client changes into a profile PUT', () => {
  const draft = directoryFormValues('users', 'create');
  assert.equal(draft.client_id, 0);
  assert.throws(() => directoryPayload('users', 'create', draft), { fields: ['client_id', 'first_name'] });
  const create = directoryPayload('users', 'create', { first_name: 'Ирина', client_id: '11', roles: [4] });
  assert.equal(create.client_id, 11);
  assert.equal(Object.hasOwn(create, 'roles'), false);
  assert.deepEqual(directoryPayload('users', 'update', {
    first_name: 'Имя', client_id: 8, password: 'test-only',
  }, USER), { first_name: 'Имя', last_name: 'Иванова', email: '', phone: '' });
  assert.throws(() => directoryPayload('admins', 'update', { ...ADMIN }), { code: 'invalid-request' });
  assert.deepEqual(directoryPayload('adminRoles', 'create', {
    name: 'Роль', permissions: ['ticket.view', 'ticket.view'],
  }), { name: 'Роль', description: '', permissions: ['ticket.view'], is_system_role: false });
  assert.equal(directoryLabel('admins', ADMIN), 'Ирина Иванова');
  assert.equal(directoryLabel('clients', CLIENT), 'Клиент');
});
