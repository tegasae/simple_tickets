const editableStatuses = new Set([
  "created", "created_from_request_user", "created_from_ticket_user", "accepted", "deferred",
]);
const commentStatuses = new Set([
  ...editableStatuses, "assigned", "at_work", "paused", "ready_for_review",
]);

export const fieldLabels = Object.freeze({
  description: "ticket.description",
  contact_user_id: "ticket.contact",
  department_id: "ticket.department",
  urgency: "ticket.urgency",
  planned_at: "work.schedule",
  remote_work_recommended: "ticket.remoteRecommended",
});

export function canCreateTicket(permissions) {
  return permissions.includes("client.view")
    && (permissions.includes("ticket.created") || permissions.includes("ticket.operation"));
}

export function allowedFields(status, permissions) {
  if (!editableStatuses.has(status)) return [];
  return Object.keys(fieldLabels).filter((field) => permissions.includes(
    field === "remote_work_recommended" ? "ticket.set_remote_recommendation" : "ticket.operation",
  ));
}

export function canPostComment(status, permissions, closed) {
  return !closed && commentStatuses.has(status) && permissions.includes("ticket.operation");
}

export function hasEdits(record) {
  return Object.keys(record?.changes ?? {}).length > 0;
}

export function isDirty(record) {
  return hasEdits(record) || Boolean(record?.comment || record?.workflowPending) || hasWorkflowInput(record?.workflowForm);
}

export function hasWorkflowInput(form) {
  return Boolean(form && (form.comment || Number(form.executorId) > 0 || form.startLocal || form.finishLocal
    || Number(form.hours) > 0 || Number(form.minutes) > 0 || form.remote !== form.initialRemote));
}

export const emptyTicket = Object.freeze({
  client_id: 0, text_of_ticket: "", description: "", user_id: 0, contact_user_id: 0,
  department_id: 0, remote_work_recommended: false, urgency: "normal", planned_at: null, comment: "",
});

export function changeNewField(data, field, value) {
  if (field === "client_id" && value !== data.client_id) {
    return { ...data, client_id: value, user_id: 0, contact_user_id: 0 };
  }
  return { ...data, [field]: value };
}

export function hasNewDraft(data) {
  return Object.entries(emptyTicket).some(([field, value]) => data[field] !== value);
}

export function operationKey() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function withinReplayWindow(intent, now = Date.now()) {
  // The server keeps idempotency results for 24 hours. Leave a margin for clock drift.
  const age = now - (intent?.startedAt ?? NaN);
  return age >= 0 && age < 23 * 60 * 60 * 1000;
}

export function isUnknownWrite(error) {
  return !error || !error.status || error.status >= 500 || error.code === "invalid-response";
}
