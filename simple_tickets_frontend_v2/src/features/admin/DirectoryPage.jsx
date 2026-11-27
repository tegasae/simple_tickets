import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { RouteLink, StatePanel } from "../../app/layout.jsx";
import { directoryPath } from "../../app/routes.js";
import { useRemoteData } from "../../app/useRemoteData.js";
import { errorText, locale, renderMessage, t } from "../../shared/i18n/messages.js";
import { formatDateTime } from "../tickets/model.js";
import { canDirectory, DIRECTORIES, directoryFormValues, directoryLabel } from "./directoryModel.js";
import "./directory.css";

const PAGE_SIZE = 25;
const noRows = [];
const defaultFilter = { draft: "", query: "", state: "", reference: 0, page: 1, descending: false };
const referenceResources = { client_id: "clients", department_id: "departments" };
const referenceForResource = { users: "client_id", admins: "department_id" };
const aboutFields = {
  clients: ["email", "phone", "address", "description", "enabled", "date_created", "created_by_admin"],
  users: ["email", "phone", "client_id", "enabled", "login", "enabled_login", "roles", "date_created"],
  admins: ["email", "phone", "job_title", "department_id", "enabled", "login", "enabled_login", "roles", "date_created"],
  departments: ["enabled", "date_created"],
  adminRoles: ["description", "permissions", "is_system_role", "date_created"],
  userRoles: ["description", "permissions", "is_system_role"],
};

function useResource(api, resource, enabled) {
  const load = useCallback((signal) => enabled
    ? api.list(resource, { signal })
    : Promise.resolve(noRows), [api, resource, enabled]);
  return useRemoteData(enabled ? resource : null, load);
}

function useHeading() {
  const heading = useRef(null);
  useLayoutEffect(() => { heading.current?.focus(); }, []);
  return heading;
}

function BackLink({ resource, navigate, mode = "list", id }) {
  return (
    <RouteLink className="back-link" href={directoryPath(resource, mode, id)} navigate={navigate}>
      {t(mode === "detail" ? "directory.backToRecord" : "directory.back")}
    </RouteLink>
  );
}

function DirectoryReadError({ error, retry, back, page = false }) {
  const status = error?.status;
  const forbidden = status === 403;
  const missing = status === 404;
  const title = t(forbidden ? "error.forbidden" : missing ? "error.notFound" : "error.title");
  return (
    <StatePanel title={title} page={page} error
      description={forbidden ? t("directory.noRead") : missing ? t("directory.notFound") : errorText(error)}>
      {forbidden || missing ? null : <button type="button" className="btn" onClick={retry}>{t("common.retry")}</button>}
      {back}
    </StatePanel>
  );
}

function referenceLabel(row, resource, field) {
  return t("ticketForm.optionIdentity", { name: directoryLabel(resource, row), id: row[field] });
}

function valueText(field, row, references = noRows) {
  const value = row[field];
  if (field === "enabled") return t(value ? "directory.enabled" : "directory.disabled");
  if (field === "enabled_login") {
    return t(!row.login ? "directory.accountAbsent" : value ? "directory.loginEnabled" : "directory.loginDisabled");
  }
  if (field === "is_system_role") return t(value ? "directory.yes" : "directory.no");
  if (field === "date_created") return formatDateTime(value);
  if (Array.isArray(value)) return value.length ? value.join(", ") : t("common.missing");
  const resource = referenceResources[field];
  if (resource && value > 0) {
    const option = references.find((reference) => reference[field] === value);
    return option ? directoryLabel(resource, option) : t("common.identifier", { id: value });
  }
  return value || t("common.missing");
}

function DirectoryList({ resource, api, permissions, navigate, filter, setFilter, returnFocus, setReturnFocus }) {
  const spec = DIRECTORIES[resource];
  const canCreate = canDirectory(resource, "create", permissions);
  const result = useResource(api, resource, true);
  const filterField = referenceForResource[resource];
  const refResource = referenceResources[filterField];
  const references = useResource(api, refResource, Boolean(refResource && canDirectory(refResource, "read", permissions)));
  const catalog = references.phase === "ready" ? references.data : noRows;
  const heading = useHeading();
  const searchField = useRef(null);
  const rows = result.phase === "ready" ? result.data : noRows;
  const refIds = filterField ? [...new Set(rows.map((row) => row[filterField]))].filter((value) => value > 0) : [];
  const hasStatus = spec.columns.includes("enabled");
  const otherColumns = spec.columns.filter((column) => ![spec.idKey, "name", "first_name", "last_name"].includes(column));
  const normalize = (value) => String(value ?? "").toLocaleLowerCase(locale).replaceAll("ё", "е");
  const query = normalize(filter.query);
  const filtered = rows.filter((row) => {
    if (filter.reference && row[filterField] !== filter.reference) return false;
    if (hasStatus && filter.state && row.enabled !== (filter.state === "enabled")) return false;
    return !query || [directoryLabel(resource, row), row[spec.idKey], row.email, row.phone]
      .some((value) => normalize(value).includes(query));
  }).sort((left, right) => {
    const difference = directoryLabel(resource, left).localeCompare(directoryLabel(resource, right), locale);
    return (filter.descending ? -difference : difference) || left[spec.idKey] - right[spec.idKey];
  });
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const page = Math.min(filter.page, totalPages);
  const start = (page - 1) * PAGE_SIZE;
  const end = Math.min(start + PAGE_SIZE, filtered.length);
  const range = filtered.length ? t("directory.range", { start: start + 1, end, total: filtered.length }) : "";

  useLayoutEffect(() => {
    if (result.phase === "loading" || returnFocus?.resource !== resource) return;
    const target = document.getElementById(`directory-row-${returnFocus.id}`);
    if (target) {
      window.scrollTo(0, returnFocus.scroll);
      target.focus({ preventScroll: true });
    } else {
      heading.current?.focus();
    }
    setReturnFocus(null);
  }, [result.phase, returnFocus, resource, heading, setReturnFocus]);

  function patch(patch) {
    setFilter({ ...filter, ...patch, page: patch.page ?? 1 });
  }

  function reset() {
    patch({ draft: "", query: "", state: "", reference: 0 });
    searchField.current?.focus();
  }

  function reload() {
    heading.current?.focus();
    result.reload();
  }

  const bodyStatus = filtered.length
    ? range
    : t(rows.length ? "directory.noResults" : "directory.empty");
  return (
    <section aria-labelledby="directory-heading">
      <header className="page-head directory-header">
        <h1 id="directory-heading" ref={heading} tabIndex={-1}>{t(spec.labelKey)}</h1>
        {canCreate && <RouteLink className="btn btn-primary" href={directoryPath(resource, "create")} navigate={navigate}>
          {t(`directory.create.${resource}`)}
        </RouteLink>}
      </header>
      <div className="panel">
        <p className="visually-hidden" role="status" aria-atomic="true">
          {result.phase === "ready" ? bodyStatus : ""}
        </p>
        <div className="directory-filters">
          <form className="directory-search" onSubmit={(event) => {
            event.preventDefault();
            patch({ query: filter.draft.trim() });
          }}>
            <label htmlFor="directory-search">{t("directory.search")}</label>
            <div className="directory-search-row">
              <input ref={searchField} id="directory-search" type="search" value={filter.draft}
                placeholder={t("directory.searchHint")} onChange={(event) => setFilter({ ...filter, draft: event.target.value })} />
              <button type="submit" className="btn">{t("queue.find")}</button>
            </div>
          </form>
          {hasStatus && <label>{t("directory.field.enabled")}
            <select value={filter.state} onChange={(event) => patch({ state: event.target.value })}>
              <option value="">{t("directory.allStates")}</option>
              <option value="enabled">{t("directory.enabled")}</option>
              <option value="disabled">{t("directory.disabled")}</option>
            </select>
          </label>}
          {filterField && (refIds.length > 0 || filter.reference > 0) && (
            <label>{t(`directory.field.${filterField}`)}
              <select value={filter.reference || ""} onChange={(event) => patch({ reference: Number(event.target.value) })}>
                <option value="">{t("directory.allReferences")}</option>
                {[...new Set([...refIds, ...(filter.reference ? [filter.reference] : [])])].sort((a, b) => a - b).map((id) => (
                  <option value={id} key={id}>{valueText(filterField, { [filterField]: id }, catalog)}</option>
                ))}
              </select>
            </label>
          )}
          {(filter.query || filter.state || filter.reference > 0) && <button className="btn"
            type="button" onClick={reset}>{t("common.reset")}</button>}
        </div>
        {result.phase === "loading" && <StatePanel title={t("common.loading")} loading />}
        {result.phase === "error" && <DirectoryReadError error={result.error} retry={reload} />}
        {result.phase === "ready" && !filtered.length && <StatePanel title={bodyStatus}>
          {!rows.length && <button type="button" className="btn" onClick={reload}>{t("common.refresh")}</button>}
        </StatePanel>}
        {result.phase === "ready" && filtered.length > 0 && (
          <>
            <p className="directory-table-hint" id="directory-scroll-hint">{t("directory.tableScroll")}</p>
            <div className="table-wrap directory-table" role="region" tabIndex={0}
              aria-labelledby="directory-heading" aria-describedby="directory-scroll-hint">
              <table aria-labelledby="directory-heading">
                <thead>
                  <tr>
                    <th scope="col">{t("directory.column.number")}</th>
                    <th scope="col" aria-sort={filter.descending ? "descending" : "ascending"}>
                      <button type="button" className="sort-button" onClick={() => patch({ descending: !filter.descending })}>
                        {t(spec.idKey === "employee_id" ? "directory.column.person" : "directory.column.name")}
                        <span aria-hidden="true">{filter.descending ? "↓" : "↑"}</span>
                      </button>
                    </th>
                    {otherColumns.map((column) => <th scope="col" key={column}>{t(`directory.field.${column}`)}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {filtered.slice(start, end).map((row) => {
                    const id = row[spec.idKey];
                    const href = directoryPath(resource, "detail", id);
                    return (
                      <tr key={id}>
                        <td>{id}</td>
                        <td className="directory-row-title">
                          <RouteLink id={`directory-row-${id}`} href={href} onFollow={() => {
                            setReturnFocus({ resource, id, scroll: window.scrollY });
                            navigate(href);
                          }}>{directoryLabel(resource, row)}</RouteLink>
                        </td>
                        {otherColumns.map((column) => <td key={column}>{column === "permissions"
                          ? t("directory.permissionCount", { count: row.permissions.length })
                          : valueText(column, row, catalog)}</td>)}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <nav className="pagination" aria-label={t("directory.pagination")}>
              <button type="button" className="btn" aria-disabled={page <= 1}
                onClick={() => { if (page > 1) patch({ page: page - 1 }); }}>{t("queue.previous")}</button>
              <span>{range}</span>
              <button type="button" className="btn" aria-disabled={page >= totalPages}
                onClick={() => { if (page < totalPages) patch({ page: page + 1 }); }}>{t("queue.next")}</button>
            </nav>
          </>
        )}
      </div>
    </section>
  );
}

function ReferenceSelect({ field, attributes, value, onChange, result }) {
  const select = useRef(null);
  const resource = referenceResources[field.name];
  const available = result.phase === "ready" ? result.data.filter((row) => row.enabled) : noRows;
  const present = available.some((row) => row[field.name] === value);
  const locked = attributes.disabled || !available.length;
  const hint = result.phase === "loading" ? t("common.loading")
    : result.phase === "error" && result.error?.status !== 403 ? t("directory.referenceError")
    : result.phase === "error" || result.phase === "forbidden" ? t("directory.referenceUnavailable")
    : !available.length ? t("directory.referenceEmpty") : "";
  return (
    <>
      <select {...attributes} ref={select} value={value || ""} disabled={false} aria-disabled={locked}
        aria-describedby={[attributes["aria-describedby"], hint && `${attributes.id}-choices`].filter(Boolean).join(" ") || undefined}
        onPointerDown={(event) => { if (locked) event.preventDefault(); }}
        onKeyDown={(event) => { if (locked && !["Tab", "Escape"].includes(event.key)) event.preventDefault(); }}
        onChange={(event) => { if (!locked) onChange(Number(event.target.value)); }}>
        <option value="">{t(field.required ? "directory.pleaseChoose" : "directory.noSelection")}</option>
        {value > 0 && !present && <option value={value} disabled>
          {t("directory.unavailableChoice", { value: t("common.identifier", { id: value }) })}
        </option>}
        {available.map((row) => <option value={row[field.name]} key={row[field.name]}>
          {referenceLabel(row, resource, field.name)}
        </option>)}
      </select>
      {hint && <p className="directory-hint" id={`${attributes.id}-choices`}>{hint}</p>}
      {result.phase === "error" && result.error?.status !== 403 && <button className="btn directory-retry"
        type="button" onClick={() => {
          select.current?.focus();
          result.reload();
        }}>{t("common.retry")}</button>}
    </>
  );
}

function PermissionField({ id, choices, value, onChange, locked, error }) {
  const group = useRef(null);
  const issue = choices.phase === "loading" ? t("common.loading")
    : choices.phase === "error" ? t(choices.error?.status === 403 ? "directory.referenceUnavailable" : "directory.referenceError")
    : !choices.data?.length ? t("directory.referenceEmpty") : "";
  return (
    <fieldset className="directory-permissions directory-wide" disabled={locked} tabIndex={-1} ref={group}
      aria-describedby={[issue && `${id}-choices`, error && `${id}-error`].filter(Boolean).join(" ") || undefined}>
      <legend>{t("directory.field.permissions")}</legend>
      {choices.phase === "ready" && choices.data.map((permission) => (
        <label key={permission} className="directory-checkbox">
          <input type="checkbox" name="permissions" value={permission} checked={value.includes(permission)}
            aria-invalid={Boolean(error)} onChange={(event) => onChange(event.target.checked
              ? [...value, permission]
              : value.filter((item) => item !== permission))} />
          <span>{permission}</span>
        </label>
      ))}
      {issue && <p className="directory-hint" id={`${id}-choices`}>{issue}</p>}
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
      {choices.phase === "error" && choices.error?.status !== 403 && (
        <button type="button" className="btn directory-retry" onClick={() => {
          group.current?.focus();
          choices.reload();
        }}>{t("common.retry")}</button>
      )}
    </fieldset>
  );
}

function EditorField({ field, value, onChange, references, error, locked }) {
  const id = useId();
  const attributes = {
    id, name: field.name, required: field.required,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": error ? `${id}-error` : undefined,
  };
  if (field.type === "permissions") {
    return <PermissionField id={id} choices={references.permissions} value={value ?? noRows}
      onChange={onChange} locked={locked} error={error} />;
  }
  const isReference = Boolean(referenceResources[field.name]);
  const checkbox = field.type === "checkbox";
  return (
    <div className={field.type === "textarea" ? "directory-field directory-wide" : "directory-field"}>
      {checkbox ? (
        <label className="directory-checkbox">
          <input {...attributes} type="checkbox" checked={Boolean(value)} disabled={locked}
            onChange={(event) => onChange(event.target.checked)} />
          <span>{t(`directory.field.${field.name}`)}</span>
        </label>
      ) : (
        <>
          <label htmlFor={id}>{t(`directory.field.${field.name}`)}
            {field.required && <span className="directory-required" aria-hidden="true"> *</span>}
          </label>
          {isReference ? (
            <ReferenceSelect field={field} attributes={{ ...attributes, disabled: locked }} value={value}
              onChange={onChange} result={references[field.name]} />
          ) : field.type === "textarea" ? (
            <textarea {...attributes} rows={4} value={value ?? ""} readOnly={locked}
              onChange={(event) => onChange(event.target.value)} />
          ) : (
            <input {...attributes} type={field.type ?? "text"} value={value ?? ""} readOnly={locked}
              onChange={(event) => onChange(event.target.value)} />
          )}
        </>
      )}
      {error && <p id={`${id}-error`} className="field-error">{error}</p>}
    </div>
  );
}

const feedbackKeys = {
  rejected: "directory.writeRejected", unconfirmed: "directory.writeUnconfirmed",
  conflict: "directory.writeConflict", success: "directory.success",
};

function DirectoryEditor({
  route, api, permissions, navigate, record, onSave, mutating, writeFeedback, onCheckWrite,
  onClearConflict, onReplayCreate, savedDraft, onDraftChange,
}) {
  const { resource, id, mode } = route;
  const creating = mode === "create";
  const formMode = creating ? "create" : "update";
  const fields = DIRECTORIES[resource].fields[formMode];
  const canRead = canDirectory(resource, "read", permissions);
  const [values, setValues] = useState(() => savedDraft?.values ?? directoryFormValues(resource, formMode, record));
  const [baseline, setBaseline] = useState(savedDraft?.baseline ?? record);
  const [localFeedback, setLocalFeedback] = useState(null);
  const [issues, setIssues] = useState({});
  const [conflict, setConflict] = useState(null);
  const alive = useRef(true);
  const submitting = useRef(false);
  const conflictRead = useRef(null);
  const heading = useHeading();
  const formRef = useRef(null);
  const comparisonHeading = useRef(null);
  const isAllowed = (resourceKey, type) =>
    fields.some((field) => field.name === type) && canDirectory(resourceKey, "read", permissions);
  const clientAccess = isAllowed("clients", "client_id");
  const departmentAccess = isAllowed("departments", "department_id");
  const clients = useResource(api, "clients", clientAccess);
  const departments = useResource(api, "departments", departmentAccess);
  const loadPermissions = useCallback((signal) => fields.some((field) => field.type === "permissions")
    ? api.permissions(resource, { signal })
    : Promise.resolve(noRows), [api, fields, resource]);
  const availablePermissions = useRemoteData(resource, loadPermissions);
  const references = {
    client_id: clientAccess ? clients : { phase: "forbidden" },
    department_id: departmentAccess ? departments : { phase: "forbidden" },
    permissions: availablePermissions,
  };
  const feedback = localFeedback?.status === "success" ? localFeedback : writeFeedback ?? localFeedback;
  const blocked = feedback?.status === "unconfirmed" || feedback?.status === "conflict";
  const localErrors = Array.isArray(feedback?.fields)
    ? Object.fromEntries(feedback.fields.map((field) => [field, t("directory.validation")]))
    : feedback?.fields ?? {};
  const errors = Object.fromEntries(Object.entries({ ...localErrors, ...issues })
    .map(([name, problem]) => [name, renderMessage(problem)]));
  const title = t(creating ? `directory.create.${resource}` : "directory.editTitle");

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      conflictRead.current?.abort();
    };
  }, []);

  useLayoutEffect(() => {
    if (conflict?.phase === "ready" && document.activeElement === heading.current) comparisonHeading.current?.focus();
  }, [conflict, heading]);

  function focusError(map) {
    const first = fields.find((field) => map[field.name]);
    if (first) {
      const candidates = formRef.current?.querySelectorAll(`[name="${first.name}"]`);
      const control = [...(candidates ?? [])].find((node) => !node.disabled);
      (control ?? heading.current)?.focus();
    }
  }

  function validate() {
    const problems = {};
    for (const field of fields) {
      const name = field.name;
      const value = values[name];
      if (field.type === "permissions") {
        if (!Array.isArray(value) || !value.length) problems[name] = { key: "directory.requirePermission" };
      } else if (referenceResources[name]) {
        const choices = references[name];
        if ((field.required || value > 0)
          && (choices?.phase !== "ready" || !choices.data.some((row) => row[name] === value && row.enabled))) {
          problems[name] = { key: "directory.requireChoice" };
        }
      } else if (field.required && !String(value ?? "").trim()) {
        problems[name] = { key: "directory.required" };
      } else if (["name", "first_name", "last_name"].includes(name) && String(value ?? "").trim()) {
        const length = Array.from(value.trim()).length;
        if (length < 2 || length > 100) problems[name] = { key: "directory.nameLength" };
      }
    }
    return problems;
  }

  async function runSave(operation) {
    if (mutating || submitting.current) return;
    submitting.current = true;
    setLocalFeedback(null);
    try {
      const result = await operation();
      if (!alive.current || !result) return;
      setLocalFeedback(result);
      if (result.status === "success") {
        const savedId = result.record?.[DIRECTORIES[resource].idKey] ?? id;
        if (canRead && savedId) navigate(directoryPath(resource, "detail", savedId));
        else if (creating) {
          setValues(directoryFormValues(resource, "create"));
          setLocalFeedback({
            ...result, message: { key: savedId ? "directory.issuedId" : "directory.created", params: { id: savedId } },
          });
          heading.current?.focus();
        }
      } else if (result.fields) {
        focusError(Array.isArray(result.fields)
          ? Object.fromEntries(result.fields.map((name) => [name, true]))
          : result.fields);
      }
    } catch {
      if (alive.current) setLocalFeedback({ status: "unconfirmed" });
    } finally {
      submitting.current = false;
    }
  }

  function submit(event) {
    event.preventDefault();
    if (mutating || blocked || submitting.current) return;
    const problems = validate();
    setIssues(problems);
    if (Object.keys(problems).length) focusError(problems);
    else void runSave(() => onSave({ resource, id, mode, values, baseline }));
  }

  function updateDraft(next, base) {
    setValues(next);
    const starting = directoryFormValues(resource, formMode, base);
    const changed = Object.keys(next).some((name) => JSON.stringify(next[name]) !== JSON.stringify(starting[name]));
    onDraftChange?.(changed ? { values: next, baseline: base } : null);
  }

  async function loadConflict() {
    if (mutating || conflictRead.current || creating) return;
    const controller = new AbortController();
    conflictRead.current = controller;
    setConflict({ phase: "loading" });
    heading.current?.focus();
    try {
      const latest = await api.get(resource, id, { signal: controller.signal });
      if (!controller.signal.aborted) setConflict({ phase: "ready", latest });
    } catch (error) {
      if (!controller.signal.aborted) setConflict({ phase: "error", error });
    } finally {
      if (conflictRead.current === controller) conflictRead.current = null;
    }
  }

  const prior = conflict?.phase === "ready" ? directoryFormValues(resource, "update", baseline) : null;
  const latest = conflict?.phase === "ready" ? directoryFormValues(resource, "update", conflict.latest) : null;
  const differences = latest
    ? fields.filter(({ name }) => values[name] !== prior[name] && latest[name] !== prior[name] && latest[name] !== values[name])
    : noRows;

  function rebase() {
    if (!latest || mutating) return;
    updateDraft(Object.fromEntries(fields.map(({ name }) => [
      name, values[name] !== prior[name] ? values[name] : latest[name],
    ])), conflict.latest);
    setBaseline(conflict.latest);
    setConflict(null);
    setIssues({});
    setLocalFeedback({ status: "success", message: { key: "directory.rebased" } });
    onClearConflict?.();
    heading.current?.focus();
  }

  return (
    <section aria-labelledby="directory-edit-heading">
      {canRead && <BackLink resource={resource} navigate={navigate} mode={creating ? "list" : "detail"} id={id} />}
      <header className="page-head"><h1 ref={heading} id="directory-edit-heading" tabIndex={-1}>{title}</h1></header>
      <div className="panel detail-panel">
        {feedback && <div className="directory-feedback">
          <p role={feedback.status === "success" ? "status" : "alert"}>
            {renderMessage(feedback.message) || t(feedbackKeys[feedback.status] ?? "error.generic")}
          </p>
          {feedback.status === "unconfirmed" && canRead && onCheckWrite && <button className="btn directory-retry"
            type="button" aria-disabled={mutating}
            onClick={() => {
              if (mutating) return;
              heading.current?.focus();
              onCheckWrite();
            }}>{t("directory.checkWrite")}</button>}
          {feedback.status === "unconfirmed" && creating && onReplayCreate && <button className="btn directory-retry"
            type="button" aria-disabled={mutating}
            onClick={() => { void runSave(onReplayCreate); }}>{t("directory.repeatCreate")}</button>}
          {feedback.status === "conflict" && !creating && conflict?.phase !== "ready" && (
            <button className="btn directory-retry" type="button"
              aria-disabled={mutating || conflict?.phase === "loading"} onClick={loadConflict}>
              {t(conflict?.phase === "loading" ? "common.loading" : "directory.checkWrite")}
            </button>
          )}
          {feedback.status === "conflict" && conflict?.phase === "error" && (
            <p role="alert">{errorText(conflict.error)}</p>
          )}
          {feedback.status === "conflict" && latest && (
            <section className="directory-conflict">
              <h2 tabIndex={-1} ref={comparisonHeading}>{t("directory.compare")}</h2>
              {differences.length ? <ul>
                {differences.map(({ name }) => <li key={name}>
                  <strong>{t(`directory.field.${name}`)}</strong>
                  <dl>
                    <div><dt>{t("directory.currentValue")}</dt><dd>{valueText(name, latest)}</dd></div>
                    <div><dt>{t("directory.draftValue")}</dt><dd>{valueText(name, values)}</dd></div>
                  </dl>
                </li>)}
              </ul> : <p>{t("directory.latestLoaded")}</p>}
              <button className="btn" type="button" aria-disabled={mutating}
                onClick={rebase}>{t("directory.rebase")}</button>
            </section>
          )}
        </div>}
        <form ref={formRef} className="directory-form" aria-labelledby="directory-edit-heading"
          onSubmit={submit} noValidate aria-busy={mutating}>
          <p className="visually-hidden" aria-live="assertive" aria-atomic="true">
            {Object.values(errors).some(Boolean) ? t("directory.validation") : ""}
          </p>
          <div className="directory-form-grid">
            {fields.map((field) => <EditorField key={field.name} field={field} value={values[field.name]}
              onChange={(value) => {
                updateDraft({ ...values, [field.name]: value }, baseline);
                setIssues((previous) => ({ ...previous, [field.name]: "" }));
              }}
              references={references} error={errors[field.name]} locked={mutating || blocked} />)}
          </div>
          <button type="submit" className="btn btn-primary directory-save" aria-disabled={mutating || blocked}>
            {t(mutating ? "directory.saving" : creating ? "directory.submitCreate" : "directory.submitEdit")}
          </button>
        </form>
      </div>
    </section>
  );
}

function DirectoryDetail({ resource, id, record, reload, navigate, permissions, renderActions, readOnlyEdit }) {
  const heading = useHeading();
  const fields = aboutFields[resource].filter((field) => Object.hasOwn(record, field));
  return (
    <article>
      <BackLink resource={resource} navigate={navigate} />
      <header className="page-head directory-header">
        <h1 ref={heading} tabIndex={-1}>{directoryLabel(resource, record)}</h1>
        {canDirectory(resource, "update", permissions) && (
          <RouteLink href={directoryPath(resource, "edit", id)} className="btn" navigate={navigate}>
            {t("directory.edit")}
          </RouteLink>
        )}
      </header>
      {readOnlyEdit && <p className="directory-feedback" role="status">{t("directory.noWrite")}</p>}
      <section className="panel detail-panel directory-details" aria-labelledby="directory-about">
        <h2 id="directory-about">{t("directory.recordDetails")}</h2>
        <dl className="metadata">
          {fields.map((field) => {
            const reference = referenceResources[field];
            const value = record[field];
            const canOpen = reference && value > 0 && canDirectory(reference, "read", permissions);
            return (
              <div key={field}>
                <dt>{t(`directory.field.${field}`)}</dt>
                <dd>{canOpen
                  ? <RouteLink href={directoryPath(reference, "detail", value)} navigate={navigate}>
                      {t("common.identifier", { id: value })}
                    </RouteLink>
                  : valueText(field, record)}</dd>
              </div>
            );
          })}
        </dl>
      </section>
      {renderActions?.({ resource, id, record, reload, permissions })}
    </article>
  );
}

function DirectoryRecord(props) {
  const { api, route, navigate, writeFeedback, onCheckWrite, mutating } = props;
  const { resource, id, mode } = route;
  const load = useCallback((signal) => api.get(resource, id, { signal }), [api, resource, id]);
  const result = useRemoteData(id, load);
  const back = <BackLink resource={resource} navigate={navigate} />;
  if (result.phase === "loading") return <>{back}<StatePanel title={t("common.loading")} loading /></>;
  if (result.phase === "error") return <DirectoryReadError error={result.error} retry={result.reload} page
    back={<>
      {back}
      {result.error?.status === 404 && writeFeedback?.status === "unconfirmed" && onCheckWrite && (
        <button className="btn" type="button" aria-disabled={mutating}
          onClick={() => { if (!mutating) onCheckWrite(); }}>{t("directory.checkWrite")}</button>
      )}
    </>} />;
  return mode === "edit"
    ? <DirectoryEditor {...props} record={result.data} />
    : <DirectoryDetail {...props} resource={resource} id={id} record={result.data} reload={result.reload} />;
}

export default function DirectoryPage(props) {
  const { route, permissions, navigate } = props;
  const { resource, id, mode } = route;
  const [filters, setFilters] = useState({});
  const [returnFocus, setReturnFocus] = useState(null);
  const read = canDirectory(resource, "read", permissions);
  const create = canDirectory(resource, "create", permissions);
  const update = canDirectory(resource, "update", permissions);
  if (mode === "create" && create) return <DirectoryEditor {...props} key={`${resource}:create`} />;
  if (mode === "edit" && read && !update) {
    return <DirectoryRecord {...props} route={{ ...route, mode: "detail" }} readOnlyEdit
      key={`${resource}:readonly:${id}`} />;
  }
  if (!read || mode === "create") {
    return (
      <StatePanel title={t("error.forbidden")} error page
        description={t(mode === "create" || mode === "edit" ? "directory.noWrite" : "directory.noRead")}>
        {read && <BackLink resource={resource} navigate={navigate} />}
        {!read && create && mode !== "create" && (
          <RouteLink href={directoryPath(resource, "create")} navigate={navigate}>{t(`directory.create.${resource}`)}</RouteLink>
        )}
      </StatePanel>
    );
  }
  if (mode !== "list") return <DirectoryRecord {...props} key={`${resource}:${mode}:${id}`} />;
  return (
    <DirectoryList {...props} key={resource} resource={resource}
      filter={filters[resource] ?? defaultFilter}
      setFilter={(filter) => setFilters((current) => ({ ...current, [resource]: filter }))}
      returnFocus={returnFocus} setReturnFocus={setReturnFocus} />
  );
}
