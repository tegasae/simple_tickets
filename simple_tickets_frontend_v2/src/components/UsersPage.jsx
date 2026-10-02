import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { can } from "../permissions.js";
import { useReferenceData } from "../referenceData.jsx";
import DataTable from "./DataTable.jsx";
import Modal from "./Modal.jsx";
import RolePicker from "./RolePicker.jsx";

const EMPTY = {
  employee_id: 0,
  client_id: 0,
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  login: "",
  enabled_login: false,
  enabled: true,
  roles: [],
};

export default function UsersPage({ permissions, showToast, onNavigate, pageContext }) {
  const refs = useReferenceData();
  const { users: rows, clients } = refs;
  const [roles, setRoles] = useState([]);
  const [rolesLoaded, setRolesLoaded] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [clientFilter, setClientFilter] = useState(Number(pageContext?.clientId || 0));

  const mayView = can.usersView(permissions);
  const mayOperate = can.usersOperate(permissions);
  const mayReadClients = can.clientsView(permissions);
  const mayReadRoleCatalog = can.adminsOperate(permissions);
  const mayChangeRoles = can.assignUserRoles(permissions);

  async function load(force = false) {
    if (!mayView) return;
    try {
      await refs.ensureAllUsers(force);
    } catch (error) {
      showToast(error.message, "error");
      return;
    }

    if (mayReadClients) {
      try { await refs.ensureClients(force); }
      catch { /* IDs remain usable when client catalog is unavailable. */ }
    }

    if (mayReadRoleCatalog) {
      try {
        const payload = await api.getUserRoles();
        setRoles(Array.isArray(payload) ? payload : []);
        setRolesLoaded(true);
      } catch {
        setRoles([]);
        setRolesLoaded(false);
      }
    }
  }

  useEffect(() => { load(false); }, [mayView, permissions.join("|")]);

  useEffect(() => { setClientFilter(Number(pageContext?.clientId || 0)); }, [pageContext]);

  useEffect(() => {
    const userId = Number(pageContext?.openUserId || 0);
    if (!userId || !mayView) return;
    refs.ensureUser(userId).then((row) => open(row)).catch((error) => showToast(error.message, "error"));
  }, [pageContext?.openUserId, mayView]);

  const clientMap = useMemo(() => Object.fromEntries(clients.map((x) => [x.client_id, x.name])), [clients]);

  const columns = [
    { key: "employee_id", label: "ID", className: "num" },
    { key: "client_id", label: "Клиент", getValue: (row) => clientMap[row.client_id] || `#${row.client_id}` },
    { key: "first_name", label: "Имя" },
    { key: "last_name", label: "Фамилия" },
    { key: "email", label: "Email" },
    { key: "phone", label: "Телефон" },
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
        saved = await api.createUser({
          client_id: Number(form.client_id), first_name: form.first_name, last_name: form.last_name,
          email: form.email, phone: form.phone, login: form.login, password,
          enable: true, enable_account: Boolean(form.login), roles: mayChangeRoles ? form.roles || [] : [],
        });
      } else {
        saved = await api.updateUser(form.employee_id, {
          first_name: form.first_name, last_name: form.last_name, email: form.email, phone: form.phone,
        });
        if (mayChangeRoles && rolesLoaded) {
          const before = new Set(editing?.roles || []);
          const after = new Set(form.roles || []);
          const grant = [...after].filter((x) => !before.has(x));
          const revoke = [...before].filter((x) => !after.has(x));
          if (grant.length) saved = await api.grantUserRoles(form.employee_id, grant);
          if (revoke.length) saved = await api.revokeUserRoles(form.employee_id, revoke);
        }
      }
      if (saved) refs.upsertUser(saved);
      showToast("Пользователь сохранён", "success");
      setEditing(null); setForm(EMPTY); setPassword("");
    } catch (error) { showToast(error.message, "error"); }
    finally { setBusy(false); }
  }

  async function toggle() {
    try {
      const saved = await (form.enabled ? api.disableUser(form.employee_id) : api.enableUser(form.employee_id));
      if (saved) refs.upsertUser(saved);
      setEditing(null); setForm(EMPTY);
      showToast("Состояние изменено", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  async function remove() {
    if (!confirm("Удалить пользователя?")) return;
    try {
      await api.deleteUser(form.employee_id);
      refs.removeUser(form.employee_id);
      setEditing(null); setForm(EMPTY);
      showToast("Пользователь удалён", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  async function attach() {
    try {
      const saved = await api.attachUserAccount(form.employee_id, { login: form.login, password, enable_account: true });
      if (saved) refs.upsertUser(saved);
      if (saved) setForm({ ...saved, roles: [...(saved.roles || [])] });
      setPassword("");
      showToast("Аккаунт подключён", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  async function detach() {
    try {
      const saved = await api.detachUserAccount(form.employee_id);
      if (saved) refs.upsertUser(saved);
      if (saved) setForm({ ...saved, roles: [...(saved.roles || [])] });
      showToast("Аккаунт отключён", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  async function changePassword() {
    try {
      const saved = await api.changeUserPassword(form.employee_id, password);
      if (saved) refs.upsertUser(saved);
      setPassword("");
      showToast("Пароль изменён", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  if (!mayView) return <div className="empty-permission">Нет права просмотра пользователей.</div>;

  return <div>
    <div className="view-header">
      <div><h1>Пользователи клиентов</h1><p>Список загружается при входе в раздел и сохраняется в общем frontend-кэше.</p></div>
      <div className="view-actions"><button className="btn" onClick={() => load(true)}>Обновить</button>{mayOperate && <button className="btn btn-primary" onClick={() => open()}>Создать</button>}</div>
    </div>

    <div className="inline-filter-row"><label><span>Клиент</span><select value={clientFilter} onChange={(e) => setClientFilter(Number(e.target.value))}><option value="0">Все</option>{clients.map((c) => <option key={c.client_id} value={c.client_id}>{c.name}</option>)}</select></label></div>
    <DataTable storageKey="users.all" title="Пользователи" rows={rows} columns={columns} getRowId={(row) => row.employee_id} onRowClick={open} extraFilters={(row) => !clientFilter || Number(row.client_id) === clientFilter} />

    {form && (editing !== null || form.employee_id === 0) && (editing || form !== EMPTY) && <Modal title={form.employee_id ? `Пользователь #${form.employee_id}` : "Новый пользователь"} onClose={() => { setEditing(null); setForm(EMPTY); }}>
      <div className="form-grid">
        <label><span>Клиент</span><select disabled={Boolean(form.employee_id) || !mayOperate} value={form.client_id} onChange={(e) => setForm({ ...form, client_id: Number(e.target.value) })}><option value="0">—</option>{clients.map((client) => <option key={client.client_id} value={client.client_id}>{client.name}</option>)}</select></label>
        <label><span>Имя</span><input disabled={!mayOperate} value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></label>
        <label><span>Фамилия</span><input disabled={!mayOperate} value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></label>
        <label><span>Email</span><input disabled={!mayOperate} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
        <label><span>Телефон</span><input disabled={!mayOperate} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
        <label><span>Логин</span><input disabled={!mayOperate} value={form.login || ""} onChange={(e) => setForm({ ...form, login: e.target.value })} /></label>
        <label><span>{form.employee_id ? "Пароль / новый пароль" : "Пароль"}</span><input type="password" disabled={!mayOperate} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {rolesLoaded && mayChangeRoles && <div className="wide-field"><span className="field-caption">Роли пользователя</span><RolePicker roles={roles} selected={form.roles} disabled={!mayOperate} onChange={(value) => setForm({ ...form, roles: value })} /></div>}
        {!rolesLoaded && form.employee_id > 0 && Boolean(form.roles?.length) && <div className="wide-field"><span className="field-caption">ID ролей</span><div className="permission-chips">{form.roles.map((id) => <span key={id} className="badge badge-info">#{id}</span>)}</div></div>}
      </div>
      {mayOperate && <div className="card-actions">
        <button className="btn btn-primary" disabled={busy || !form.first_name || !form.client_id} onClick={save}>{busy ? "Сохранение..." : "Сохранить"}</button>
        {form.employee_id > 0 && <>
          <button className="btn" onClick={toggle}>{form.enabled ? "Отключить" : "Включить"}</button>
          <button className="btn" disabled={!form.login || !password} onClick={attach}>Подключить аккаунт</button>
          <button className="btn" disabled={!form.login} onClick={detach}>Отключить аккаунт</button>
          <button className="btn" disabled={!password} onClick={changePassword}>Сменить пароль</button>
          {onNavigate && <button className="btn" onClick={() => onNavigate("tickets", { userId: form.employee_id })}>Заявки пользователя</button>}
          <button className="btn btn-danger" onClick={remove}>Удалить</button>
        </>}
      </div>}
    </Modal>}
  </div>;
}
