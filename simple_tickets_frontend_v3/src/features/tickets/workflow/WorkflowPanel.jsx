import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { ConfirmationDialog } from "../../../app/layout.jsx";
import { t } from "../../../shared/i18n/messages.js";
import { normalizeStatus } from "../model.js";
import { allowedExecutors, availableActions, defaultWorkMode, workModes } from "./policy.js";
import "./workflow.css";

const HOTLINE = "startRemoteWork";
const ASSIGN = "assign";
const RETRO = "registerWork";
const MAX_COMMENT_LENGTH = 1000;
const REQUIRES_REASON = new Set(["reject", "defer", "cancel"]);
const FEEDBACK_KEYS = {
  success: "workflow.success",
  rejected: "workflow.rejected",
  unconfirmed: "workflow.unconfirmed",
  conflict: "workflow.changed",
};

function useAdministrators(api, enabled) {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState(null);
  useEffect(() => {
    if (!enabled || typeof api?.admins !== "function") return undefined;
    const controller = new AbortController();
    const { signal } = controller;
    async function load() {
      try {
        const admins = await api.admins({ signal });
        if (!signal.aborted) setResult({ api, attempt, phase: "ready", admins });
      } catch (error) {
        if (!signal.aborted) {
          setResult({ api, attempt, phase: error?.status === 403 ? "forbidden" : "error", admins: [] });
        }
      }
    }
    load();
    return () => controller.abort();
  }, [api, attempt, enabled]);

  if (!enabled || typeof api?.admins !== "function") return { phase: "forbidden", admins: [] };
  return {
    ...(result?.api === api && result.attempt === attempt ? result : { phase: "loading", admins: [] }),
    retry: () => setAttempt((value) => value + 1),
  };
}

function Field({ label, name, error, hint, required, children }) {
  const id = useId();
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ");
  return (
    <div className="workflow-field">
      <label htmlFor={id}>
        {label}{required && <span className="workflow-required" aria-hidden="true"> *</span>}
      </label>
      {children({
        id, name, required,
        "aria-invalid": error ? true : undefined,
        "aria-describedby": describedBy || undefined,
      })}
      {hint && <p id={`${id}-hint`} className="workflow-hint">{hint}</p>}
      {error && <p id={`${id}-error`} className="field-error">{error}</p>}
    </div>
  );
}

function candidateLabel(admin) {
  const name = [admin.first_name, admin.last_name].filter(Boolean).join(" ");
  return name
    ? t("ticketForm.optionIdentity", { name, id: admin.employee_id })
    : t("common.identifier", { id: admin.employee_id });
}

function ExecutorField({ catalog, candidates, value, onChange, error, locked }) {
  const control = useRef(null);
  const options = candidates ?? [];
  const disabled = locked || !options.length;
  const known = options.some((candidate) => candidate.employee_id === value);
  const hint = {
    loading: t("common.loading"),
    forbidden: t("workflow.executorCatalogForbidden"),
    error: t("workflow.executorCatalogError"),
  }[catalog.phase] ?? (options.length ? "" : t("workflow.noExecutors"));

  return (
    <>
      <Field label={t("workflow.executor")} name="executorId" required error={error} hint={hint}>
        {(attributes) => (
          <select {...attributes} ref={control} value={value || ""}
            aria-disabled={disabled}
            onPointerDown={(event) => { if (disabled) event.preventDefault(); }}
            onKeyDown={(event) => {
              if (disabled && !["Tab", "Escape"].includes(event.key)) event.preventDefault();
            }}
            onChange={(event) => {
              if (!disabled) onChange(Number(event.target.value));
            }}>
            <option value="">{t("workflow.selectExecutor")}</option>
            {value > 0 && !known && (
              <option value={value} disabled>{t("common.identifier", { id: value })}</option>
            )}
            {options.map((admin) => (
              <option value={admin.employee_id} key={admin.employee_id}>{candidateLabel(admin)}</option>
            ))}
          </select>
        )}
      </Field>
      {catalog.phase === "error" && !locked && (
        <button className="btn workflow-retry" type="button" onClick={() => {
          control.current?.focus();
          catalog.retry();
        }}>{t("common.retry")}</button>
      )}
    </>
  );
}

function RetroFields({ form, update, errors, locked }) {
  const id = useId();
  return (
    <fieldset className="workflow-retro-fields">
      <legend>{t("workflow.retroMode")}</legend>
      <div className="workflow-retro-mode">
        {["interval", "duration"].map((mode) => (
          <label key={mode}>
            <input type="radio" name={`${id}-retro-mode`} value={mode} disabled={locked}
              checked={form.retroMode === mode} onChange={() => update("retroMode", mode)} />
            {t(`workflow.${mode}`)}
          </label>
        ))}
      </div>
      {form.retroMode === "interval" ? (
        <div className="workflow-retro-grid">
          {["startLocal", "finishLocal"].map((field) => (
            <Field key={field} name={field} label={t(field === "startLocal" ? "workflow.start" : "workflow.finish")}
              required error={errors[field]} hint={field === "startLocal" ? t("workflow.localTime") : ""}>
              {(attributes) => (
                <input {...attributes} type="datetime-local" value={form[field] ?? ""} readOnly={locked}
                  onChange={(event) => update(field, event.target.value)} />
              )}
            </Field>
          ))}
        </div>
      ) : (
        <div className="workflow-retro-grid">
          {["hours", "minutes"].map((field) => (
            <Field key={field} name={field} label={t(`workflow.${field}`)} error={errors[field]}>
              {(attributes) => (
                <input {...attributes} type="number" step="1" min="0" max={field === "minutes" ? 59 : undefined}
                  value={form[field] ?? ""} readOnly={locked} onChange={(event) => update(field, event.target.value)} />
              )}
            </Field>
          ))}
        </div>
      )}
    </fieldset>
  );
}

function readLocalTime(value) {
  const time = new Date(value);
  if (!Number.isFinite(time.getTime())) return NaN;
  const local = new Date(time.getTime() - time.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, value.length) === value ? time.getTime() : NaN;
}

function buildPayload(form, candidates, modes) {
  const { action } = form;
  const comment = (form.comment ?? "").trim();
  const errors = {};
  const payload = comment ? { comment } : {};
  if (REQUIRES_REASON.has(action) && !comment) errors.comment = t("workflow.reasonRequired");
  else if (Array.from(comment).length > MAX_COMMENT_LENGTH) {
    errors.comment = t("workflow.commentTooLong", { max: MAX_COMMENT_LENGTH });
  }
  if (action === ASSIGN) {
    if (candidates.some((admin) => admin.employee_id === form.executorId)) {
      payload.executor_id = form.executorId;
    } else {
      errors.executorId = t("workflow.executorRequired");
    }
  }
  if (modes.length) payload.work_is_remote = modes.length === 1 ? modes[0] : Boolean(form.remote);
  if (action === RETRO) {
    if (form.retroMode === "interval") {
      const start = readLocalTime(form.startLocal);
      const finish = readLocalTime(form.finishLocal);
      if (!Number.isFinite(start)) errors.startLocal = t("workflow.invalidInterval");
      else if (!Number.isFinite(finish) || finish <= start || finish > Date.now()) {
        errors.finishLocal = t("workflow.invalidInterval");
      } else {
        payload.actual_started_at = new Date(start).toISOString();
        payload.actual_finished_at = new Date(finish).toISOString();
      }
    } else {
      const hours = Number(form.hours ?? "");
      const minutes = Number(form.minutes ?? "");
      const duration = hours * 3600 + minutes * 60;
      if (!Number.isSafeInteger(hours) || hours < 0) errors.hours = t("workflow.invalidDuration");
      else if (!Number.isSafeInteger(minutes) || minutes < 0 || minutes > 59) {
        errors.minutes = t("workflow.invalidDuration");
      } else if (!Number.isSafeInteger(duration) || duration <= 0) {
        errors.hours = t("workflow.invalidDuration");
      } else {
        payload.duration = duration;
      }
    }
  }
  return { errors, payload };
}

function ActionForm({
  form, heading, ticket, actorId, api, permissions, busy, blocked, allowed, onChange, onRun, onBack,
}) {
  const id = useId();
  const { action } = form;
  const [errors, setErrors] = useState({});
  const modes = workModes(ticket, action, { permissions });
  const catalog = useAdministrators(api, action === ASSIGN && allowed);
  const candidates = action === ASSIGN ? allowedExecutors(ticket, catalog.admins, { actorId }) : [];
  const locked = busy || blocked || !allowed;
  const canSubmit = !locked && (action !== ASSIGN || candidates.length > 0);
  const required = REQUIRES_REASON.has(action);
  const remote = modes.length === 1 ? modes[0] : Boolean(form.remote);

  function update(name, value) {
    setErrors((current) => {
      if (!current[name]) return current;
      const next = { ...current };
      delete next[name];
      return next;
    });
    onChange({ ...form, [name]: value });
  }

  function submit(event) {
    event.preventDefault();
    if (!canSubmit) return;
    const result = buildPayload(form, candidates, modes);
    setErrors(result.errors);
    const first = Object.keys(result.errors)[0];
    if (first) event.currentTarget.elements.namedItem(first)?.focus();
    else onRun(action, result.payload);
  }

  return (
    <form onSubmit={submit} noValidate className="workflow-form"
      aria-labelledby={`${id}-heading`} aria-busy={busy}>
      <h3 id={`${id}-heading`} tabIndex={-1} ref={heading}>{t(`workflow.${action}`)}</h3>
      <p>{t(`workflow.${action}.help`)}</p>
      <p className="visually-hidden" aria-live="assertive" aria-atomic="true">{Object.values(errors)[0] ?? ""}</p>
      {!allowed && <p role="status" className="workflow-hint">{t("workflow.actionUnavailable")}</p>}
      {action === ASSIGN && (
        <ExecutorField catalog={catalog} candidates={candidates} value={form.executorId}
          onChange={(value) => update("executorId", value)} error={errors.executorId} locked={locked} />
      )}
      {modes.length > 0 && (
        <div className="workflow-field">
          <label className="workflow-checkbox">
            <input type="checkbox" checked={remote} disabled={locked || modes.length === 1}
              aria-describedby={modes.length === 1 ? `${id}-mode` : undefined}
              onChange={(event) => update("remote", event.target.checked)} />
            {t("workflow.remote")}
          </label>
          {modes.length === 1 && <p id={`${id}-mode`} className="workflow-hint">
            {t(remote ? "workflow.remoteOnly" : "workflow.localOnly")}
          </p>}
        </div>
      )}
      {action === RETRO && <RetroFields form={form} update={update} errors={errors} locked={locked} />}
      <Field label={t(required ? "workflow.reason" : "workflow.comment")} name="comment"
        required={required} error={errors.comment}>
        {(attributes) => (
          <textarea {...attributes} rows={3} value={form.comment ?? ""} readOnly={locked}
            onChange={(event) => update("comment", event.target.value)} />
        )}
      </Field>
      <div className="workflow-actions">
        {allowed && <button className="btn btn-primary" type="submit" aria-disabled={!canSubmit}>
          {t(busy ? "workflow.pending" : "workflow.confirm")}
        </button>}
        <button className="btn" type="button" aria-disabled={busy} onClick={() => { if (!busy) onBack(); }}>
          {t("workflow.back")}
        </button>
      </div>
    </form>
  );
}

function unavailableHotline(ticket, permissions, actorId, actorDepartmentId) {
  if (!ticket.remote_work_recommended || !permissions.includes("ticket.at_work_remote")) return "";
  const status = normalizeStatus(ticket.status ?? ticket.statuses?.at(-1)?.status);
  if (status === "accepted") {
    if (!(ticket.department_id > 0)) return t("workflow.startRemoteWork.noDepartment");
    if (Number.isSafeInteger(actorDepartmentId) && actorDepartmentId !== ticket.department_id) {
      return t("workflow.startRemoteWork.wrongDepartment");
    }
  }
  if (status === "assigned" && ticket.current_executor_id !== actorId) {
    return t("workflow.startRemoteWork.otherExecutor");
  }
  return "";
}

export default function WorkflowPanel({
  ticket,
  permissions = [],
  actorId,
  actorDepartmentId,
  api,
  onRun,
  busy = false,
  feedback = null,
  onReload,
  form = null,
  onFormChange,
}) {
  const id = useId();
  const section = useRef(null);
  const formHeading = useRef(null);
  const pendingFocus = useRef(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const actions = availableActions(ticket, { permissions, actorId, actorDepartmentId });
  const blocked = feedback?.status === "unconfirmed" || feedback?.status === "conflict";
  const hotline = actions.includes(HOTLINE);
  const hotlineReason = hotline ? "" : unavailableHotline(ticket, permissions, actorId, actorDepartmentId);
  const formAction = form?.action;

  useLayoutEffect(() => {
    const next = pendingFocus.current;
    if (next === "form" && formAction) {
      pendingFocus.current = null;
      formHeading.current?.focus();
    } else if (next && next !== "form" && !formAction) {
      pendingFocus.current = null;
      (section.current?.querySelector(`[data-workflow-action="${next}"]`)
        ?? section.current?.querySelector("h2"))?.focus();
    } else if (!formAction && feedback?.status === "success" && document.activeElement === document.body) {
      section.current?.querySelector("h2")?.focus();
    }
  }, [formAction, feedback?.status]);

  function open(action) {
    if (busy || blocked) return;
    if (action === "deleteTicket") {
      setConfirmingDelete(true);
      return;
    }
    if (action === HOTLINE) {
      section.current?.querySelector("h2")?.focus();
      onRun(action, {});
      return;
    }
    const modes = workModes(ticket, action, { permissions });
    const previousMode = defaultWorkMode(ticket);
    const remote = modes.includes(previousMode) ? previousMode : modes[0];
    pendingFocus.current = "form";
    onFormChange({
      action, comment: "", executorId: 0, remote, initialRemote: remote, retroMode: "interval",
      startLocal: "", finishLocal: "", hours: "", minutes: "",
    });
  }

  if (!actions.length && !formAction && !feedback && !hotlineReason) return null;
  return (
    <section ref={section} className="panel detail-panel workflow-panel" aria-labelledby={`${id}-heading`}>
      <h2 id={`${id}-heading`} tabIndex={-1}>{t("workflow.title")}</h2>
      {confirmingDelete && actions.includes("deleteTicket") && (
        <ConfirmationDialog title={t("workflow.deleteTicket")}
          description={t(ticket.user_ticket_id ? "workflow.deleteTicket.linked" : "workflow.deleteTicket.help", { id: ticket.ticket_id })}
          confirmLabel={t("workflow.deleteTicket.confirm")} busy={busy}
          onCancel={() => setConfirmingDelete(false)} onConfirm={() => {
            setConfirmingDelete(false);
            onRun("deleteTicket", {});
          }} />
      )}
      {feedback && (
        <div className="workflow-feedback" data-error={feedback.status !== "success" || undefined}>
          <p role={feedback.status === "success" ? "status" : "alert"}>
            {feedback.message || t(FEEDBACK_KEYS[feedback.status] ?? "error.generic")}
          </p>
          {blocked && onReload && (
            <button className="btn workflow-retry" type="button" aria-disabled={busy}
              onClick={() => {
                if (busy) return;
                section.current?.querySelector("h2")?.focus();
                onReload();
              }}>{t("workflow.reload")}</button>
          )}
        </div>
      )}
      {formAction ? (
        <ActionForm key={formAction} form={form} heading={formHeading} ticket={ticket} actorId={actorId}
          api={api} permissions={permissions} busy={busy} blocked={blocked} allowed={actions.includes(formAction)}
          onChange={onFormChange} onRun={onRun} onBack={() => {
            pendingFocus.current = formAction;
            onFormChange(null);
          }} />
      ) : (
        <>
          {hotlineReason && <p className="workflow-hint">{hotlineReason}</p>}
          {actions.length > 0 && (
            <div className="workflow-actions">
              {actions.map((action) => (
                <button key={action} type="button" data-workflow-action={action}
                  className={action === HOTLINE ? "btn btn-primary" : "btn"} aria-disabled={busy || blocked}
                  aria-describedby={action === HOTLINE ? `${id}-hotline` : undefined}
                  onClick={() => open(action)}>{t(`workflow.${action}`)}</button>
              ))}
            </div>
          )}
          {hotline && <p className="workflow-hint" id={`${id}-hotline`}>
            {t("workflow.startRemoteWork.help")}
          </p>}
          {busy && <p className="workflow-hint" role="status">{t("workflow.pending")}</p>}
        </>
      )}
    </section>
  );
}
