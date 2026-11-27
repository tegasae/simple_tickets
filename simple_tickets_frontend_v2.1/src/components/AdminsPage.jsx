import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { can } from "../permissions.js";
import { useReferenceData } from "../referenceData.jsx";
import DataTable from "./DataTable.jsx";
import Modal from "./Modal.jsx";
import RolePicker from "./RolePicker.jsx";

const EMPTY = {
  employee_id: 0, first_name: "", last_name: "", email: "", phone: "", job_title: "",
  login: "", enabled_login: false, enabled: true, roles: [], department_id: 0,
};

export default function AdminsPage({ permissions, showToast }) {
  const refs = useReferenceData();
  const { admins: rows, departments } = refs;
  const [roles, setRoles] = useState([]);
  const [rolesLoaded, setRolesLoaded] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const mayView = can.adminsView(permissions);
  const mayOperate = can.adminsOperate(permissions);
  const mayChangeRoles = can.assignAdminRoles(permissions);

  async function load(force = false) {
    if (!mayView) return;
    const jobs = [refs.ensureAdmins(force)];
    if (mayOperate) jobs.push(refs.ensureDepartments(force));
    try { await Promise.all(jobs); }
    catch (error) { showToast(error.message, "error"); }

    if (mayOperate) {
      try {
        const payload = await api.getAdminRoles();
        setRoles(Array.isArray(payload) ? payload : []);
        setRolesLoaded(true);
      } catch {
        setRoles([]);
        setRolesLoaded(false);
      }
    }
  }

  useEffect(() => { load(false); }, [mayView, permissions.join("|")]);

  const departmentMap = useMemo(
    () => Object.fromEntries(departments.map((department) => [department.department_id, department.name])),
    [departments],
  );

  const columns = [
    { key: "employee_id", label: "ID", className: "num" },
    { key: "first_name", label: "Имя" },
    { key: "last_name", label: "Фамилия" },
    { key: "job_title", label: "Должность" },
    { key: "department_id", label: "Отдел", getValue: (row) => row.department_id ? departmentMap[row.department_id] || `#${row.department_id}` : "—" },
    { key: "email", label: "Email" },
    { key: "login", label: "Логин" },
    { key: "enabled", label: "Активен", render: (row) => <span className={row.enabled ? "badge badge-ok" : "badge badge-muted"}>{row.enabled ? "Да" : "Нет"}</span> },
  ];

  function open(row = null) {
    setEditing(row);
    setForm(row ? { ...row, roles: [...(row.roles || [])] } : { ...EMPTY, roles: [] });
    setPassword("");
  }

  async function save() {
    setBusy(true);
    try {
      let saved;
      if (!form.employee_id) {
        saved = await api.createAdmin({
          first_name: form.first_name, last_name: form.last_name, email: form.email, phone: form.phone,
          job_title: form.job_title, login: form.login, password, enable_account: Boolean(form.login),
          department_id: Number(form.department_id) || 0, roles: mayChangeRoles ? form.roles || [] : [],
        });
      } else {
        saved = await api.updateAdmin(form.employee_id, {
          first_name: form.first_name, last_name: form.last_name, email: form.email, phone: form.phone,
          job_title: form.job_title, department_id: Number(form.department_id) || 0,
        });
        if (mayChangeRoles && rolesLoaded) {
          const before = new Set(editing?.roles || []);
          const after = new Set(form.roles || []);
          const grant = [...after].filter((id) => !before.has(id));
          const revoke = [...before].filter((id) => !after.has(id));
          if (grant.length) saved = await api.grantAdminRoles(form.employee_id, grant);
          if (revoke.length) saved = await api.revokeAdminRoles(form.employee_id, revoke);
        }
      }
      if (saved) refs.upsertAdmin(saved);
      showToast("Сотрудник сохранён", "success");
      setEditing(null); setForm(EMPTY); setPassword("");
    } catch (error) { showToast(error.message, "error"); }
    finally { setBusy(false); }
  }

  async function toggle() {
    try {
      const saved = await (form.enabled ? api.disableAdmin(form.employee_id) : api.enableAdmin(form.employee_id));
      if (saved) refs.upsertAdmin(saved);
      setEditing(null); setForm(EMPTY);
      showToast("Состояние изменено", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  async function remove() {
    if (!confirm("Удалить сотрудника?")) return;
    try {
      await api.deleteAdmin(form.employee_id);
      refs.removeAdmin(form.employee_id);
      setEditing(null); setForm(EMPTY);
      showToast("Сотрудник удалён", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  async function attach() {
    try {
      const saved = await api.attachAdminAccount(form.employee_id, { login: form.login, password, enable_account: true });
      if (saved) refs.upsertAdmin(saved);
      setPassword("");
      if (saved) setForm({ ...saved, roles: [...(saved.roles || [])] });
      showToast("Аккаунт подключён", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  async function detach() {
    try {
      const saved = await api.detachAdminAccount(form.employee_id);
      if (saved) refs.upsertAdmin(saved);
      if (saved) setForm({ ...saved, roles: [...(saved.roles || [])] });
      showToast("Аккаунт отключён", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  async function changePassword() {
    try {
      const saved = await api.changeAdminPassword(form.employee_id, password);
      if (saved) refs.upsertAdmin(saved);
      setPassword("");
      showToast("Пароль изменён", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  if (!mayView) return <div className="empty-permission">Нет права просмотра сотрудников.</div>;

  return <div>
    <div className="view-header">
      <div><h1>Сотрудники</h1><p>Сотрудники поддержки, аккаунты, отделы и роли.</p></div>
      <div className="view-actions"><button className="btn" onClick={() => load(true)}>Обновить</button>{mayOperate && <button className="btn btn-primary" onClick={() => open()}>Создать сотрудника</button>}</div>
    </div>
    <DataTable storageKey="admins.all" title="Сотрудники" rows={rows} columns={columns} getRowId={(row) => row.employee_id} onRowClick={open} />

    {form && (editing || form !== EMPTY) && <Modal title={form.employee_id ? `Сотрудник #${form.employee_id}` : "Новый сотрудник"} onClose={() => { setEditing(null); setForm(EMPTY); }}>
      <div className="form-grid">
        <label><span>Имя</span><input disabled={!mayOperate} value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></label>
        <label><span>Фамилия</span><input disabled={!mayOperate} value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></label>
        <label><span>Email</span><input disabled={!mayOperate} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
        <label><span>Телефон</span><input disabled={!mayOperate} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
        <label><span>Должность</span><input disabled={!mayOperate} value={form.job_title || ""} onChange={(e) => setForm({ ...form, job_title: e.target.value })} /></label>
        <label><span>Отдел</span><select disabled={!mayOperate} value={form.department_id || 0} onChange={(e) => setForm({ ...form, department_id: Number(e.target.value) })}><option value="0">Без отдела</option>{departments.map((department) => <option key={department.department_id} value={department.department_id}>{department.name}{department.enabled ? "" : " (отключён)"}</option>)}</select></label>
        <label><span>Логин</span><input disabled={!mayOperate} value={form.login || ""} onChange={(e) => setForm({ ...form, login: e.target.value })} /></label>
        <label><span>Пароль</span><input type="password" disabled={!mayOperate} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {rolesLoaded && mayChangeRoles && <div className="wide-field"><span className="field-caption">Роли сотрудника</span><RolePicker roles={roles} selected={form.roles} disabled={!mayOperate} onChange={(value) => setForm({ ...form, roles: value })} /></div>}
        {!rolesLoaded && form.employee_id > 0 && Boolean(form.roles?.length) && <div className="wide-field"><span className="field-caption">ID ролей</span><div className="permission-chips">{form.roles.map((id) => <span key={id} className="badge badge-info">#{id}</span>)}</div></div>}
      </div>
      {mayOperate && <div className="card-actions">
        <button className="btn btn-primary" disabled={busy || !form.first_name} onClick={save}>{busy ? "Сохранение..." : "Сохранить"}</button>
        {form.employee_id > 0 && <>
          <button className="btn" onClick={toggle}>{form.enabled ? "Отключить" : "Включить"}</button>
          <button className="btn" disabled={!form.login || !password} onClick={attach}>Подключить аккаунт</button>
          <button className="btn" disabled={!form.login} onClick={detach}>Отключить аккаунт</button>
          <button className="btn" disabled={!password} onClick={changePassword}>Сменить пароль</button>
          <button className="btn btn-danger" onClick={remove}>Удалить</button>
        </>}
      </div>}
    </Modal>}
  </div>;
}
