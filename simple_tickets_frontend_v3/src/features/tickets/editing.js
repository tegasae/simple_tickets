import { ApiError } from '../../api/transport.js';

const FIELDS = [
  'description', 'contact_user_id', 'department_id', 'urgency',
  'planned_at', 'remote_work_recommended',
];

function canonicalValue(field, value) {
  if (field === 'description' && typeof value === 'string') return value.trim();
  if (field === 'planned_at') {
    if (value === '' || value === null) return null;
    const time = typeof value === 'string' ? Date.parse(value) : NaN;
    if (Number.isFinite(time)) return new Date(time).toISOString();
  }
  return value;
}

export function editableFields(ticket) {
  return Object.fromEntries(FIELDS.map((field) => [
    field,
    canonicalValue(field, field === 'planned_at' ? ticket[field] ?? null : ticket[field]),
  ]));
}

export function isUnknownWriteOutcome(error) {
  return error?.status >= 500 ||
    ['timeout', 'network', 'invalid-response', 'unexpected-write-result'].includes(error?.code);
}

export async function saveTicketFields(api, ticketId, baseline, draft, { signal, canRead = true } = {}) {
  const activeSignal = api.bindSignal?.(signal) ?? signal;
  const before = editableFields(baseline);
  const desired = Object.fromEntries(FIELDS.filter((field) => Object.hasOwn(draft, field)).map(
    (field) => [field, canonicalValue(field, draft[field])],
  ));
  const state = {
    ticket: null,
    applied: [],
    matched: [],
    remaining: Object.keys(desired).filter((field) => desired[field] !== before[field]),
    conflicts: [],
    uncertainField: null,
    error: null,
  };
  const result = (status, error = null) => ({ ...state, status, error });

  function checkActive(error) {
    activeSignal?.throwIfAborted();
    if (error?.name === 'AbortError' || error?.code === 'stale-session') throw error;
  }

  function reconcile() {
    const current = editableFields(state.ticket);
    const pending = [];
    const conflicts = [];
    for (const field of state.remaining) {
      if (current[field] === desired[field]) {
        state.matched.push(field);
      } else {
        pending.push(field);
        if (current[field] !== before[field]) conflicts.push(field);
      }
    }
    state.remaining = pending;
    state.conflicts = conflicts;
  }

  async function rereadAfterFailure() {
    try {
      state.ticket = await api.get(ticketId, { signal: activeSignal });
      checkActive();
      reconcile();
    } catch (error) {
      checkActive(error);
    }
  }

  checkActive();
  if (!state.remaining.length) return result('unchanged');
  if (!canRead) return result('failed', new ApiError(403, 'preflight-read-required'));

  try {
    state.ticket = await api.get(ticketId, { signal: activeSignal });
    checkActive();
  } catch (error) {
    checkActive(error);
    return result('failed', error);
  }

  reconcile();
  while (state.remaining.length) {
    if (state.conflicts.length) return result(state.applied.length ? 'partial' : 'conflict');
    const field = state.remaining[0];
    try {
      checkActive();
      const next = await api.updateField(ticketId, field, desired[field], { signal: activeSignal });
      checkActive();
      state.ticket = next;
      if (editableFields(next)[field] !== desired[field]) {
        throw new ApiError(200, 'unexpected-write-result');
      }
      state.applied.push(field);
      state.remaining = state.remaining.slice(1);
      reconcile();
    } catch (error) {
      checkActive(error);
      if (isUnknownWriteOutcome(error)) {
        state.uncertainField = field;
        await rereadAfterFailure();
        return result('unconfirmed', error);
      }
      if (error?.status === 409) {
        await rereadAfterFailure();
        return result(state.applied.length ? 'partial' : 'conflict', error);
      }
      return result(state.applied.length ? 'partial' : 'failed', error);
    }
  }
  return result(state.applied.length ? 'saved' : 'unchanged');
}
