import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { ApiError } from "../../api/transport.js";
import { editableFields, saveTicketFields } from "./editing.js";
import { normalizeStatus } from "./model.js";
import { allowedFields, canPostComment, hasEdits, isUnknownWrite, operationKey, withinReplayWindow } from "./workspaceState.js";
import { availableActions } from "./workflow/policy.js";
import { confirmsWorkflow, sameWorkflowHistory, sameWorkflowState } from "./workflow/receipts.js";
import { errorText, t } from "../../shared/i18n/messages.js";

const emptyRecord = Object.freeze({
  title: "", status: "", closed: false, revision: 0, history: false,
  editing: false, changes: {}, baseline: null, outcome: null, confirmed: false,
  editError: null, busy: false, comment: "", commentError: null, commentIntent: null,
  commentUncertain: false, commentSent: false,
  workflowForm: null, workflowFeedback: null, workflowPending: null,
});

export function useTicketWork(api, session, canView, permissions, onChanged, { workflowApi, actorId }) {
  const [records, setRecords] = useState({});
  const [openIds, setOpenIds] = useState([]);
  const work = useRef(new Map());
  const available = useRef(canView);
  const rights = useRef(permissions);
  useLayoutEffect(() => {
    available.current = canView;
    rights.current = permissions;
    if (!canView) {
      for (const controller of work.current.values()) controller.abort();
      work.current.clear();
      setRecords((previous) => Object.keys(previous).length ? {} : previous);
      setOpenIds((previous) => previous.length ? [] : previous);
    }
  }, [canView, permissions]);
  useEffect(() => () => {
    for (const controller of work.current.values()) controller.abort();
    work.current.clear();
  }, []);

  const update = useCallback((id, change) => {
    if (!available.current) return;
    setRecords((previous) => {
      const before = previous[id] ?? emptyRecord;
      const after = typeof change === "function" ? change(before) : { ...before, ...change };
      return after === before ? previous : { ...previous, [id]: after };
    });
  }, []);

  const open = useCallback((id, title) => {
    if (!available.current) return;
    setOpenIds((previous) => previous.includes(id) ? previous : [...previous, id]);
    if (title) update(id, (record) => record.title === title ? record : { ...record, title });
  }, [update]);

  const remember = useCallback((id, ticket) => {
    const status = normalizeStatus(ticket.statuses.at(-1)?.status);
    const title = ticket.text_of_ticket;
    const closed = ticket.is_closed;
    update(id, (record) => record.status === status && record.title === title && record.closed === closed
      ? record
      : { ...record, status, title, closed });
  }, [update]);

  function close(id) {
    if (work.current.has(id)) return false;
    setOpenIds((previous) => previous.filter((item) => item !== id));
    setRecords((previous) => {
      const next = { ...previous };
      const record = previous[id];
      if (record?.workflowPending?.action === "deleteTicket") {
        next[id] = { ...emptyRecord, workflowPending: { action: "deleteTicket" }, workflowFeedback: record.workflowFeedback };
      } else {
        delete next[id];
      }
      return next;
    });
    return true;
  }

  function beginEdit(id, ticket) {
    update(id, (record) => ({
      ...record, editing: true, confirmed: false,
      baseline: record.baseline ?? editableFields(ticket),
    }));
  }

  function change(id, field, value) {
    update(id, (record) => {
      if (!record.baseline || record.busy) return record;
      const changes = { ...record.changes };
      if (record.baseline[field] === value) delete changes[field];
      else changes[field] = value;
      return { ...record, changes, editError: null, confirmed: false };
    });
  }

  function adoptLatest(id) {
    update(id, (record) => {
      if (!record.outcome?.ticket || record.busy) return record;
      const baseline = editableFields(record.outcome.ticket);
      const changes = Object.fromEntries(Object.entries(record.changes).filter(([field, value]) => baseline[field] !== value));
      return { ...record, baseline, changes, outcome: null };
    });
  }

  function start(id) {
    if (!available.current || work.current.has(id)) return null;
    const controller = new AbortController();
    work.current.set(id, controller);
    update(id, { busy: true });
    return controller;
  }

  function current(id, controller) {
    return available.current && work.current.get(id) === controller && !controller.signal.aborted;
  }

  function finish(id, controller) {
    if (!current(id, controller)) return;
    work.current.delete(id);
    update(id, { busy: false });
  }

  function reportError(error) {
    if (error?.status === 401 || error?.status === 403) void session.reloadPermissions().catch(() => {});
  }

  async function save(id) {
    const record = records[id] ?? emptyRecord;
    if (record.outcome?.status === "unconfirmed") return false;
    if (!hasEdits(record)) {
      update(id, { editing: false, baseline: null, outcome: null });
      return true;
    }
    if (!record.baseline || record.outcome?.status === "conflict" || record.outcome?.conflicts?.length) return false;
    const allowed = allowedFields(record.status, rights.current);
    if (Object.keys(record.changes).some((key) => !allowed.includes(key))) return false;
    const controller = start(id);
    if (!controller) return false;
    update(id, { editError: null, outcome: null, confirmed: false });
    try {
      const outcome = await saveTicketFields(api, id, record.baseline, record.changes, { signal: controller.signal });
      if (!current(id, controller)) return false;
      const completed = outcome.status === "saved" || outcome.status === "unchanged";
      const verified = new Set([...(outcome.applied ?? []), ...(outcome.matched ?? [])]);
      if (outcome.status === "unconfirmed") verified.delete(outcome.uncertainField);
      const baseline = { ...record.baseline };
      const currentFields = outcome.ticket ? editableFields(outcome.ticket) : {};
      for (const field of verified) baseline[field] = Object.hasOwn(currentFields, field) ? currentFields[field] : record.changes[field];
      const changes = Object.fromEntries(Object.entries(record.changes).filter(([field]) => !verified.has(field)));
      update(id, (entry) => ({
        ...entry,
        baseline: completed ? null : baseline,
        changes: completed ? {} : changes,
        editing: !completed,
        outcome: completed ? null : outcome,
        editError: outcome.error ?? null,
        confirmed: completed,
        revision: entry.revision + Number(Boolean(outcome.ticket || verified.size)),
      }));
      if (outcome.ticket || verified.size) onChanged();
      reportError(outcome.error);
      return completed;
    } catch (error) {
      if (current(id, controller)) {
        update(id, { editError: error });
        reportError(error);
      }
      return false;
    } finally {
      finish(id, controller);
    }
  }

  async function check(id) {
    const record = records[id];
    const field = record?.outcome?.uncertainField;
    if (!record || !field) return;
    const controller = start(id);
    if (!controller) return;
    try {
      const ticket = await api.get(id, { signal: controller.signal });
      if (!current(id, controller)) return;
      const latest = editableFields(ticket);
      const changes = { ...record.changes };
      const baseline = { ...record.baseline };
      const desired = editableFields({ ...baseline, ...changes });
      const observed = record.outcome.ticket ? editableFields(record.outcome.ticket) : {};
      if (Object.hasOwn(changes, field) && latest[field] === desired[field]) {
        baseline[field] = latest[field];
        delete changes[field];
      }
      const conflicts = Object.keys(changes).filter((key) => latest[key] !== desired[key]
        && (latest[key] !== baseline[key] || (key === field && observed[key] === desired[key])));
      const done = !Object.keys(changes).length;
      update(id, (entry) => ({
        ...entry, baseline: done ? null : baseline, changes, editing: !done, confirmed: done, editError: null,
        outcome: conflicts.length ? { status: "conflict", conflicts, ticket } : null,
        revision: entry.revision + 1,
      }));
      onChanged();
    } catch (error) {
      if (current(id, controller)) update(id, { editError: error });
    } finally {
      finish(id, controller);
    }
  }

  async function addComment(id, text) {
    const record = records[id] ?? emptyRecord;
    const sameIntent = record.commentIntent?.text === text;
    const replay = record.commentUncertain && sameIntent && rights.current.includes("ticket.operation");
    if (!canPostComment(record.status, rights.current, record.closed) && !replay) return false;
    if (!text || Array.from(text).length > 1000) return false;
    if (record.commentUncertain && record.commentIntent?.text !== text) return false;
    const reuse = sameIntent && withinReplayWindow(record.commentIntent);
    if (record.commentUncertain && !reuse) {
      update(id, { commentError: new ApiError(0, "replay-expired") });
      return false;
    }
    const intent = reuse ? record.commentIntent : { text, key: operationKey(), startedAt: Date.now() };
    const controller = start(id);
    if (!controller) return false;
    update(id, { commentIntent: intent, commentError: null, commentSent: false });
    try {
      await api.addComment(id, text, { idempotencyKey: intent.key, signal: controller.signal });
      if (!current(id, controller)) return false;
      // A replay is a snapshot from the original write. The next GET provides current history.
      update(id, (entry) => ({
        ...entry, comment: "", commentIntent: null, commentUncertain: false,
        commentSent: true, revision: entry.revision + 1,
      }));
      onChanged();
      return true;
    } catch (error) {
      if (current(id, controller)) {
        update(id, { commentError: error, commentUncertain: record.commentUncertain || isUnknownWrite(error) });
        reportError(error);
      }
      return false;
    } finally {
      finish(id, controller);
    }
  }

  function setComment(id, comment) {
    update(id, (record) => record.busy || record.commentUncertain ? record
      : { ...record, comment, commentError: null, commentSent: false });
  }

  function setWorkflowForm(id, form) {
    update(id, (record) => {
      if (record.busy) return record;
      const feedback = record.workflowFeedback;
      return {
        ...record, workflowForm: form,
        workflowFeedback: feedback?.status === "unconfirmed" || feedback?.status === "conflict"
          || form?.action === record.workflowForm?.action ? feedback : null,
      };
    });
  }

  async function runWorkflow(ticket, action, payload) {
    const id = ticket.ticket_id;
    const deleting = action === "deleteTicket";
    const record = records[id] ?? emptyRecord;
    if (["unconfirmed", "conflict"].includes(record.workflowFeedback?.status)) return;
    const canRun = (data) => availableActions(data, { permissions: rights.current, actorId }).includes(action);
    if (!canRun(ticket)) return;
    const controller = start(id);
    if (!controller) return;
    const signal = workflowApi.bindSignal(controller.signal);
    const feedback = (status, key) => ({ status, message: t(key) });
    let intent = null;
    update(id, { workflowFeedback: null });
    try {
      const before = await api.get(id, { signal });
      if (!current(id, controller) || signal.aborted) return;
      if (!sameWorkflowState(ticket, before) || !canRun(before) || (deleting && before.user_ticket_id !== ticket.user_ticket_id)) {
        update(id, (entry) => ({ ...entry, workflowFeedback: feedback("conflict", "workflow.conflict"), revision: entry.revision + 1 }));
        onChanged();
        return;
      }
      intent = { before, action, payload };
      if (deleting) {
        await api.remove(id, { signal });
        if (!current(id, controller) || signal.aborted) return;
        onChanged();
        return true;
      }
      const result = await workflowApi.execute(id, action, payload, { signal });
      if (!current(id, controller) || signal.aborted) return;
      if (!confirmsWorkflow(result, before, action, payload, actorId)) {
        throw new ApiError(200, "invalid-response");
      }
      update(id, (entry) => ({
        ...entry, workflowForm: null,
        workflowFeedback: feedback("success", action === "startRemoteWork" ? "workflow.startedHotline" : "workflow.succeeded"),
        revision: entry.revision + 1,
      }));
      onChanged();
    } catch (error) {
      if (!current(id, controller) || signal.aborted) return;
      const pending = intent && isUnknownWrite(error) ? intent : null;
      const result = pending
        ? feedback("unconfirmed", "workflow.unconfirmed")
        : error?.status === 409 && intent
          ? feedback("conflict", "workflow.conflict")
          : feedback("rejected", !intent ? "workflow.preReadFailed"
            : error?.status === 403 ? "work.writeForbidden"
              : action === "startRemoteWork" && error?.status === 400 ? "workflow.hotlineRejected" : "workflow.rejected");
      update(id, (entry) => ({
        ...entry, workflowFeedback: result, workflowPending: pending,
        revision: entry.revision + (pending && deleting ? 0 : 1),
      }));
      onChanged();
      reportError(error);
    } finally {
      finish(id, controller);
    }
  }

  async function reloadWorkflow(id) {
    const controller = start(id);
    if (!controller) return;
    const pending = records[id]?.workflowPending;
    const signal = api.bindSignal(controller.signal);
    try {
      const latest = await api.get(id, { signal });
      if (!current(id, controller) || signal.aborted) return;
      if (pending?.action === "deleteTicket") {
        remember(id, latest);
        update(id, { workflowFeedback: { status: "unconfirmed", message: t("workflow.deleteStillUnconfirmed") } });
        return;
      }
      const observed = pending && confirmsWorkflow(latest, pending.before, pending.action, pending.payload, actorId);
      const unchanged = pending && !observed && sameWorkflowHistory(pending.before, latest);
      const feedback = observed ? { status: "success", message: t("workflow.observed") }
        : pending ? { status: "unconfirmed", message: t(unchanged ? "workflow.stillUnconfirmed" : "workflow.differentState") }
          : { status: "success", message: t("workflow.reloaded") };
      remember(id, latest);
      update(id, (entry) => ({
        ...entry, workflowFeedback: feedback,
        workflowForm: observed ? null : entry.workflowForm,
        workflowPending: observed ? null : pending,
        revision: entry.revision + 1,
      }));
      onChanged();
    } catch (error) {
      if (current(id, controller) && !signal.aborted) {
        if (pending?.action === "deleteTicket" && error?.status === 404 && rights.current.includes("ticket.view")) {
          update(id, { workflowPending: null, workflowFeedback: null });
          onChanged();
          return true;
        }
        update(id, { workflowFeedback: { status: pending ? "unconfirmed" : "conflict", message: errorText(error) } });
        reportError(error);
      }
    } finally {
      finish(id, controller);
    }
  }

  return {
    records, openIds, record: (id) => records[id] ?? emptyRecord,
    update, open, close, remember, beginEdit, change, save, check, adoptLatest, setComment, addComment,
    setWorkflowForm, runWorkflow, reloadWorkflow,
  };
}
