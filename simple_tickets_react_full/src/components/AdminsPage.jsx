import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { can } from "../permissions.js";
import DataTable from "./DataTable.jsx";
import Modal from "./Modal.jsx";
import RolePicker from "./RolePicker.jsx";

const EMPTY = {
  employee_id: 0,
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  job_title: "",
  login: "",
  enabled_login: false,
  enabled: true,
  roles: [],
  department_id: 0,
};

export default function AdminsPage({ permissions, showToast }) {
  const [rows, setRows] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [roles, setRoles] = useState([]);
  const [departmentsLoaded, setDepartmentsLoaded] = useState(false);
  const [rolesLoaded, setRolesLoaded] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [password, setPassword] = useState("");

  const mayView = can.adminsView(permissions);
  const mayOperate = can.adminsOperate(permissions);
  const mayChangeRoles = can.rolesAssign(permissions) || can.rolesRevoke(permissions);

  async function load() {
    if (!mayView) return;
    try {
      const payload = await api.getAdmins();
      setRows(Array.isArray(payload) ? payload : []);
    } catch (error) {
      showToast(error.message, "error");
      return;
    }

    if (mayOperate) {
      try {
        const payload = await api.getDepartments();
        setDepartments(Array.isArray(payload) ? payload : []);
        setDepartmentsLoaded(true);
      } catch {
        setDepartments([]);
        setDepartmentsLoaded(false);
      }
      try {
        const payload = await api.getAdminRoles();
        setRoles(Array.isArray(payload) ? payload : []);
        setRolesLoaded(true);
      } catch {
        setRoles([]);
        setRolesLoaded(false);
      }
    } else {
      setDepartments([]);
      setRoles([]);
      setDepartmentsLoaded(false);
      setRolesLoaded(false);
    }
  }

  useEffect(() => {
    load();
  }, [mayView, permissions.join("|")]);

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
    try {
      if (!form.employee_id) {
        await api.createAdmin({
          first_name: form.first_name,
          last_name: form.last_name,
          email: form.email,
          phone: form.phone,
          job_title: form.job_title,
          login: form.login,
          password,
          enable_account: Boolean(form.login),
          department_id: Number(form.department_id) || 0,
          roles: mayChangeRoles ? form.roles || [] : [],
        });
      } else {
        // Department is deliberately NOT sent here: it has a dedicated endpoint.
        await api.updateAdmin(form.employee_id, {
          first_name: form.first_name,
          last_name: form.last_name,
          email: form.email,
          phone: form.phone,
          job_title: form.job_title,
        });

        if (mayChangeRoles && rolesLoaded) {
          const before = new Set(editing?.roles || []);
          const after = new Set(form.roles || []);
          const grant = [...after].filter((id) => !before.has(id));
          const revoke = [...before].filter((id) => !after.has(id));
          if (grant.length) await api.grantAdminRoles(form.employee_id, grant);
          if (revoke.length) await api.revokeAdminRoles(form.employee_id, revoke);
        }

        const oldDepartment = Number(editing?.department_id) || 0;
        const newDepartment = Number(form.department_id) || 0;
        if (newDepartment !== oldDepartment) {
          if (newDepartment) await api.changeAdminDepartment(form.employee_id, newDepartment);
          else await api.removeAdminDepartment(form.employee_id);
        }
      }

      showToast("Admin сохранён", "success");
      setEditing(null);
      setForm(EMPTY);
      await load();
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function toggle() {
    try {
      await (form.enabled ? api.disableAdmin(form.employee_id) : api.enableAdmin(form.employee_id));
      setEditing(null);
      await load();
      showToast("Состояние изменено", "success");
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function remove() {
    if (!confirm("Удалить Admin?")) return;
    try {
      await api.deleteAdmin(form.employee_id);
      setEditing(null);
      await load();
      showToast("Admin удалён", "success");
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function attach() {
    try {
      await api.attachAdminAccount(form.employee_id, { login: form.login, password, enable_account: true });
      setPassword("");
      await load();
      showToast("Аккаунт подключён", "success");
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function detach() {
    try {
      await api.detachAdminAccount(form.employee_id);
      await load();
      showToast("Аккаунт отключён", "success");
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function changePassword() {
    try {
      await api.changeAdminPassword(form.employee_id, password);
      setPassword("");
      showToast("Пароль изменён", "success");
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  if (!mayView) return <div className="empty-permission">Нет права просмотра Admin.</div>;

  return (
    <div>
      <div className="view-header">
        <div><h1>Admin</h1><p>Сотрудники поддержки, аккаунты, отделы и роли.</p></div>
        <div className="view-actions"><button className="btn" onClick={load}>Обновить</button>{mayOperate && <button className="btn btn-primary" onClick={() => open()}>Создать Admin</button>}</div>
      </div>
      <DataTable storageKey="admins.all" title="Admin" rows={rows} columns={columns} getRowId={(row) => row.employee_id} onRowClick={open} />

      {form && (editing || form !== EMPTY) && (
        <Modal title={form.employee_id ? `Admin #${form.employee_id}` : "Новый Admin"} onClose={() => { setEditing(null); setForm(EMPTY); }}>
          <div className="form-grid">
            <label><span>Имя</span><input disabled={!mayOperate} value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></label>
            <label><span>Фамилия</span><input disabled={!mayOperate} value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></label>
            <label><span>Email</span><input disabled={!mayOperate} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
            <label><span>Телефон</span><input disabled={!mayOperate} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
            <label><span>Должность</span><input disabled={!mayOperate} value={form.job_title || ""} onChange={(e) => setForm({ ...form, job_title: e.target.value })} /></label>
            <label>
              <span>Отдел</span>
              {departmentsLoaded ? (
                <select disabled={!mayOperate} value={form.department_id || 0} onChange={(e) => setForm({ ...form, department_id: Number(e.target.value) })}>
                  <option value="0">Без отдела</option>
                  {departments.map((department) => <option key={department.department_id} value={department.department_id}>{department.name}{department.enabled ? "" : " (off)"}</option>)}
                </select>
              ) : (
                <input type="number" min="0" disabled={!mayOperate} value={form.department_id || ""} onChange={(e) => setForm({ ...form, department_id: Number(e.target.value) || 0 })} placeholder="Department ID" />
              )}
            </label>
            <label><span>Логин</span><input disabled={!mayOperate} value={form.login || ""} onChange={(e) => setForm({ ...form, login: e.target.value })} /></label>
            <label><span>Пароль</span><input type="password" disabled={!mayOperate} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
            {rolesLoaded && mayChangeRoles && (
              <div className="wide-field"><span className="field-caption">Admin roles</span><RolePicker roles={roles} selected={form.roles} disabled={!mayOperate} onChange={(value) => setForm({ ...form, roles: value })} /></div>
            )}
            {!rolesLoaded && form.employee_id > 0 && Boolean(form.roles?.length) && (
              <div className="wide-field"><span className="field-caption">Role IDs</span><div className="permission-chips">{form.roles.map((id) => <span key={id} className="badge badge-info">#{id}</span>)}</div></div>
            )}
          </div>
          {mayOperate && (
            <div className="card-actions">
              <button className="btn btn-primary" disabled={!form.first_name} onClick={save}>Сохранить</button>
              {form.employee_id > 0 && (
                <>
                  <button className="btn" onClick={toggle}>{form.enabled ? "Отключить" : "Включить"}</button>
                  <button className="btn" disabled={!form.login || !password} onClick={attach}>Attach account</button>
                  <button className="btn" disabled={!form.login} onClick={detach}>Detach</button>
                  <button className="btn" disabled={!password} onClick={changePassword}>Сменить пароль</button>
                  <button className="btn btn-danger" onClick={remove}>Удалить</button>
                </>
              )}
            </div>
          )}
        </Modal>
      )}
    </div>
  );
}
