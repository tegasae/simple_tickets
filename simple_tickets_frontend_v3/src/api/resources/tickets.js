import { ApiError } from '../transport.js';

const TICKETS = '/admin/tickets';
const LIST_PATHS = {
  all: `${TICKETS}/`,
  open: `${TICKETS}/open`,
  closed: `${TICKETS}/closed`,
};
const FIELD_PATHS = {
  description: 'description',
  contact_user_id: 'contact-user',
  department_id: 'department',
  urgency: 'urgency',
  planned_at: 'schedule',
  remote_work_recommended: 'remote-work-recommended',
};
const URGENCIES = ['normal', 'urgent', 'maintenance'];

export function requireId(id) {
  if (!Number.isSafeInteger(id) || id <= 0) {
    throw new ApiError(0, 'invalid-request');
  }
  return id;
}

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function isId(value) {
  return Number.isSafeInteger(value) && value >= 0;
}

function isDateTime(value) {
  return typeof value === 'string' && Number.isFinite(Date.parse(value));
}

function isOptionalDateTime(value) {
  return value == null || isDateTime(value);
}

function isTimelineEntry(value) {
  return isRecord(value) &&
    (value.id == null || isId(value.id)) &&
    (value.actor_id == null || isId(value.actor_id)) &&
    isOptionalDateTime(value.date_created) &&
    typeof value.comment === 'string';
}

function isStatusEntry(value) {
  return isTimelineEntry(value) &&
    typeof value.status === 'string' &&
    (value.executor_id == null || isId(value.executor_id)) &&
    isOptionalDateTime(value.actual_started_at) &&
    isOptionalDateTime(value.actual_finished_at) &&
    (value.work_is_remote == null || typeof value.work_is_remote === 'boolean');
}

function isTicket(value) {
  return isRecord(value) &&
    isId(value.ticket_id) &&
    value.ticket_id > 0 &&
    [
      value.client_id,
      value.user_id,
      value.contact_user_id,
      value.user_ticket_id,
      value.department_id,
      value.current_executor_id,
      value.last_executor_id,
    ].every(isId) &&
    typeof value.text_of_ticket === 'string' &&
    typeof value.description === 'string' &&
    typeof value.urgency === 'string' &&
    typeof value.remote_work_recommended === 'boolean' &&
    typeof value.is_closed === 'boolean' &&
    isDateTime(value.date_created) &&
    isOptionalDateTime(value.date_finished) &&
    isOptionalDateTime(value.planned_at) &&
    Array.isArray(value.statuses) &&
    value.statuses.every(isStatusEntry) &&
    Array.isArray(value.comments) &&
    value.comments.every(isTimelineEntry);
}

export function requireTicket(ticket, expectedId, status = 200) {
  if (!isTicket(ticket) || (expectedId !== undefined && ticket.ticket_id !== expectedId)) {
    throw new ApiError(status, 'invalid-response');
  }
  return ticket;
}

function isFieldValue(field, value) {
  switch (field) {
    case 'description': return typeof value === 'string';
    case 'contact_user_id':
    case 'department_id': return isId(value);
    case 'urgency': return URGENCIES.includes(value);
    case 'planned_at': return value === null ||
      (isDateTime(value) && /(?:Z|[+-]\d{2}:\d{2})$/i.test(value));
    case 'remote_work_recommended': return typeof value === 'boolean';
    default: return false;
  }
}

export function createTicketsApi(session) {
  return {
    bindSignal: (signal) => session.bindSignal?.(signal) ?? signal,

    async list({ queue = 'open', executorId, signal } = {}) {
      const path = queue === 'mine'
        ? `${TICKETS}/by-executor/${requireId(executorId)}`
        : Object.hasOwn(LIST_PATHS, queue) && LIST_PATHS[queue];
      if (!path) {
        throw new ApiError(0, 'invalid-request');
      }
      const tickets = await session.get(path, { signal });
      if (!Array.isArray(tickets) || !tickets.every(isTicket)) {
        throw new ApiError(200, 'invalid-response');
      }
      return tickets;
    },

    async get(ticketId, { signal } = {}) {
      const id = requireId(ticketId);
      const ticket = await session.get(`${TICKETS}/${id}`, { signal });
      return requireTicket(ticket, id);
    },

    async create(payload, { idempotencyKey, signal } = {}) {
      if (!isRecord(payload)) {
        throw new ApiError(0, 'invalid-request');
      }
      const ticket = await session.mutate(`${TICKETS}/`, {
        method: 'POST', json: payload, idempotencyKey, signal,
      });
      return requireTicket(ticket, undefined, 201);
    },

    async addComment(ticketId, comment, { idempotencyKey, signal } = {}) {
      const id = requireId(ticketId);
      if (typeof comment !== 'string' || !comment.trim()) {
        throw new ApiError(422, 'validation', ['comment']);
      }
      const ticket = await session.mutate(`${TICKETS}/${id}/comments`, {
        method: 'POST', json: { comment }, idempotencyKey, signal,
      });
      return requireTicket(ticket, id);
    },

    async updateField(ticketId, field, value, { signal } = {}) {
      const id = requireId(ticketId);
      if (!Object.hasOwn(FIELD_PATHS, field)) {
        throw new ApiError(0, 'invalid-request');
      }
      if (!isFieldValue(field, value)) {
        throw new ApiError(422, 'validation', [field]);
      }
      const path = `${TICKETS}/${id}/${FIELD_PATHS[field]}`;
      const options = field === 'planned_at' && value === null
        ? { method: 'DELETE', signal }
        : { method: 'PATCH', json: { [field]: value }, signal };
      return requireTicket(await session.mutate(path, options), id);
    },
  };
}
