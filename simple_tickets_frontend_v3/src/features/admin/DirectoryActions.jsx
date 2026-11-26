import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { ConfirmationDialog } from "../../app/layout.jsx";
import { directoryPath } from "../../app/routes.js";
import { useRemoteData } from "../../app/useRemoteData.js";
import { t } from "../../shared/i18n/messages.js";
import { canDirectory, canDirectoryAction, directoryLabel } from "./directoryModel.js";

function CommandPanel({ action, label, busy, canSubmit = true, onSubmit, onCancel, children }) {
  const id = useId();
  const heading = useRef(null);
  useEffect(() => { heading.current?.focus(); }, [action]);
  return (
    <form className="directory-command" aria-labelledby={id} aria-busy={busy} onSubmit={onSubmit}>
      <h3 id={id} ref={heading} tabIndex={-1}>{label}</h3>
      {children}
      <div className="directory-action-row">
        <button type="submit" className="btn btn-primary" disabled={busy || !canSubmit}>{t("directory.actionConfirm")}</button>
        <button type="button" className="btn" disabled={busy} onClick={onCancel}>{t("directory.actionBack")}</button>
      </div>
    </form>
  );
}

function CatalogState({ result, empty }) {
  if (result.phase === "loading") return <p role="status">{t("common.loading")}</p>;
  if (result.phase === "error") return <div role="alert">
    <p>{t("directory.actionCatalogError")}</p>
    <button type="button" className="btn" onClick={result.reload}>{t("common.retry")}</button>
  </div>;
  return empty ? <p role="status">{t("directory.actionCatalogEmpty")}</p> : null;
}

function RoleChoices({ api, resource, record, action, busy, onSubmit, onCancel }) {
  const group = resource === "admins" ? "adminRoles" : "userRoles";
  const load = useCallback((signal) => api.list(group, { signal }), [api, group]);
  const result = useRemoteData(group, load);
  const removing = action === "revokeRoles";
  const available = (result.data ?? []).filter((row) => record.roles.includes(row.role_id) === removing);
  const [selected, setSelected] = useState([]);
  const eligible = selected.filter((id) => available.some((role) => role.role_id === id));

  function submit(event) {
    event.preventDefault();
    if (eligible.length) onSubmit({ roles: eligible });
  }

  return <CommandPanel action={action} label={t(`directory.action.${action}`)}
    busy={busy} canSubmit={eligible.length > 0} onSubmit={submit} onCancel={onCancel}>
    <CatalogState result={result} empty={!available.length} />
    {available.length > 0 && <fieldset className="directory-command-options" disabled={busy}>
      <legend>{t("directory.rolesSelection")}</legend>
      {available.map((role) => <label key={role.role_id}>
        <input type="checkbox" checked={eligible.includes(role.role_id)}
          onChange={(event) => setSelected(event.target.checked
            ? [...selected, role.role_id] : selected.filter((id) => id !== role.role_id))} />
        {directoryLabel(group, role)} <span className="muted">{t("common.identifier", { id: role.role_id })}</span>
      </label>)}
    </fieldset>}
  </CommandPanel>;
}

function DepartmentChoice({ api, busy, record, onSubmit, onCancel }) {
  const load = useCallback((signal) => api.list("departments", { signal }), [api]);
  const result = useRemoteData("departments", load);
  const available = (result.data ?? []).filter((row) => row.enabled && row.department_id !== record.department_id);
  const [selected, setSelected] = useState("");

  function submit(event) {
    event.preventDefault();
    const department_id = Number(selected);
    if (available.some((row) => row.department_id === department_id)) onSubmit({ department_id });
  }

  return <CommandPanel action="changeDepartment" label={t("directory.action.changeDepartment")}
    busy={busy} canSubmit={available.some((row) => String(row.department_id) === selected)} onSubmit={submit} onCancel={onCancel}>
    <CatalogState result={result} empty={!available.length} />
    {available.length > 0 && <label className="directory-command-field">
      {t("directory.departmentChoice")}
      <select required value={selected} disabled={busy} onChange={(event) => setSelected(event.target.value)}>
        <option value="">{t("directory.chooseDepartment")}</option>
        {available.map((row) => <option key={row.department_id} value={row.department_id}>{row.name}</option>)}
      </select>
    </label>}
  </CommandPanel>;
}

function Credentials({ action, busy, self, onSubmit, onCancel }) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [enabled, setEnabled] = useState(true);
  const id = useId();
  const attaching = action === "attachAccount";

  function submit(event) {
    event.preventDefault();
    if (!password || (attaching && login.trim().length < 2)) return;
    const data = attaching ? { login: login.trim(), password, enable_account: enabled } : { password };
    setPassword("");
    onSubmit(data);
  }

  return <CommandPanel action={action} label={t(`directory.action.${action}`)} busy={busy} onSubmit={submit} onCancel={onCancel}>
    {attaching && <label className="directory-command-field">
      {t("directory.accountLogin")}
      <input name="login" autoComplete="off" required minLength={2} maxLength={100} readOnly={busy}
        value={login} onChange={(event) => setLogin(event.target.value)} />
    </label>}
    <label className="directory-command-field">
      {t("directory.accountPassword")}
      <input name="password" type="password" autoComplete="new-password" required minLength={8} maxLength={128}
        aria-describedby={id} readOnly={busy} value={password} onChange={(event) => setPassword(event.target.value)} />
    </label>
    <p id={id} className="muted">{t("directory.accountPasswordHint")}</p>
    {self && !attaching && <p>{t("directory.accountOwnPassword")}</p>}
    {attaching && <label className="directory-command-check">
      <input type="checkbox" checked={enabled} disabled={busy} onChange={(event) => setEnabled(event.target.checked)} />
      {t("directory.accountStartEnabled")}
    </label>}
  </CommandPanel>;
}

export default function DirectoryActions({ api, mutations, resource, id, record, reload, permissions, actorId, navigate }) {
  const [action, setAction] = useState(null);
  const active = useRef(false);
  useLayoutEffect(() => {
    active.current = true;
    return () => { active.current = false; };
  }, []);
  const { busy, feedback, passwordPending } = mutations.state(resource, id);
  const blocked = busy || feedback?.status === "unconfirmed";
  const allowed = (value) => canDirectoryAction(resource, value, permissions);
  const self = resource === "admins" && id === actorId;
  const employee = resource === "admins" || resource === "users";
  const attached = Boolean(record.login);
  const controls = [];
  const lifecycle = record.enabled ? "disable" : "enable";
  if (typeof record.enabled === "boolean" && allowed(lifecycle) && !(self && lifecycle === "disable")) controls.push(lifecycle);
  if (employee) {
    if (!attached && record.enabled && allowed("attachAccount")) controls.push("attachAccount");
    if (attached) {
      if (record.enabled && !record.enabled_login && allowed("enableAccount")) controls.push("enableAccount");
      if (!self && record.enabled_login && allowed("disableAccount")) controls.push("disableAccount");
      if (allowed("changePassword")) controls.push("changePassword");
      if (!self && allowed("detachAccount")) controls.push("detachAccount");
    }
    if (record.enabled && allowed("grantRoles")) controls.push("grantRoles");
    if (record.roles.length && allowed("revokeRoles")) controls.push("revokeRoles");
  }
  if (resource === "admins") {
    if (allowed("changeDepartment") && canDirectory("departments", "read", permissions)) controls.push("changeDepartment");
    if (record.department_id && allowed("removeDepartment")) controls.push("removeDepartment");
  }
  if (canDirectory(resource, "remove", permissions) && !record.is_system_role) controls.push("remove");

  function settle(result) {
    if (!active.current || !result) return;
    if (result.removed) navigate(directoryPath(resource), { replace: true });
    else if (result.record || result.status === "conflict") reload();
    if (result.status !== "rejected" || !["grantRoles", "revokeRoles", "changeDepartment", "attachAccount", "changePassword"].includes(action)) {
      setAction(null);
    }
  }

  async function send(data) {
    if (blocked || !controls.includes(action)) return;
    const transaction = { resource, id, record };
    const result = action === "remove" ? await mutations.remove(transaction)
      : await mutations.command({ ...transaction, action, data });
    settle(result);
  }

  function close() {
    setAction(null);
  }

  if (!controls.length && !feedback) return null;
  const current = controls.includes(action) ? action : null;
  const title = current && t(`directory.action.${current}`);
  return <section className="panel directory-actions-panel" aria-label={t("directory.actionsTitle")}>
    <h2>{t("directory.actionsTitle")}</h2>
    {feedback && <div className="directory-action-feedback">
      <p role={["success", "notice"].includes(feedback.status) ? "status" : "alert"}>{feedback.message}</p>
      {passwordPending && <button type="button" className="btn" disabled={busy}
        onClick={() => mutations.stopPasswordCheck(resource, id)}>{t("directory.passwordStopCheck")}</button>}
      {!passwordPending && feedback.status === "unconfirmed" && <button type="button" className="btn" disabled={busy}
        onClick={async () => settle(await mutations.check(resource, id))}>{t("directory.actionCheck")}</button>}
    </div>}
    <div className="directory-action-row">
      {controls.map((value) => <button key={value} type="button" className="btn" disabled={blocked}
        onClick={() => setAction(value)}>{t(`directory.action.${value}`)}</button>)}
    </div>
    {current === "grantRoles" || current === "revokeRoles"
      ? <RoleChoices key={current} api={api} resource={resource} record={record} action={current}
        busy={blocked} onSubmit={send} onCancel={close} />
      : current === "changeDepartment"
        ? <DepartmentChoice api={api} record={record} busy={blocked} onSubmit={send} onCancel={close} />
        : current === "attachAccount" || current === "changePassword"
          ? <Credentials key={current} action={current} busy={blocked} self={self} onSubmit={send} onCancel={close} />
          : current && <ConfirmationDialog title={title}
            description={t(current === "remove" && self ? "directory.action.removeSelf.help" : `directory.action.${current}.help`,
              { name: directoryLabel(resource, record), id })}
            confirmLabel={t(current === "remove" ? "directory.actionConfirmDelete" : "directory.actionConfirm")}
            busy={busy} onConfirm={() => send()} onCancel={close} />}
  </section>;
}
