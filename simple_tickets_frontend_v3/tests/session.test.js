import assert from 'node:assert/strict';
import test from 'node:test';

import { createTicketsApi } from '../src/api/resources/tickets.js';
import { ApiError, createApi } from '../src/api/transport.js';
import { createSession, REFRESH_STORAGE_KEY } from '../src/app/session/session.js';

const PERMISSIONS_PATH = '/admin/admins/permissions';
const TICKETS_PATH = '/admin/tickets/';
const TICKET_PATH = '/admin/tickets/42';
const PERMISSIONS = { permissions: ['ticket.view'] };

function tokenPair(label, actorId = 17) {
  const payload = Buffer.from(JSON.stringify({ sub: String(actorId), subject_type: 'admin', label }));
  return {
    access_token: `header.${payload.toString('base64url')}.signature`,
    refresh_token: `refresh-${label}`,
    token_type: 'bearer',
    expires_in: 300,
    scope: '',
  };
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function sessionFixture(api, storedRefresh) {
  const values = new Map();
  if (storedRefresh) values.set(REFRESH_STORAGE_KEY, storedRefresh);
  const storage = {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: key => values.delete(key),
  };
  return { session: createSession({ api, storage }), values };
}

function httpError(status) {
  return new ApiError(status, 'http');
}

test('transport sends Admin login, rotating refresh, logout and Bearer with their wire formats', async () => {
  const calls = [];
  const api = createApi({
    fetchImpl: async (url, options) => {
      calls.push(new Request(new URL(url, 'https://fixture.invalid'), options));
      if (url.endsWith('/login') || url.endsWith('/refresh')) return Response.json(tokenPair('transport'));
      if (url.endsWith('/logout')) return Response.json({ message: 'Logged out successfully' });
      return Response.json([]);
    },
  });

  await api.login('имя & тест', 'test+password!');
  await api.refresh('old-refresh');
  await api.get(TICKETS_PATH, { accessToken: 'fixture-access' });
  await api.logout('new-refresh');

  assert.deepEqual(calls.map(({ url, method }) => [new URL(url).pathname, method]), [
    ['/api/auth/admin/login', 'POST'],
    ['/api/auth/admin/refresh', 'POST'],
    [`/api${TICKETS_PATH}`, 'GET'],
    ['/api/auth/admin/logout', 'POST'],
  ]);
  const loginRequest = calls[0];
  assert.match(loginRequest.headers.get('content-type'), /^application\/x-www-form-urlencoded/);
  assert.deepEqual(Object.fromEntries(await loginRequest.formData()), {
    username: 'имя & тест',
    password: 'test+password!',
  });
  assert.deepEqual(await calls[1].json(), { refresh_token: 'old-refresh' });
  assert.equal(calls[2].headers.get('authorization'), 'Bearer fixture-access');
  assert.equal(calls[2].redirect, 'error');
  assert.equal(calls[2].credentials, 'omit');
  assert.deepEqual(await calls[3].json(), { refresh_token: 'new-refresh' });
  await assert.rejects(async () => api.get('https://example.invalid/admin/tickets/', { accessToken: 'fixture-access' }));
  assert.equal(calls.length, 4, 'Absolute external URL must not reach fetch');
});

test('transport maps HTTP, network and invalid success responses without exposing the body', async () => {
  const privateText = 'private fixture diagnostic';
  const api = createApi({ fetchImpl: async () => new Response(privateText, { status: 503 }) });
  const internalError = createApi({ fetchImpl: async () => Response.json({ detail: privateText }, { status: 500 }) });
  const badGateway = createApi({ fetchImpl: async () => new Response(`<html>${privateText}</html>`, {
    status: 502, headers: { 'Content-Type': 'text/html' },
  }) });
  const brokenResponse = createApi({ fetchImpl: async () => new Response(privateText, { status: 200 }) });
  const offlineApi = createApi({ fetchImpl: async () => { throw new Error(privateText); } });

  const expected = [
    [api, 503, 'unavailable'],
    [internalError, 500, 'http'],
    [badGateway, 502, 'http'],
    [brokenResponse, 200, 'invalid-response'],
    [offlineApi, 0, 'network'],
  ];
  for (const [client, status, code] of expected) {
    await assert.rejects(client.get(TICKET_PATH, { accessToken: 'fixture-access' }), error => {
      assert.equal(error.status, status);
      assert.equal(error.code, code);
      assert.doesNotMatch(String(error), /private fixture diagnostic/);
      return true;
    });
  }
});

test('transport bounds both receipt of headers and JSON while preserving caller cancellation', async (t) => {
  const keepAlive = setTimeout(() => {}, 1_000);
  t.after(() => clearTimeout(keepAlive));
  const hanging = deferred();
  let headersSignal;
  const waitingForHeaders = createApi({
    timeoutMs: 20,
    fetchImpl: (url, { signal }) => {
      headersSignal = signal;
      return hanging.promise;
    },
  });
  await assert.rejects(waitingForHeaders.get(TICKET_PATH, { accessToken: 'fixture-access' }), {
    status: 0, code: 'timeout',
  });
  assert.equal(headersSignal.reason.name, 'TimeoutError');

  let jsonStarted = false;
  const waitingForBody = createApi({
    timeoutMs: 20,
    fetchImpl: async () => ({
      ok: true,
      status: 200,
      json() {
        jsonStarted = true;
        return hanging.promise;
      },
    }),
  });
  await assert.rejects(waitingForBody.get(TICKET_PATH, { accessToken: 'fixture-access' }), {
    status: 0, code: 'timeout',
  });
  assert.equal(jsonStarted, true);

  const abort = new AbortController();
  const sent = deferred();
  const abortable = createApi({
    fetchImpl: (url, { signal }) => {
      sent.resolve(signal);
      return hanging.promise;
    },
  });
  const cancelled = assert.rejects(abortable.get(TICKET_PATH, {
    accessToken: 'fixture-access',
    signal: abort.signal,
  }), error => error === abort.signal.reason && error.name === 'AbortError');
  const signal = await sent.promise;
  abort.abort();
  await cancelled;
  assert.equal(signal.aborted, true);
});

test('ticket API accepts valid references and nullable dates and rejects unsafe response fields', async () => {
  const date = '2026-11-26T14:00:00Z';
  const comment = { id: 3, actor_id: 17, date_created: date, comment: 'A comment' };
  const status = {
    id: 2, actor_id: 17, executor_id: 0, date_created: date, status: 'created', comment: '',
    actual_started_at: null, actual_finished_at: null, work_is_remote: null,
  };
  const valid = {
    ticket_id: 42, client_id: 2, user_id: 0, contact_user_id: 0, user_ticket_id: 0,
    department_id: 3, current_executor_id: 0, last_executor_id: 0,
    text_of_ticket: 'Ticket title', description: 'Ticket description',
    date_created: date, date_finished: null, planned_at: null,
    remote_work_recommended: false, is_closed: false, urgency: 'normal',
    statuses: [status], comments: [comment],
  };
  let ticket = valid;
  const api = createTicketsApi({
    get: async path => path === TICKET_PATH ? ticket : [ticket],
  });

  assert.deepEqual(await api.list(), [valid]);
  assert.deepEqual(await api.get(valid.ticket_id), valid);
  ticket = { ...valid, statuses: [], comments: [] };
  assert.deepEqual(await api.get(valid.ticket_id), ticket);
  ticket = { ...valid, statuses: [{ ...status, date_created: null }] };
  assert.deepEqual(await api.get(valid.ticket_id), ticket);

  const malformed = [
    { text_of_ticket: { unexpected: 'object' } },
    { description: [] },
    { client_id: '2' },
    { current_executor_id: -1 },
    { planned_at: 'invalid date' },
    { urgency: { value: 'normal' } },
    { remote_work_recommended: 'false' },
    { statuses: [{ ...status, status: 1 }] },
    { statuses: [{ ...status, id: { invalid: true } }] },
    { comments: [{ ...comment, comment: { value: 'not a string' } }] },
    { comments: [{ ...comment, date_created: 42 }] },
  ];
  for (const fields of malformed) {
    ticket = { ...valid, ...fields };
    await assert.rejects(api.get(valid.ticket_id), { code: 'invalid-response' });
    await assert.rejects(api.list(), { code: 'invalid-response' });
  }
});

test('reload restores the current Admin, replaces its stored refresh and checks actual permissions', async () => {
  const rotated = tokenPair('rotated');
  const { session, values } = sessionFixture({
    refresh: async refresh => {
      assert.equal(refresh, 'refresh-before-reload');
      return rotated;
    },
    get: async (path, { accessToken }) => {
      assert.equal(path, PERMISSIONS_PATH);
      assert.equal(accessToken, rotated.access_token);
      return PERMISSIONS;
    },
  }, 'refresh-before-reload');

  assert.equal(session.getSnapshot().phase, 'restoring');
  assert.equal(await session.restore(), true);
  assert.equal(session.getSnapshot().phase, 'authenticated');
  assert.equal(session.getSnapshot().actorId, 17);
  assert.deepEqual(session.getSnapshot().permissions, PERMISSIONS.permissions);
  assert.deepEqual([...values], [[REFRESH_STORAGE_KEY, rotated.refresh_token]]);
});

test('overlapping 401s share a refresh while a later token expiry can rotate again', async () => {
  const original = tokenPair('original');
  const rotated = tokenPair('rotated');
  const later = tokenPair('later');
  const refreshStarted = deferred();
  const pendingRefresh = deferred();
  const refreshCalls = [];
  const reads = [];
  const { session } = sessionFixture({
    login: async () => original,
    refresh: async refresh => {
      refreshCalls.push(refresh);
      if (refresh === original.refresh_token) {
        refreshStarted.resolve();
        return pendingRefresh.promise;
      }
      return later;
    },
    get: async (path, { accessToken }) => {
      if (path === PERMISSIONS_PATH) return PERMISSIONS;
      reads.push({ path, accessToken });
      if (accessToken === original.access_token || (path === '/admin/tickets/open' && accessToken === rotated.access_token)) {
        throw httpError(401);
      }
      return path;
    },
  });

  assert.equal(await session.login('operator', 'test-password'), true);
  const readsInFlight = Promise.all([session.get(TICKETS_PATH), session.get(TICKET_PATH)]);
  await refreshStarted.promise;
  pendingRefresh.resolve(rotated);
  assert.deepEqual(await readsInFlight, [TICKETS_PATH, TICKET_PATH]);
  assert.deepEqual(refreshCalls, [original.refresh_token]);
  for (const path of [TICKETS_PATH, TICKET_PATH]) {
    assert.deepEqual(reads.filter(read => read.path === path).map(read => read.accessToken), [original.access_token, rotated.access_token]);
  }
  assert.equal(await session.get('/admin/tickets/open'), '/admin/tickets/open');
  assert.deepEqual(refreshCalls, [original.refresh_token, rotated.refresh_token]);
});

test('late 401 for a replaced access token uses the already rotated token', async () => {
  const original = tokenPair('original');
  const rotated = tokenPair('rotated');
  const oldRead = deferred();
  const refreshCalls = [];
  const { session } = sessionFixture({
    login: async () => original,
    refresh: async refresh => {
      refreshCalls.push(refresh);
      return rotated;
    },
    get: async (path, { accessToken }) => {
      if (path === PERMISSIONS_PATH) return PERMISSIONS;
      if (accessToken === rotated.access_token) return path;
      if (path === TICKET_PATH) return oldRead.promise;
      throw httpError(401);
    },
  });

  assert.equal(await session.login('operator', 'test-password'), true);
  const lateResult = session.get(TICKET_PATH);
  assert.equal(await session.get(TICKETS_PATH), TICKETS_PATH);
  oldRead.reject(httpError(401));
  assert.equal(await lateResult, TICKET_PATH);
  assert.deepEqual(refreshCalls, [original.refresh_token]);
});

test('a protected read still returning 401 after refresh is not retried again', async () => {
  let refreshes = 0;
  let reads = 0;
  const { session, values } = sessionFixture({
    login: async () => tokenPair('original'),
    refresh: async () => {
      refreshes += 1;
      assert.equal(refreshes, 1, 'A single request cannot rotate repeatedly');
      return tokenPair('rotated');
    },
    logout: async () => {},
    get: async path => {
      if (path === PERMISSIONS_PATH) return PERMISSIONS;
      reads += 1;
      throw httpError(401);
    },
  });

  assert.equal(await session.login('operator', 'test-password'), true);
  await assert.rejects(session.get(TICKET_PATH));
  assert.equal(refreshes, 1);
  assert.equal(reads, 2);
  assert.equal(session.getSnapshot().phase, 'anonymous');
  assert.equal(session.getSnapshot().error.status, 401);
  assert.equal(values.has(REFRESH_STORAGE_KEY), false);
});

test('403 keeps the session, requires explicit recheck and never refreshes credentials by itself', async () => {
  let refreshes = 0;
  let permissionReads = 0;
  const { session } = sessionFixture({
    login: async () => tokenPair('first'),
    refresh: async () => { refreshes += 1; },
    get: async path => {
      if (path === PERMISSIONS_PATH) {
        permissionReads += 1;
        return permissionReads === 1 ? PERMISSIONS : { permissions: [] };
      }
      throw httpError(403);
    },
  });

  assert.equal(await session.login('operator', 'test-password'), true);
  await assert.rejects(session.get(TICKET_PATH), { status: 403 });
  assert.equal(refreshes, 0);
  assert.equal(permissionReads, 1);
  assert.equal(await session.reloadPermissions(), true);
  assert.equal(permissionReads, 2);
  assert.equal(session.getSnapshot().phase, 'authenticated');
  assert.deepEqual(session.getSnapshot().permissions, []);
});

test('ticket 403 withdraws access immediately and disarms earlier reads and failed rechecks', async () => {
  const granted = { permissions: ['ticket.view', 'client.view'] };
  const olderPermissions = deferred();
  const newerPermissions = deferred();
  const newerPermissionsStarted = deferred();
  const earlierTicketRead = deferred();
  let permissionReads = 0;
  let ticketReads = 0;
  const { session, values } = sessionFixture({
    login: async () => tokenPair('first'),
    refresh: async () => assert.fail('Read denial cannot trigger refresh'),
    get: async path => {
      if (path === PERMISSIONS_PATH) {
        permissionReads += 1;
        if (permissionReads === 2) return olderPermissions.promise;
        if (permissionReads === 3) {
          newerPermissionsStarted.resolve();
          return newerPermissions.promise;
        }
        return granted;
      }
      ticketReads += 1;
      if (path === TICKETS_PATH) return earlierTicketRead.promise;
      throw httpError(403);
    },
  });

  assert.equal(await session.login('operator', 'test-password'), true);
  const oldCheck = session.reloadPermissions();
  const oldData = assert.rejects(session.get(TICKETS_PATH), { code: 'stale-permissions' });
  const denied = assert.rejects(session.get(TICKET_PATH), { status: 403 });
  await denied;
  const retry = session.reloadPermissions();
  await newerPermissionsStarted.promise;

  assert.equal(session.getSnapshot().phase, 'authenticated');
  assert.deepEqual(session.getSnapshot().permissions, ['client.view']);
  assert.equal(values.get(REFRESH_STORAGE_KEY), 'refresh-first');
  olderPermissions.resolve(granted);
  assert.equal(await oldCheck, false);
  earlierTicketRead.resolve([{ ticket_id: 42 }]);
  await oldData;
  assert.deepEqual(session.getSnapshot().permissions, ['client.view']);

  newerPermissions.reject(httpError(503));
  assert.equal(await retry, false);
  assert.deepEqual(session.getSnapshot().permissions, ['client.view']);
  assert.equal(session.getSnapshot().error.status, 503);
  await assert.rejects(session.get(TICKET_PATH), { status: 403 });
  assert.equal(ticketReads, 2, 'Do not fetch protected data with a withdrawn grant');

  assert.equal(await session.reloadPermissions(), true);
  assert.deepEqual(session.getSnapshot().permissions, granted.permissions);
  assert.equal(session.getSnapshot().error, null);
});

test('a denial outside tickets keeps unrelated ticket rights when permissions cannot be rechecked', async () => {
  let permissionReads = 0;
  const { session } = sessionFixture({
    login: async () => tokenPair('first'),
    get: async path => {
      if (path !== PERMISSIONS_PATH) throw httpError(403);
      if (permissionReads++) throw httpError(503);
      return PERMISSIONS;
    },
  });
  assert.equal(await session.login('operator', 'test-password'), true);
  await assert.rejects(session.get('/admin/clients/'), { status: 403 });
  assert.deepEqual(session.getSnapshot().permissions, PERMISSIONS.permissions);
});

test('temporary refresh failure supports retry; confirmed rejection clears only the affected session', async () => {
  let refreshes = 0;
  const api = {
    refresh: async () => {
      refreshes += 1;
      if (refreshes === 1) throw httpError(503);
      if (refreshes === 2) return tokenPair('winner');
      throw httpError(401);
    },
    get: async () => PERMISSIONS,
  };
  const first = sessionFixture(api, 'refresh-cloned');
  const duplicate = sessionFixture(api, 'refresh-cloned');

  assert.equal(await first.session.restore(), false);
  assert.equal(first.session.getSnapshot().phase, 'error');
  assert.equal(first.values.get(REFRESH_STORAGE_KEY), 'refresh-cloned');
  assert.equal(await first.session.restore(), true);
  assert.equal(await duplicate.session.restore(), false);
  assert.equal(duplicate.session.getSnapshot().phase, 'anonymous');
  assert.equal(duplicate.values.has(REFRESH_STORAGE_KEY), false);
  assert.equal(first.session.getSnapshot().phase, 'authenticated');
  assert.equal(first.values.get(REFRESH_STORAGE_KEY), 'refresh-winner');
});

test('logout clears local session immediately and revokes the token from in-flight rotation', async () => {
  const original = tokenPair('original');
  const rotated = tokenPair('rotated');
  const refreshStarted = deferred();
  const pendingRefresh = deferred();
  const revocations = [];
  const { session, values } = sessionFixture({
    login: async () => original,
    refresh: async () => {
      refreshStarted.resolve();
      return pendingRefresh.promise;
    },
    logout: async refresh => { revocations.push(refresh); },
    get: async path => {
      if (path === PERMISSIONS_PATH) return PERMISSIONS;
      throw httpError(401);
    },
  });

  assert.equal(await session.login('operator', 'test-password'), true);
  const interrupted = assert.rejects(session.get(TICKET_PATH), { code: 'stale-session' });
  await refreshStarted.promise;
  const logout = session.logout();
  assert.equal(session.getSnapshot().phase, 'anonymous');
  assert.equal(values.has(REFRESH_STORAGE_KEY), false);
  pendingRefresh.resolve(rotated);
  assert.equal(await logout, 'revoked');
  await interrupted;
  assert.deepEqual(revocations, [rotated.refresh_token]);
  assert.equal(session.getSnapshot().phase, 'anonymous');
  assert.equal(values.has(REFRESH_STORAGE_KEY), false);
});

test('server logout failure leaves local data cleared and revocation unconfirmed', async () => {
  const { session, values } = sessionFixture({
    login: async () => tokenPair('operator'),
    logout: async () => { throw httpError(503); },
    get: async () => PERMISSIONS,
  });

  assert.equal(await session.login('operator', 'test-password'), true);
  assert.equal(await session.logout(), 'unconfirmed');
  assert.equal(session.getSnapshot().phase, 'anonymous');
  assert.equal(session.getSnapshot().logoutStatus, 'unconfirmed');
  assert.deepEqual(session.getSnapshot().permissions, []);
  assert.equal(values.has(REFRESH_STORAGE_KEY), false);
});

test('a late read after logout cannot populate a different Admin session', async () => {
  const oldRead = deferred();
  const { session } = sessionFixture({
    login: async username => tokenPair(username, username === 'first' ? 17 : 23),
    logout: async () => {},
    get: async path => path === PERMISSIONS_PATH ? PERMISSIONS : oldRead.promise,
  });

  assert.equal(await session.login('first', 'test-password'), true);
  const discarded = assert.rejects(session.get(TICKET_PATH), { code: 'stale-session' });
  assert.equal(await session.logout(), 'revoked');
  assert.equal(await session.login('second', 'test-password'), true);
  oldRead.resolve({ ticket_id: 42, description: 'Earlier session data' });
  await discarded;
  assert.equal(session.getSnapshot().actorId, 23);
  assert.equal(session.getSnapshot().phase, 'authenticated');
});

test('a change to own roles suspends access before dispatch and ignores an earlier permissions read', async () => {
  const previousPermissions = deferred();
  const mutation = deferred();
  const updatedPermissions = deferred();
  const recheckStarted = deferred();
  const previousData = deferred();
  let checks = 0;
  let sends = 0;
  const { session } = sessionFixture({
    login: async () => tokenPair('role-operator'),
    get: async (path) => {
      if (path !== PERMISSIONS_PATH) return previousData.promise;
      checks += 1;
      if (checks === 1) return { permissions: ['admin.view', 'role.assign'] };
      if (checks === 2) return previousPermissions.promise;
      recheckStarted.resolve();
      return updatedPermissions.promise;
    },
    mutate: async () => {
      sends += 1;
      assert.equal(session.getSnapshot().checkingPermissions, true);
      return mutation.promise;
    },
  });
  assert.equal(await session.login('operator', 'fixture'), true);
  const olderCheck = session.reloadPermissions();
  const earlierData = assert.rejects(session.get('/admin/admins/17'), { code: 'stale-permissions' });
  const write = session.mutate('/admin/admins/17/roles', { method: 'DELETE', json: { roles: [24] } });
  assert.equal(await session.reloadPermissions(), false);
  await assert.rejects(session.get('/admin/admins/17'), { code: 'stale-permissions' });
  await assert.rejects(session.mutate('/admin/clients/1', { method: 'DELETE' }), { code: 'stale-permissions' });
  previousPermissions.resolve({ permissions: ['role.assign'] });
  previousData.resolve({ employee_id: 17 });
  assert.equal(await olderCheck, false);
  await earlierData;

  mutation.resolve({ employee_id: 17, roles: [] });
  await recheckStarted.promise;
  assert.equal(session.getSnapshot().checkingPermissions, true);
  updatedPermissions.resolve({ permissions: ['admin.view'] });
  await write;
  assert.equal(sends, 1);
  assert.equal(session.getSnapshot().checkingPermissions, false);
  assert.deepEqual(session.getSnapshot().permissions, ['admin.view']);
});

test('a failed strict permissions check keeps the same workspace suspended until a fresh retry', async () => {
  let checks = 0;
  const { session } = sessionFixture({
    login: async () => tokenPair('role-operator'),
    get: async () => {
      checks += 1;
      if (checks === 2) throw httpError(503);
      return checks === 1 ? { permissions: ['role.assign'] } : { permissions: [] };
    },
    mutate: async () => { throw httpError(503); },
  });
  await session.login('operator', 'fixture');
  await assert.rejects(session.mutate('/admin/admins/17/roles', { method: 'POST', json: { roles: [23] } }), { status: 503 });
  assert.equal(session.getSnapshot().phase, 'authenticated');
  assert.equal(session.getSnapshot().actorId, 17);
  assert.equal(session.getSnapshot().checkingPermissions, true);
  assert.equal(session.getSnapshot().error.status, 503);
  await assert.rejects(session.get('/admin/roles/admin'), { code: 'stale-permissions' });
  assert.equal(await session.recheckPermissions(), true);
  assert.equal(session.getSnapshot().checkingPermissions, false);
  assert.deepEqual(session.getSnapshot().permissions, []);
});

test('a refresh with unavailable storage keeps a strict permissions check suspended', async () => {
  const started = deferred();
  const retried = deferred();
  let requests = 0;
  let storageFails = false;
  const session = createSession({
    storage: {
      getItem: () => null,
      setItem: () => { if (storageFails) throw new Error('Storage unavailable'); },
      removeItem: () => {},
    },
    api: {
      login: async () => tokenPair('initial'),
      refresh: async () => tokenPair('rotated'),
      mutate: async () => ({ employee_id: 17, roles: [] }),
      get: async (path) => {
        assert.equal(path, PERMISSIONS_PATH);
        requests += 1;
        if (requests === 1) return { permissions: ['admin.view', 'role.assign'] };
        if (requests === 2) throw httpError(401);
        started.resolve();
        return retried.promise;
      },
    },
  });
  assert.equal(await session.login('operator', 'fixture'), true);
  storageFails = true;
  const write = session.mutate('/admin/admins/17/roles', { method: 'DELETE', json: { roles: [24] } });
  await started.promise;
  assert.equal(session.getSnapshot().storageAvailable, false);
  assert.equal(session.getSnapshot().checkingPermissions, true);
  await assert.rejects(session.get('/admin/admins/17'), { code: 'stale-permissions' });
  retried.reject(httpError(503));
  await write;
  assert.equal(session.getSnapshot().checkingPermissions, true);
  assert.equal(session.getSnapshot().error.status, 503);
});
