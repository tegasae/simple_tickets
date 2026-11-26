import { normalizeStatus } from "../model.js";
import { workDurationSeconds } from "./policy.js";

const expectedStatuses = Object.freeze({
  accept: "accepted",
  reject: "rejected",
  defer: "deferred",
  assign: "assigned",
  startWork: "at_work",
  startRemoteWork: "at_work",
  pauseWork: "paused",
  resumeWork: "at_work",
  finishWork: "ready_for_review",
  registerWork: "ready_for_review",
  execute: "executed",
});

function statusOf(record) {
  return normalizeStatus(record?.status);
}

export function sameWorkflowHistory(before, latest) {
  return before.statuses.length === latest.statuses.length && before.statuses.at(-1)?.id === latest.statuses.at(-1)?.id;
}

export function sameWorkflowState(before, latest) {
  const first = before.statuses.at(-1);
  const second = latest.statuses.at(-1);
  return sameWorkflowHistory(before, latest) &&
    statusOf(first) === statusOf(second) && (statusOf(first) !== "at_work" || first.work_is_remote === second.work_is_remote) &&
    first?.actual_started_at === second?.actual_started_at && first?.actual_finished_at === second?.actual_finished_at &&
    first?.duration === second?.duration && before.current_executor_id === latest.current_executor_id &&
    before.department_id === latest.department_id && before.remote_work_recommended === latest.remote_work_recommended &&
    before.is_closed === latest.is_closed;
}

function matchingWorkTime(record, payload) {
  if (payload.duration !== undefined) return workDurationSeconds(record.duration) === payload.duration;
  return Date.parse(record.actual_started_at) === Date.parse(payload.actual_started_at) &&
    Date.parse(record.actual_finished_at) === Date.parse(payload.actual_finished_at);
}

export function confirmsWorkflow(latest, before, action, payload, actorId) {
  if (!Object.hasOwn(expectedStatuses, action) || !Number.isSafeInteger(actorId) || actorId <= 0) return false;
  const history = latest.statuses;
  const offset = before.statuses.length;
  const baseline = before.statuses.at(-1);
  if (!baseline?.id || baseline.id !== history[offset - 1]?.id) return false;

  const autoAssign = action === "startRemoteWork" && statusOf(baseline) === "accepted";
  const retrospective = action === "registerWork";
  const first = history[offset];
  const last = autoAssign || retrospective ? history[offset + 1] : first;
  const commentRecord = retrospective ? first : last;
  if (!first?.id || first.id <= baseline.id || !last?.id ||
      (last !== first && (last.id <= first.id || !first.date_created || first.date_created !== last.date_created)) ||
      first.actor_id !== actorId || last.actor_id !== actorId ||
      statusOf(last) !== expectedStatuses[action] || commentRecord?.comment !== (payload.comment?.trim() ?? "")) return false;

  const executorMatches = (id) => last !== history.at(-1) || latest.current_executor_id === id;
  if (action === "assign") return last.executor_id === payload.executor_id && executorMatches(payload.executor_id);
  if (action === "startRemoteWork") {
    return last.work_is_remote === true && executorMatches(actorId) &&
      (autoAssign ? statusOf(first) === "assigned" && first.executor_id === actorId : before.current_executor_id === actorId);
  }
  if (action === "startWork" || action === "resumeWork") {
    return last.work_is_remote === (payload.work_is_remote ?? false) &&
      before.current_executor_id === actorId && executorMatches(actorId);
  }
  if (retrospective) {
    return statusOf(first) === "at_work" && first.work_is_remote === (payload.work_is_remote ?? false) &&
      matchingWorkTime(first, payload);
  }
  return true;
}
