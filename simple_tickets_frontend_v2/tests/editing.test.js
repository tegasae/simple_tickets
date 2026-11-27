import assert from 'node:assert/strict';
import test from 'node:test';

import { createReferencesApi } from '../src/api/resources/references.js';
import { createTicketsApi } from '../src/api/resources/tickets.js';
import { ApiError, createApi } from '../src/api/transport.js';
import { createSession } from '../src/app/session/session.js';
import { editableFields, saveTicketFields } from '../src/features/tickets/editing.js';

const TICKET_ID = 12;
const TICKET_PATH = `/admin/tickets/${TICKET_ID}`;
const DATE = '2027-01-15T17:30:00Z';

function ticket(overrides = {}) {
  return {
    ticket_id: TICKET_ID, client_id: 2, user_id: 0, contact_user_id: 0, user_ticket_id: 0,
    department_id: 2, current_executor_id: 0, last_executor_id: 0,
    text_of_ticket: 'User report', description: 'Original',
    date_created: DATE, date_finished: null, planned_at: null,
    remote_work_recommended: false, is_closed: false, urgency: 'normal',
    statuses: [], comments: [], ...overrides,
  };
}

test('ticket writes use exact URLs, body keys and the explicit POST idempotency key', async () => {
  const writes = [];
  const calls = createTicketsApi({
    mutate: async (path, { method, json, idempotencyKey }) => {
      writes.push({ path, method, json, idempotencyKey });
      return ticket();
    },
  });
  const intent = { client_id: 2, text_of_ticket: 'Create me', contact_user_id: 0 };
  await calls.create(intent, { idempotencyKey: 'create-key' });
  await calls.addComment(TICKET_ID, 'Comment', { idempotencyKey: 'comment-key' });
  await calls.updateField(TICKET_ID, 'description', '');
  await calls.updateField(TICKET_ID, 'contact_user_id', 0);
  await calls.updateField(TICKET_ID, 'department_id', 0);
  await calls.updateField(TICKET_ID, 'urgency', 'maintenance');
  await calls.updateField(TICKET_ID, 'planned_at', DATE);
  await calls.updateField(TICKET_ID, 'planned_at', null);
  await calls.updateField(TICKET_ID, 'remote_work_recommended', false);
  assert.deepEqual(writes, [
    { path: '/admin/tickets/', method: 'POST', json: intent, idempotencyKey: 'create-key' },
    { path: `${TICKET_PATH}/comments`, method: 'POST', json: { comment: 'Comment' }, idempotencyKey: 'comment-key' },
    { path: `${TICKET_PATH}/description`, method: 'PATCH', json: { description: '' }, idempotencyKey: undefined },
    { path: `${TICKET_PATH}/contact-user`, method: 'PATCH', json: { contact_user_id: 0 }, idempotencyKey: undefined },
    { path: `${TICKET_PATH}/department`, method: 'PATCH', json: { department_id: 0 }, idempotencyKey: undefined },
    { path: `${TICKET_PATH}/urgency`, method: 'PATCH', json: { urgency: 'maintenance' }, idempotencyKey: undefined },
    { path: `${TICKET_PATH}/schedule`, method: 'PATCH', json: { planned_at: DATE }, idempotencyKey: undefined },
    { path: `${TICKET_PATH}/schedule`, method: 'DELETE', json: undefined, idempotencyKey: undefined },
    { path: `${TICKET_PATH}/remote-work-recommended`, method: 'PATCH', json: { remote_work_recommended: false }, idempotencyKey: undefined },
  ]);
  await assert.rejects(calls.updateField(TICKET_ID, 'text_of_ticket', 'new title'), {
    code: 'invalid-request',
  });
  await assert.rejects(calls.updateField(TICKET_ID, 'planned_at', '2027-01-15T17:30'), {
    status: 422, fields: ['planned_at'],
  });
  await assert.rejects(calls.addComment(TICKET_ID, '  '), { status: 422, fields: ['comment'] });
  assert.equal(writes.length, 9);
});

test('write transport binds token and idempotency key and exposes only safe 422 field names', async () => {
  const requests = [];
  const api = createApi({
    fetchImpl: async (path, options) => {
      requests.push(new Request(new URL(path, 'https://fixture.invalid'), options));
      return Response.json({ detail: [
        { loc: ['body', 'text_of_ticket'], msg: 'private fixture diagnostic', input: 'private input' },
        { loc: ['body', 'text_of_ticket'], type: 'duplicate' },
        { loc: ['body', '<external value>'] },
        { loc: ['path', 'ticket_id'] },
      ] }, { status: 422 });
    },
  });
  await assert.rejects(api.mutate('/admin/tickets/', {
    method: 'POST', json: { text_of_ticket: 'x' }, idempotencyKey: 'retry-key', accessToken: 'access',
  }), (error) => {
    assert.equal(error.status, 422);
    assert.deepEqual(error.fields, ['text_of_ticket']);
    assert.doesNotMatch(String(error), /private/);
    return true;
  });
  const [request] = requests;
  assert.equal(request.url, 'https://fixture.invalid/api/admin/tickets/');
  assert.equal(request.headers.get('Authorization'), 'Bearer access');
  assert.equal(request.headers.get('Idempotency-Key'), 'retry-key');
  assert.equal(request.redirect, 'error');
  assert.deepEqual(await request.json(), { text_of_ticket: 'x' });
  await assert.rejects(api.mutate('/admin/tickets/', {
    method: 'POST', json: {}, idempotencyKey: 'not a key', accessToken: 'access',
  }), { code: 'invalid-request' });
  assert.equal(requests.length, 1);
});

test('401 and timeouts in writes are each sent once without refreshing or withdrawing ticket view', async () => {
  let writes = 0;
  const session = createSession({
    storage: null,
    api: {
      login: async () => ({ access_token: 'access', refresh_token: 'refresh' }),
      get: async () => ({ permissions: ['ticket.view', 'ticket.operation'] }),
      refresh: async () => assert.fail('A write must not trigger token refresh'),
      mutate: async () => {
        writes += 1;
        if (writes === 1) throw new ApiError(401);
        if (writes === 2) throw new ApiError(0, 'timeout');
        throw new ApiError(403);
      },
    },
  });
  await session.login('operator', 'fixture');
  const write = () => session.mutate(`${TICKET_PATH}/description`, {
    method: 'PATCH', json: { description: 'New' },
  });
  await assert.rejects(write(), { status: 401 });
  assert.equal(writes, 1);
  await assert.rejects(write(), { code: 'timeout' });
  assert.equal(writes, 2);
  await assert.rejects(write(), { status: 403 });
  assert.equal(writes, 3);
  assert.ok(session.getSnapshot().permissions.includes('ticket.view'));
});

test('related reads preserve disabled records and refuse an out-of-scope client list', async () => {
  const client = { client_id: 2, name: 'Client', email: '', phone: '', address: '', description: '', enabled: false };
  const user = {
    employee_id: 3, client_id: 2, first_name: 'Member', last_name: '', email: '', phone: '',
    login: '', enabled: false, enabled_login: false,
  };
  const department = { department_id: 4, name: 'Former department', enabled: false };
  const paths = new Map([
    ['/admin/clients/', [client]],
    ['/admin/clients/2', client],
    ['/admin/users/client/2', [user]],
    ['/admin/users/3', user],
    ['/admin/departments/', [department]],
  ]);
  const references = createReferencesApi({ get: async path => paths.get(path) });
  assert.deepEqual(await references.clients(), [client]);
  assert.deepEqual(await references.client(2), client);
  assert.deepEqual(await references.users(2), [user]);
  assert.deepEqual(await references.user(3), user);
  assert.deepEqual(await references.departments(), [department]);
  paths.set('/admin/users/client/2', [{ ...user, client_id: 4 }]);
  await assert.rejects(references.users(2), { code: 'invalid-response' });
});

test('pre-read refuses all writes when a dirty field changed or reading is unavailable', async () => {
  const baseline = editableFields(ticket());
  let reads = 0;
  const api = {
    get: async () => {
      reads += 1;
      return ticket({ department_id: 7 });
    },
    updateField: async () => assert.fail('No field may be written after a pre-read conflict'),
  };
  const draft = { description: 'Mine', department_id: 3 };
  const saved = await saveTicketFields(api, TICKET_ID, baseline, draft);
  assert.equal(saved.status, 'conflict');
  assert.deepEqual(saved.conflicts, ['department_id']);
  assert.deepEqual(saved.remaining, ['description', 'department_id']);
  assert.equal(saved.ticket.department_id, 7);
  assert.equal(reads, 1);

  const denied = await saveTicketFields(api, TICKET_ID, baseline, draft, { canRead: false });
  assert.equal(denied.status, 'failed');
  assert.equal(denied.error.code, 'preflight-read-required');
  assert.equal(reads, 1);
});

test('save canonicalizes user input and detects intervening edits to later fields', async () => {
  const writes = [];
  const api = {
    get: async () => ticket(),
    updateField: async (id, field, value) => {
      writes.push([id, field, value]);
      return ticket({ description: 'First edit', urgency: 'maintenance' });
    },
  };
  const baseline = editableFields(ticket());
  const outcome = await saveTicketFields(api, TICKET_ID, baseline, {
    description: ' First edit  ', urgency: 'urgent', planned_at: DATE,
  });
  assert.equal(outcome.status, 'partial');
  assert.deepEqual(writes, [[TICKET_ID, 'description', 'First edit']]);
  assert.deepEqual(outcome.applied, ['description']);
  assert.deepEqual(outcome.conflicts, ['urgency']);
  assert.deepEqual(outcome.remaining, ['urgency', 'planned_at']);
  assert.equal(outcome.ticket.urgency, 'maintenance');
});

test('unknown PATCH is checked once by value and never replayed or followed by additional writes', async () => {
  const writes = [];
  let reads = 0;
  const api = {
    get: async () => {
      reads += 1;
      return reads === 1 ? ticket() : ticket({ description: 'Already visible' });
    },
    updateField: async (id, field) => {
      writes.push([id, field]);
      throw new ApiError(0, 'timeout');
    },
  };
  const outcome = await saveTicketFields(api, TICKET_ID, editableFields(ticket()), {
    description: 'Already visible', urgency: 'urgent',
  });
  assert.equal(outcome.status, 'unconfirmed');
  assert.equal(outcome.uncertainField, 'description');
  assert.equal(outcome.error.code, 'timeout');
  assert.equal(reads, 2);
  assert.deepEqual(writes, [[TICKET_ID, 'description']]);
  assert.deepEqual(outcome.applied, []);
  assert.deepEqual(outcome.matched, ['description']);
  assert.deepEqual(outcome.remaining, ['urgency']);
});

test('editing preserves a valid immutable baseline and recognizes equal UTC instants', async () => {
  const baseline = editableFields(ticket({ planned_at: DATE }));
  const draft = { description: 'Original', planned_at: '2027-01-15T18:30:00+01:00' };
  const api = { get: async () => assert.fail('No pre-read is needed when fields are unchanged') };
  const outcome = await saveTicketFields(api, TICKET_ID, baseline, draft);
  assert.equal(outcome.status, 'unchanged');
  assert.equal(draft.planned_at, '2027-01-15T18:30:00+01:00');
  assert.equal(baseline.planned_at, '2027-01-15T17:30:00.000Z');
});

test('a late PATCH from an earlier session cannot continue an edit under a different Admin', async () => {
  let completeWrite;
  let notifyWrite;
  const firstWrite = new Promise((resolve) => { completeWrite = resolve; });
  const firstWriteStarted = new Promise((resolve) => { notifyWrite = resolve; });
  const writes = [];
  const session = createSession({
    storage: null,
    api: {
      login: async username => ({ access_token: username, refresh_token: `refresh-${username}` }),
      logout: async () => {},
      get: async path => path === '/admin/admins/permissions'
        ? { permissions: ['ticket.view', 'ticket.operation'] } : ticket(),
      mutate: async (path, { accessToken }) => {
        writes.push([path, accessToken]);
        notifyWrite();
        return firstWrite;
      },
    },
  });
  const api = createTicketsApi(session);
  assert.equal(await session.login('earlier-admin', 'fixture'), true);
  const discarded = assert.rejects(saveTicketFields(api, TICKET_ID, editableFields(ticket()), {
    description: 'First write', urgency: 'urgent',
  }), (error) => error?.name === 'AbortError' || error?.code === 'stale-session');
  await firstWriteStarted;
  await session.logout();
  assert.equal(await session.login('current-admin', 'fixture'), true);
  completeWrite(ticket({ description: 'First write' }));
  await discarded;
  assert.deepEqual(writes, [[`${TICKET_PATH}/description`, 'earlier-admin']]);
});
