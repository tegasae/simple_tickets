import { normalizeStatus } from '../model.js';

const INITIAL = ['created', 'created_from_request_user', 'created_from_ticket_user'];
const ACCEPTABLE = [...INITIAL, 'deferred', 'assigned', 'ready_for_review'];
const DEFERRABLE = ['accepted', 'assigned', 'at_work', 'paused'];
const ASSIGNABLE = ['accepted', 'deferred', 'assigned', 'at_work', 'paused', 'ready_for_review'];

function isPositiveId(value) {
  return Number.isSafeInteger(value) && value > 0;
}

export function workDurationSeconds(value) {
  if (typeof value === 'number') return Number.isFinite(value) && value >= 0 ? value : null;
  if (typeof value !== 'string') return null;
  const match = value.match(/^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$/);
  if (!match?.slice(1).some(Boolean)) return null;
  const [, days = 0, hours = 0, minutes = 0, seconds = 0] = match;
  const total = days * 86400 + hours * 3600 + minutes * 60 + Number(seconds);
  return Number.isFinite(total) ? total : null;
}

function workIsRetrospective(record) {
  if (record.actual_started_at != null || record.actual_finished_at != null) {
    const start = Date.parse(record.actual_started_at);
    const finish = Date.parse(record.actual_finished_at);
    return Number.isFinite(start) && Number.isFinite(finish) && finish > start ? true : null;
  }
  const duration = workDurationSeconds(record.duration);
  return duration === null ? null : duration > 0;
}

export function workModes(ticket, action, { permissions = [] } = {}) {
  if (action === 'registerWork') {
    return permissions.includes('ticket.at_work_retrospective') ? [false, true] : [];
  }
  if (action === 'startWork' || action === 'resumeWork') {
    if (permissions.includes('ticket.at_work')) return [false, true];
    if (action === 'resumeWork' && ticket?.remote_work_recommended === true &&
        permissions.includes('ticket.at_work_remote')) return [true];
  }
  return [];
}

export function defaultWorkMode(ticket) {
  const history = Array.isArray(ticket?.statuses) ? ticket.statuses : [];
  return history.findLast((entry) => normalizeStatus(entry?.status) === 'at_work')?.work_is_remote === true;
}

export function availableActions(ticket, { permissions = [], actorId, actorDepartmentId } = {}) {
  const record = Array.isArray(ticket?.statuses) ? ticket.statuses.at(-1) : null;
  const status = normalizeStatus(record?.status);
  if (!status || ticket.is_closed === true) return [];

  const has = (permission) => permissions.includes(permission);
  const actorKnown = isPositiveId(actorId);
  const executorKnown = isPositiveId(ticket.current_executor_id);
  const actorIsExecutor = actorKnown && executorKnown && actorId === ticket.current_executor_id;
  const otherActorAtWork = actorKnown && executorKnown && !actorIsExecutor;
  const atWork = status === 'at_work';
  const retrospective = atWork ? workIsRetrospective(record) : null;
  const generalWorker = has('ticket.at_work');
  const remoteWorker = has('ticket.at_work_remote');
  const handlesCurrentRemoteWork = remoteWorker && actorIsExecutor && record.work_is_remote === true;
  const hasTicketDepartment = isPositiveId(ticket.department_id);
  const departmentMatches = hasTicketDepartment &&
    (actorDepartmentId == null || actorDepartmentId === ticket.department_id);
  const permittedHotline = remoteWorker && actorKnown && ticket.remote_work_recommended === true &&
    ((status === 'accepted' && departmentMatches) || (status === 'assigned' && actorIsExecutor));

  const options = [
    ['accept', has('ticket.accepted') && ACCEPTABLE.includes(status)],
    ['reject', has('ticket.canceled') && INITIAL.includes(status)],
    ['defer', has('ticket.operation') && DEFERRABLE.includes(status) && (!atWork || otherActorAtWork)],
    ['assign', has('ticket.assign_executor') && has('admin.view') && actorKnown && hasTicketDepartment &&
      ASSIGNABLE.includes(status) && (!atWork || otherActorAtWork)],
    ['startWork', status === 'assigned' && actorIsExecutor && generalWorker],
    ['pauseWork', atWork && actorIsExecutor && retrospective === false && (generalWorker || handlesCurrentRemoteWork)],
    ['resumeWork', status === 'paused' && actorIsExecutor && workModes(ticket, 'resumeWork', { permissions }).length > 0],
    ['finishWork', atWork && retrospective !== null &&
      ((generalWorker && (actorIsExecutor || (actorKnown && retrospective))) || handlesCurrentRemoteWork)],
    ['registerWork', status === 'assigned' && executorKnown && actorKnown && has('ticket.at_work_retrospective')],
    ['execute', status === 'ready_for_review' && has('ticket.executed')],
    ['startRemoteWork', permittedHotline],
  ];
  return options.filter(([, allowed]) => allowed).map(([action]) => action);
}

export function allowedExecutors(ticket, admins, { actorId } = {}) {
  if (!isPositiveId(ticket?.department_id) || !isPositiveId(actorId) || !Array.isArray(admins)) return [];
  return admins.filter((admin) => admin?.enabled === true &&
    isPositiveId(admin.employee_id) &&
    admin.department_id === ticket.department_id &&
    admin.employee_id !== actorId);
}
