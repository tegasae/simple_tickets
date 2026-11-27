import { useEffect, useId, useRef, useState } from "react";
import { locale, renderMessage, t } from "../../shared/i18n/messages.js";
import { urgencyLabel } from "./model.js";
import "./fields.css";

const MAX_TEXT_LENGTH = 4000;
const MAX_COMMENT_LENGTH = 1000;
const urgencies = ["normal", "urgent", "maintenance"];
const emptyFieldErrors = Object.freeze({});

function useCatalog(api, resource, allowed, clientId = 0) {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState(null);
  const available = typeof api?.[resource] === "function";
  const needsClient = resource === "users" && !clientId;
  const enabled = allowed && available && !needsClient;

  useEffect(() => {
    if (!enabled) return undefined;
    const controller = new AbortController();
    const { signal } = controller;
    async function read() {
      try {
        const rows = resource === "users"
          ? await api.users(clientId, { signal })
          : await api[resource]({ signal });
        if (!signal.aborted) setResult({ api, attempt, clientId, phase: "ready", rows });
      } catch (error) {
        if (!signal.aborted) {
          setResult({
            api, attempt, clientId, phase: error?.status === 403 ? "forbidden" : "error", rows: [],
          });
        }
      }
    }
    read();
    return () => controller.abort();
  }, [api, resource, enabled, clientId, attempt]);

  if (!allowed) return { phase: "forbidden", rows: [] };
  if (needsClient) return { phase: "needsClient", rows: [] };
  if (!available) return { phase: "unavailable", rows: [] };

  return {
    ...(result?.api === api && result.attempt === attempt && result.clientId === clientId
      ? result
      : { phase: "loading", rows: [] }),
    retry: () => setAttempt((value) => value + 1),
  };
}

function Field({ label, hint, error, required, wide, name, children }) {
  const id = useId();
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ");
  const attributes = {
    id,
    name,
    "aria-describedby": describedBy || undefined,
    "aria-invalid": error ? true : undefined,
  };

  return (
    <div className={wide ? "ticket-form-field ticket-form-wide" : "ticket-form-field"}>
      <label htmlFor={id}>
        {label}{required && <span className="ticket-required-mark" aria-hidden="true"> *</span>}
      </label>
      {children(attributes)}
      {hint && <p className="ticket-field-help" id={`${id}-hint`}>{hint}</p>}
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
    </div>
  );
}

function normalizeSearch(value) {
  return value.toLocaleLowerCase(locale).replaceAll("ё", "е");
}

function Lookup({
  attributes, label, selectedId, onSelect, catalog, options, required, locked, canClear,
}) {
  const [search, setSearch] = useState(null);
  const [open, setOpen] = useState(false);
  const [activeId, setActiveId] = useState(null);
  const input = useRef(null);
  const activeOption = useRef(null);
  const listId = `${attributes.id}-options`;
  const selected = options.find((option) => option.id === selectedId);
  const selectedLabel = selected
    ? selected.enabled ? selected.label : t("ticketForm.inactiveSelection", { name: selected.label })
    : selectedId ? t("common.identifier", { id: selectedId }) : "";
  const query = normalizeSearch((search ?? "").trim());
  const availableOptions = options.filter((option) => option.enabled);
  const matches = availableOptions.filter((option) => normalizeSearch(option.label).includes(query));
  const canChoose = !locked && catalog.phase === "ready" && availableOptions.length > 0;
  const expanded = open && canChoose;
  const activeIndex = matches.findIndex((option) => option.id === activeId);
  const active = expanded ? matches[activeIndex] : undefined;

  useEffect(() => {
    if (expanded && active) activeOption.current?.scrollIntoView({ block: "nearest" });
  }, [expanded, active?.id]);

  function close() {
    setSearch(null);
    setActiveId(null);
    setOpen(false);
  }

  function choose(id) {
    onSelect(id);
    close();
  }

  function keyDown(event) {
    if (!canChoose) return;
    if (event.key === "Escape" && expanded) {
      event.preventDefault();
      event.stopPropagation();
      close();
    } else if (event.key === "Enter" && expanded && (active || search !== null)) {
      event.preventDefault();
      if (active) choose(active.id);
    } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      if (matches.length) {
        const next = event.key === "ArrowDown"
          ? (activeIndex + 1) % matches.length
          : (activeIndex <= 0 ? matches.length : activeIndex) - 1;
        setActiveId(matches[next].id);
      }
    }
  }

  return (
    <>
      <div className="ticket-option-control">
        <div className="ticket-option-anchor">
          <input {...attributes} ref={input} role="combobox" type="text" autoComplete="off"
            aria-autocomplete="list" aria-expanded={expanded}
            aria-controls={expanded ? listId : undefined}
            aria-activedescendant={active ? `${listId}-${active.id}` : undefined}
            aria-required={required || undefined}
            value={search ?? selectedLabel}
            readOnly={!canChoose}
            placeholder={canChoose ? t("ticketForm.searchOptions") : undefined}
            onFocus={(event) => {
              setOpen(true);
              if (canChoose && search === null && selectedId) event.currentTarget.select();
            }}
            onClick={() => setOpen(true)} onBlur={close} onKeyDown={keyDown}
            onChange={(event) => {
              setSearch(event.target.value);
              setActiveId(null);
              setOpen(true);
            }} />
          {expanded && (
            <ul className="ticket-option-list" id={listId} role="listbox" aria-label={label}>
              {matches.map((option) => (
                <li key={option.id} id={`${listId}-${option.id}`}
                  ref={option.id === active?.id ? activeOption : undefined} role="option"
                  aria-selected={option.id === active?.id}
                  onMouseDown={(event) => event.preventDefault()} onClick={() => choose(option.id)}>
                  {option.label}
                </li>
              ))}
              {!matches.length && <li role="presentation" className="ticket-field-help">
                {t("ticketForm.noMatches")}
              </li>}
            </ul>
          )}
        </div>
        {canClear && !locked && selectedId > 0 && (
          <button className="btn" type="button"
            aria-label={t("ticketForm.clearSelection", { label })}
            onClick={() => {
              choose(0);
              input.current?.focus();
            }}>{t("ticketForm.clear")}</button>
        )}
      </div>
      <p className="visually-hidden" role="status" aria-atomic="true">
        {expanded && (matches.length
          ? t("ticketForm.optionsCount", { count: matches.length })
          : t("ticketForm.noMatches"))}
      </p>
      {catalog.phase === "error" && !locked && (
        <div className="ticket-form-catalog-error">
          <button className="btn" type="button" onClick={() => {
            input.current?.focus();
            catalog.retry();
          }}>{t("common.retry")}</button>
        </div>
      )}
    </>
  );
}

function catalogHint(catalog, extra) {
  switch (catalog.phase) {
    case "forbidden": return t("ticketForm.selectionUnavailable");
    case "unavailable": return t("ticketForm.catalogUnavailable");
    case "error": return t("ticketForm.catalogFailed");
    case "loading": return t("common.loading");
    case "needsClient": return t("ticketForm.chooseClientFirst");
    default: return extra;
  }
}

function option(row, id, name) {
  const label = name
    ? t("ticketForm.optionIdentity", { name, id })
    : t("common.identifier", { id });
  return { id, label, enabled: row.enabled === true };
}

function localDate(value) {
  if (!value) return "";
  const timestamp = new Date(value);
  if (!Number.isFinite(timestamp.getTime())) return "";
  return new Date(timestamp.getTime() - timestamp.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

function codePoints(value = "") {
  return Array.from(value.trim()).length;
}

export default function TicketFields({
  mode = "create",
  values,
  onChange,
  onSubmit,
  onCancel,
  busy = false,
  locked = false,
  hideSubmit = false,
  submitLabel,
  error = "",
  fieldErrors = emptyFieldErrors,
  referencesApi,
  permissions = [],
}) {
  const creating = mode === "create";
  const canOperate = creating || permissions.includes("ticket.operation");
  const canRecommend = permissions.includes("ticket.set_remote_recommendation");
  const form = useRef(null);
  const recommendationErrorId = useId();
  const [validation, setValidation] = useState(emptyFieldErrors);
  const [referenceNotice, setReferenceNotice] = useState("");
  const fieldsLocked = busy || locked;
  const clients = useCatalog(referencesApi, "clients", creating && permissions.includes("client.view"));
  const users = useCatalog(referencesApi, "users", canOperate && permissions.includes("user.view"), values.client_id);
  const departments = useCatalog(
    referencesApi, "departments", canOperate && permissions.includes("department.view"),
  );
  const clientOptions = clients.rows.map((row) => option(row, row.client_id, row.name));
  const userOptions = users.rows.filter((row) => row.client_id === values.client_id).map((row) =>
    option(row, row.employee_id, [row.first_name, row.last_name].filter(Boolean).join(" ")));
  const departmentOptions = departments.rows.map((row) => option(row, row.department_id, row.name));
  const requiredContact = !creating && values.user_id > 0;
  const issues = Object.fromEntries(Object.entries({ ...fieldErrors, ...validation })
    .map(([name, problem]) => [name, renderMessage(problem)]));
  const hasIssues = Object.values(issues).some(Boolean);

  function update(name, value) {
    setValidation((current) => {
      if (!(name in current)) return current;
      const next = { ...current };
      delete next[name];
      return next;
    });
    if (name === "client_id" && value !== values.client_id) {
      setReferenceNotice(values.user_id || values.contact_user_id ? "ticketForm.clientChanged" : "");
    }
    onChange(name, value);
  }

  function submit(event) {
    event.preventDefault();
    if (busy || hideSubmit) return;
    if (locked) {
      onSubmit();
      return;
    }
    const elements = event.currentTarget.elements;
    const problems = {};
    if (creating) {
      if (!clientOptions.some((item) => item.id === values.client_id && item.enabled)) {
        problems.client_id = { key: "ticketForm.clientRequired" };
      }
      const length = codePoints(values.text_of_ticket);
      if (length < 2 || length > MAX_TEXT_LENGTH) {
        problems.text_of_ticket = { key: "ticketForm.subjectLength", params: { max: MAX_TEXT_LENGTH } };
      }
      if (codePoints(values.comment) > MAX_COMMENT_LENGTH) {
        problems.comment = { key: "ticketForm.commentLength", params: { max: MAX_COMMENT_LENGTH } };
      }
    }
    if (canOperate) {
      if (codePoints(values.description) > MAX_TEXT_LENGTH) {
        problems.description = { key: "ticketForm.descriptionLength", params: { max: MAX_TEXT_LENGTH } };
      }
      if (requiredContact && !values.contact_user_id) problems.contact_user_id = { key: "ticketForm.chooseContact" };
      if (elements.namedItem("planned_at")?.validity.badInput) {
        problems.planned_at = { key: "ticketForm.invalidDate" };
      }
    }
    setValidation(problems);
    const firstProblem = Object.keys(problems)[0];
    if (firstProblem) elements.namedItem(firstProblem)?.focus();
    else onSubmit();
  }

  const invalidNames = Object.keys(fieldErrors).filter((name) => fieldErrors[name]).join(" ");
  useEffect(() => {
    if (busy || locked) return;
    const name = invalidNames.split(" ").find((key) => key && form.current?.elements.namedItem(key));
    if (name) form.current?.elements.namedItem(name)?.focus();
  }, [invalidNames, busy, locked]);

  function catalogField(name, label, catalog, options, { required = false, extra } = {}) {
    const hint = catalog.phase === "ready" && !options.some((item) => item.enabled)
      ? t("ticketForm.noOptions")
      : catalogHint(catalog, extra);
    return (
      <Field name={name} label={label} required={required} error={issues[name]} hint={hint}>
        {(attributes) => <Lookup attributes={attributes} label={label} catalog={catalog} options={options}
          required={required} selectedId={values[name] ?? 0} locked={fieldsLocked} canClear={!required}
          onSelect={(value) => update(name, value)} />}
      </Field>
    );
  }

  function textField(name, label, rows, required = false) {
    return (
      <Field name={name} label={label} required={required} error={issues[name]} wide>
        {(attributes) => <textarea {...attributes} rows={rows} value={values[name] ?? ""}
          required={required} readOnly={fieldsLocked}
          onChange={(event) => update(name, event.target.value)} />}
      </Field>
    );
  }

  return (
    <form ref={form} className="ticket-fields-form"
      aria-label={t(creating ? "ticketForm.create" : "ticketForm.edit")}
      aria-busy={busy} onSubmit={submit} noValidate>
      {(error || hasIssues) && <p className="field-error" role="alert">
        {error || t("ticketForm.fieldErrors")}
      </p>}
      <div className="ticket-fields-grid">
        {creating && catalogField("client_id", t("ticket.client"), clients, clientOptions, { required: true })}
        {creating && textField("text_of_ticket", t("ticketForm.subject"), 2, true)}
        {creating && catalogField("user_id", t("ticket.requester"), users, userOptions)}
        {canOperate && catalogField("contact_user_id", t("ticket.contact"), users, userOptions, {
          required: requiredContact,
          extra: creating && values.user_id && !values.contact_user_id ? t("ticketForm.contactDefault") : undefined,
        })}
        {canOperate && catalogField("department_id", t("ticket.department"), departments, departmentOptions)}
        {canOperate && textField("description", t("ticket.description"), 4)}
        {canOperate && <Field name="urgency" label={t("ticket.urgency")} error={issues.urgency}>
          {(attributes) => <select {...attributes} value={values.urgency ?? "normal"} disabled={fieldsLocked}
            onChange={(event) => update("urgency", event.target.value)}>
            {urgencies.map((value) => <option key={value} value={value}>{urgencyLabel(value)}</option>)}
          </select>}
        </Field>}
        {canOperate && <Field name="planned_at" label={t("ticket.planned")} error={issues.planned_at}
          hint={t("ticketForm.optionalDate")}>
          {(attributes) => <input {...attributes} type="datetime-local" value={localDate(values.planned_at)}
            readOnly={fieldsLocked} onChange={(event) => {
              if (event.target.validity.badInput) return;
              const value = event.target.value;
              const parsed = value ? Date.parse(value) : NaN;
              update("planned_at", Number.isFinite(parsed) ? new Date(parsed).toISOString() : null);
            }} />}
        </Field>}
        {canRecommend && <div className="ticket-form-field ticket-form-wide">
          <label className="ticket-form-checkbox">
            <input name="remote_work_recommended" type="checkbox" checked={Boolean(values.remote_work_recommended)}
              disabled={fieldsLocked} aria-invalid={issues.remote_work_recommended ? true : undefined}
              aria-describedby={issues.remote_work_recommended ? recommendationErrorId : undefined}
              onChange={(event) => update("remote_work_recommended", event.target.checked)} />
            <span>{t("ticket.remoteRecommended")}</span>
          </label>
          {issues.remote_work_recommended && <p className="field-error" id={recommendationErrorId}>
            {issues.remote_work_recommended}
          </p>}
        </div>}
        {creating && textField("comment", t("ticketForm.comment"), 3)}
      </div>
      <p className="visually-hidden" role="status" aria-atomic="true">{referenceNotice && t(referenceNotice)}</p>
      {(!hideSubmit || onCancel) && <div className="ticket-form-actions">
        {!hideSubmit && <button className="btn btn-primary" type="submit" aria-disabled={busy}>
          {busy ? t("ticketForm.saving") : submitLabel ?? t(creating ? "ticketForm.createSubmit" : "ticketForm.editSubmit")}
        </button>}
        {onCancel && <button className="btn" type="button" disabled={busy} onClick={onCancel}>
          {t("ticketForm.cancel")}
        </button>}
      </div>}
    </form>
  );
}
