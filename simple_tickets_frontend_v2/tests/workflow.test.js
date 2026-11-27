import assert from 'node:assert/strict';
import test from 'node:test';

import { createWorkflowApi, workflowPayload } from '../src/api/resources/workflow.js';
import { ApiError } from '../src/api/transport.js';
import {
  allowedExecutors, availableActions, defaultWorkMode, workModes,
} from '../src/features/tickets/workflow/policy.js';

const TICKET_ID = 24;
const DATE = '2026-10-28T09:00:00Z';
const ACTOR = 17;
const OTHER = 28;
const DEPARTMENT = 4;

function event(status, overrides = {}) {
  return {
    id: 12, status, actor_id: ACTOR, executor_id: 0, date_created: DATE, comment: '',
    actual_started_at: null, actual_finished_at: null, duration: 'PT0S', work_is_remote: null,
    ...overrides,
  };
}

function ticket(status, overrides = {}) {
  return {
    ticket_id: TICKET_ID, client_id: 2, user_id: 0, contact_user_id: 0, user_ticket_id: 0,
    department_id: DEPARTMENT, current_executor_id: 0, last_executor_id: 0,
    text_of_ticket: 'Example', description: '', urgency: 'normal',
    date_created: DATE, date_finished: null, planned_at: null,
    remote_work_recommended: false, is_closed: false,
    statuses: [event(status)], comments: [], ...overrides,
  };
}

function rules(permissions, actorId = ACTOR, actorDepartmentId) {
  return { permissions, actorId, actorDepartmentId };
}

function atWork(executor, options) {
  return ticket('at_work', {
    current_executor_id: executor,
    statuses: [event('at_work', { work_is_remote: false, ...options })],
  });
}

test('workflow commands use exact PATCH paths and omit unrelated fields', async () => {
  const calls = [];
  const signal = new AbortController().signal;
  const api = createWorkflowApi({
    mutate: async (path, request) => {
      calls.push([path, request]);
      return ticket('accepted');
    },
  });
  const cases = [
    ['accept', 'accept', {}, {}],
    ['reject', 'reject', { comment: '  Отказ  ' }, { comment: 'Отказ' }],
    ['defer', 'defer', { comment: 'Причина' }, { comment: 'Причина' }],
    ['assign', 'executor', { executor_id: OTHER }, { executor_id: OTHER }],
    ['startWork', 'start-work', { work_is_remote: true }, { work_is_remote: true }],
    ['pauseWork', 'pause-work', {}, {}],
    ['resumeWork', 'resume-work', { work_is_remote: false }, { work_is_remote: false }],
    ['finishWork', 'finish-work', { comment: 'Готово' }, { comment: 'Готово' }],
    ['registerWork', 'complete-work-retroactively', {
      work_is_remote: true, duration: 5_400,
    }, { work_is_remote: true, duration: 'PT5400S' }],
    ['execute', 'execute', {}, {}],
    ['startRemoteWork', 'start-remote-work', {}, {}],
    ['cancel', 'cancel', { comment: '  Отмена  ' }, { comment: 'Отмена' }],
  ];
  for (const [action, suffix, payload] of cases) {
    assert.equal((await api.execute(TICKET_ID, action, payload, { signal })).ticket_id, TICKET_ID);
    assert.equal(calls.at(-1)[0], `/admin/tickets/${TICKET_ID}/${suffix}`);
  }
  assert.deepEqual(calls.map(([, options]) => options), cases.map(([, , , json]) => ({
    method: 'PATCH', json, signal,
  })));
  await assert.rejects(api.execute(TICKET_ID, 'startRemoteWork', { work_is_remote: true }), {
    code: 'invalid-request',
  });
  assert.equal(calls.length, cases.length);
});

test('workflow requires reasons and validates retrospective alternatives before sending', () => {
  for (const action of ['reject', 'defer', 'cancel']) {
    assert.throws(() => workflowPayload(action, { comment: '  ' }), {
      status: 422, fields: ['comment'],
    });
  }
  assert.throws(() => workflowPayload('accept', { comment: 'я'.repeat(1_001) }), {
    status: 422, fields: ['comment'],
  });
  assert.throws(() => workflowPayload('assign', { executor_id: '17' }), {
    status: 422, fields: ['executor_id'],
  });
  assert.throws(() => workflowPayload('resumeWork', { work_is_remote: 'false' }), {
    status: 422, fields: ['work_is_remote'],
  });
  const interval = { actual_started_at: '2026-10-28T11:00:00+02:00', actual_finished_at: '2026-10-28T09:30:00Z' };
  assert.deepEqual(workflowPayload('registerWork', interval), {
    actual_started_at: '2026-10-28T09:00:00.000Z',
    actual_finished_at: '2026-10-28T09:30:00.000Z',
  });
  assert.throws(() => workflowPayload('registerWork', { ...interval, duration: 60 }), {
    status: 422, fields: ['duration', 'actual_started_at', 'actual_finished_at'],
  });
  assert.throws(() => workflowPayload('registerWork', {
    ...interval, actual_finished_at: '2026-10-28T08:30:00Z',
  }), { status: 422, fields: ['actual_started_at', 'actual_finished_at'] });
  assert.throws(() => workflowPayload('registerWork', { duration: 0 }), { status: 422, fields: ['duration'] });
  assert.deepEqual(workflowPayload('registerWork', { duration: 'PT5400S' }), { duration: 'PT5400S' });
});

test('one workflow mutation is observed without transport replay or read on unknown result', async () => {
  let count = 0;
  const api = createWorkflowApi({
    get: async () => assert.fail('Receipt verification is a separate read in the controller'),
    mutate: async () => {
      count += 1;
      throw new ApiError(0, 'timeout');
    },
  });
  await assert.rejects(api.execute(TICKET_ID, 'startRemoteWork'), { code: 'timeout' });
  assert.equal(count, 1);
});

test('ordinary assignment uses the Admin catalog, matches department, excludes self and keeps disabled data readable', async () => {
  const admin = (id, departmentId, enabled, enabledLogin = true) => ({
    employee_id: id, department_id: departmentId, enabled, enabled_login: enabledLogin,
    first_name: 'Имя', last_name: '', job_title: '',
  });
  const catalog = [
    admin(ACTOR, DEPARTMENT, true),
    admin(OTHER, DEPARTMENT, true, false),
    admin(33, DEPARTMENT + 1, true),
    admin(36, DEPARTMENT, false),
  ];
  const api = createWorkflowApi({
    get: async path => {
      assert.equal(path, '/admin/admins/');
      return catalog;
    },
  });
  const accepted = ticket('accepted');
  assert.deepEqual(await api.admins(), catalog);
  assert.deepEqual(allowedExecutors(accepted, catalog, { actorId: ACTOR }), [catalog[1]]);
  assert.deepEqual(allowedExecutors(ticket('accepted', { department_id: 0 }), catalog, { actorId: ACTOR }), []);
  assert.deepEqual(allowedExecutors(accepted, catalog, {}), []);
  assert.deepEqual(availableActions(accepted, rules(['ticket.assign_executor'])), []);
  assert.deepEqual(availableActions(accepted, rules(['ticket.assign_executor', 'admin.view'])), ['assign']);
  assert.deepEqual(availableActions(atWork(ACTOR), rules(['ticket.assign_executor', 'admin.view'])), []);
  assert.deepEqual(availableActions(atWork(OTHER), rules(['ticket.assign_executor', 'admin.view'])), ['assign']);
  const denied = createWorkflowApi({ get: async () => { throw new ApiError(403); } });
  await assert.rejects(denied.admins(), { status: 403 });
});

test('intake, deferral, and review follow exact action rights and valid statuses', () => {
  const accept = rules(['ticket.accepted']);
  const reject = rules(['ticket.canceled']);
  const defer = rules(['ticket.operation']);
  for (const status of ['created', 'created_from_request_user', 'created_from_ticket_user']) {
    assert.deepEqual(availableActions(ticket(status), accept), ['accept']);
    assert.deepEqual(availableActions(ticket(status), reject), ['reject']);
    assert.deepEqual(availableActions(ticket(status), defer), []);
  }
  assert.deepEqual(availableActions(ticket('deferred'), accept), ['accept']);
  assert.deepEqual(availableActions(ticket('assigned'), accept), ['accept']);
  assert.deepEqual(availableActions(ticket('ready_for_review'), accept), ['accept']);
  assert.deepEqual(availableActions(ticket('accepted'), reject), ['cancel']);
  assert.deepEqual(availableActions(atWork(ACTOR), reject), []);
  assert.deepEqual(availableActions(atWork(OTHER), reject), ['cancel']);
  assert.deepEqual(availableActions(ticket('executed', { is_closed: true }), rules(['ticket.delete'])), ['deleteTicket']);
  assert.deepEqual(availableActions(ticket('accepted'), defer), ['defer']);
  assert.deepEqual(availableActions(atWork(ACTOR), defer), []);
  assert.deepEqual(availableActions(atWork(OTHER), defer), ['defer']);
  assert.deepEqual(availableActions(ticket('ready_for_review'), rules(['ticket.executed'])), ['execute']);
  assert.deepEqual(availableActions(ticket('suspended'), rules(['ticket.executed', 'ticket.accepted'])), []);
  assert.deepEqual(availableActions(ticket('accepted', { is_closed: true }), defer), []);
  assert.deepEqual(availableActions(ticket('accepted', { statuses: [] }), defer), []);
});

test('hotline requires recommendation and uses department only before assignment', () => {
  const hot = rules(['ticket.at_work_remote'], ACTOR, DEPARTMENT);
  const recommended = ticket('accepted', { remote_work_recommended: true });
  assert.deepEqual(availableActions(recommended, hot), ['startRemoteWork']);
  assert.deepEqual(availableActions(recommended, rules(hot.permissions)), ['startRemoteWork']);
  assert.deepEqual(availableActions(recommended, rules(hot.permissions, ACTOR, DEPARTMENT + 1)), []);
  assert.deepEqual(availableActions(recommended, rules(hot.permissions, ACTOR, 0)), []);
  assert.deepEqual(availableActions({ ...recommended, department_id: 0 }, hot), []);
  assert.deepEqual(availableActions(recommended, rules(hot.permissions, null)), []);
  assert.deepEqual(availableActions(ticket('accepted'), hot), []);
  const assigned = ticket('assigned', { current_executor_id: ACTOR, remote_work_recommended: true });
  assert.deepEqual(availableActions(assigned, rules(hot.permissions, ACTOR, DEPARTMENT + 1)), ['startRemoteWork']);
  assert.deepEqual(availableActions(assigned, rules(hot.permissions, OTHER)), []);
});

test('work actions distinguish assignment, current actors, modes and retrospective work', () => {
  const general = rules(['ticket.at_work']);
  const remote = rules(['ticket.at_work_remote']);
  const retrospective = rules(['ticket.at_work_retrospective']);
  const assigned = ticket('assigned', { current_executor_id: ACTOR });
  assert.deepEqual(availableActions(assigned, general), ['startWork']);
  assert.deepEqual(availableActions(assigned, remote), []);
  assert.deepEqual(availableActions(assigned, retrospective), ['registerWork']);
  assert.deepEqual(availableActions(assigned, rules(general.permissions, OTHER)), []);
  assert.deepEqual(workModes(assigned, 'startWork', general), [false, true]);
  assert.deepEqual(workModes(assigned, 'registerWork', retrospective), [false, true]);
  assert.deepEqual(availableActions(atWork(ACTOR), general), ['pauseWork', 'finishWork']);
  assert.deepEqual(availableActions(atWork(OTHER), general), []);
  assert.deepEqual(availableActions(atWork(ACTOR, { work_is_remote: true }), remote), ['pauseWork', 'finishWork']);
  assert.deepEqual(availableActions(atWork(ACTOR), remote), []);
  assert.deepEqual(availableActions(atWork(OTHER, { work_is_remote: true }), remote), []);
  assert.deepEqual(availableActions(atWork(OTHER, { duration: 'PT35M' }), general), ['finishWork']);
  assert.deepEqual(availableActions(atWork(ACTOR, { duration: 'PT35M' }), general), ['finishWork']);
  assert.deepEqual(availableActions(atWork(ACTOR, { duration: 'invalid' }), general), []);

  const paused = ticket('paused', {
    current_executor_id: ACTOR, remote_work_recommended: true,
    statuses: [event('at_work', { work_is_remote: true }), event('paused')],
  });
  assert.equal(defaultWorkMode(paused), true);
  assert.deepEqual(availableActions(paused, remote), ['resumeWork']);
  assert.deepEqual(workModes(paused, 'resumeWork', remote), [true]);
  assert.deepEqual(workModes(paused, 'resumeWork', general), [false, true]);
  assert.deepEqual(availableActions({ ...paused, remote_work_recommended: false }, remote), []);
  assert.deepEqual(availableActions({ ...paused, current_executor_id: OTHER }, general), []);
});
