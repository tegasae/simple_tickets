import { ApiError } from '../transport.js';
import { requireId, requireTicket } from './tickets.js';

const COMMANDS = {
  accept: { path: 'accept' },
  reject: { path: 'reject', requiredComment: true },
  defer: { path: 'defer', requiredComment: true },
  assign: { path: 'executor', fields: ['executor_id'] },
  startWork: { path: 'start-work', fields: ['work_is_remote'] },
  pauseWork: { path: 'pause-work' },
  resumeWork: { path: 'resume-work', fields: ['work_is_remote'] },
  finishWork: { path: 'finish-work' },
  registerWork: {
    path: 'complete-work-retroactively',
    fields: ['work_is_remote', 'duration', 'actual_started_at', 'actual_finished_at'],
  },
  execute: { path: 'execute' },
  startRemoteWork: { path: 'start-remote-work' },
};

function invalidFields(...fields) {
  return new ApiError(422, 'validation', fields);
}

function readInstant(value, field) {
  const time = typeof value === 'string' && /(?:Z|[+-]\d{2}:\d{2})$/i.test(value)
    ? Date.parse(value)
    : NaN;
  if (!Number.isFinite(time)) throw invalidFields(field);
  return time;
}

function registeredWork({ duration, actual_started_at, actual_finished_at }) {
  const usesDuration = duration !== undefined && duration !== null;
  const usesInterval = actual_started_at != null || actual_finished_at != null;
  if (usesDuration === usesInterval) {
    throw invalidFields('duration', 'actual_started_at', 'actual_finished_at');
  }
  if (usesDuration) {
    const seconds = typeof duration === 'string' && /^PT[1-9]\d*S$/.test(duration)
      ? Number(duration.slice(2, -1))
      : duration;
    if (!Number.isSafeInteger(seconds) || seconds <= 0) throw invalidFields('duration');
    return { duration: `PT${seconds}S` };
  }
  const start = readInstant(actual_started_at, 'actual_started_at');
  const finish = readInstant(actual_finished_at, 'actual_finished_at');
  if (finish <= start) throw invalidFields('actual_started_at', 'actual_finished_at');
  return {
    actual_started_at: new Date(start).toISOString(),
    actual_finished_at: new Date(finish).toISOString(),
  };
}

export function workflowPayload(action, payload = {}) {
  if (!Object.hasOwn(COMMANDS, action) || !payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new ApiError(0, 'invalid-request');
  }
  const command = COMMANDS[action];
  const allowedFields = ['comment', ...(command.fields ?? [])];
  const input = Object.assign(Object.create(null), payload);
  if (Object.keys(input).some((field) => !allowedFields.includes(field))) {
    throw new ApiError(0, 'invalid-request');
  }

  const json = {};
  if (input.comment !== undefined && typeof input.comment !== 'string') {
    throw invalidFields('comment');
  }
  const comment = input.comment?.trim() ?? '';
  if ((command.requiredComment && !comment) || [...comment].length > 1_000) {
    throw invalidFields('comment');
  }
  if (comment) json.comment = comment;

  if (action === 'assign') {
    if (!Number.isSafeInteger(input.executor_id) || input.executor_id <= 0) {
      throw invalidFields('executor_id');
    }
    json.executor_id = input.executor_id;
  }
  if (input.work_is_remote !== undefined) {
    if (typeof input.work_is_remote !== 'boolean') throw invalidFields('work_is_remote');
    json.work_is_remote = input.work_is_remote;
  }
  return action === 'registerWork' ? { ...json, ...registeredWork(input) } : json;
}

function isAdmin(value) {
  return value != null && Number.isSafeInteger(value.employee_id) && value.employee_id > 0 &&
    Number.isSafeInteger(value.department_id) && value.department_id >= 0 &&
    typeof value.enabled === 'boolean' &&
    [value.first_name, value.last_name, value.job_title].every((field) => typeof field === 'string');
}

export function createWorkflowApi(session) {
  return {
    bindSignal: (signal) => session.bindSignal?.(signal) ?? signal,

    async execute(ticketId, action, payload = {}, { signal } = {}) {
      const id = requireId(ticketId);
      const json = workflowPayload(action, payload);
      const path = `/admin/tickets/${id}/${COMMANDS[action].path}`;
      return requireTicket(await session.mutate(path, { method: 'PATCH', json, signal }), id);
    },

    async admins({ signal } = {}) {
      const rows = await session.get('/admin/admins/', { signal });
      if (!Array.isArray(rows) || !rows.every(isAdmin)) {
        throw new ApiError(200, 'invalid-response');
      }
      return rows;
    },
  };
}
