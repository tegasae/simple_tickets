import { useEffect, useState } from "react";
import { api } from "../api.js";
import { can } from "../permissions.js";
import DataTable from "./DataTable.jsx";
import Modal from "./Modal.jsx";

const EMPTY = { role_id: 0, name: "", description: "", permissions: [], is_system_role: false };

export default function RolesPage({ permissions, showToast }) {
  const [mode, setMode] = useState("admin");
  const [rows, setRows] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const mayView = can.rolesView(permissions);
  const mayOperate = can.rolesOperate(permissions);

  async function load() {
    if (!mayView) return;
    try {
      const roleLoader = mode === "admin" ? api.getAdminRoles : api.getUserRoles;
      const permissionLoader = mode === "admin" ? api.getAdminPermissionsCatalog : api.getUserPermissionsCatalog;
      const rolesPayload = await roleLoader();
      setRows(Array.isArray(rolesPayload) ? rolesPayload : []);
      try {
        const permissionPayload = await permissionLoader();
        setCatalog(Array.isArray(permissionPayload) ? permissionPayload : []);
      } catch {
        setCatalog([]);
      }
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  useEffect(() => {
    load();
    setForm(EMPTY);
  }, [mode, mayView]);

  const columns = [
    { key: "role_id", label: "ID", className: "num" },
    { key: "name", label: "Роль" },
    { key: "description", label: "Описание" },
    {
      key: "permissions",
      label: "Permissions",
      getValue: (row) => (row.permissions || []).join(", "),
      render: (row) => <div className="permission-chips">{(row.permissions || []).map((permission) => <span key={permission} className="badge badge-info">{permission}</span>)}</div>,
    },
    { key: "is_system_role", label: "System", render: (row) => <span className={row.is_system_role ? "badge badge-info" : "badge badge-muted"}>{row.is_system_role ? "Да" : "Нет"}</span> },
  ];

  function togglePermission(permission) {
    const selected = new Set(form.permissions);
    if (selected.has(permission)) selected.delete(permission);
    else selected.add(permission);
    setForm({ ...form, permissions: [...selected] });
  }

  async function save() {
    try {
      const payload = {
        name: form.name,
        description: form.description,
        permissions: form.permissions,
        is_system_role: Boolean(form.is_system_role),
      };
      if (mode === "admin") await api.createAdminRole(payload);
      else await api.createUserRole(payload);
      setForm(EMPTY);
      await load();
      showToast("Роль создана", "success");
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function remove() {
    if (form.is_system_role && !confirm("Это системная роль. Попытаться удалить?")) return;
    if (!form.is_system_role && !confirm("Удалить роль?")) return;
    try {
      if (mode === "admin") await api.deleteAdminRole(form.role_id);
      else await api.deleteUserRole(form.role_id);
      setForm(EMPTY);
      await load();
      showToast("Роль удалена", "success");
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  if (!mayView) return <div className="empty-permission">Нет права управления ролями.</div>;

  return (
    <div>
      <div className="view-header">
        <div><h1>Роли</h1><p>Admin и User realms разделены.</p></div>
        <div className="view-actions"><button className="btn" onClick={load}>Обновить</button>{mayOperate && <button className="btn btn-primary" onClick={() => setForm({ ...EMPTY, permissions: [] })}>Создать роль</button>}</div>
      </div>
      <div className="segmented-filter"><button className={mode === "admin" ? "active" : ""} onClick={() => setMode("admin")}>Admin roles</button><button className={mode === "user" ? "active" : ""} onClick={() => setMode("user")}>User roles</button></div>
      <DataTable storageKey={`roles.${mode}`} title={mode === "admin" ? "Admin roles" : "User roles"} rows={rows} columns={columns} getRowId={(row) => row.role_id} onRowClick={(row) => setForm({ ...row, permissions: [...(row.permissions || [])] })} />
      {form !== EMPTY && (
        <Modal title={form.role_id ? `Роль #${form.role_id}` : `Новая ${mode} role`} onClose={() => setForm(EMPTY)}>
          <div className="form-grid compact">
            <label><span>Название</span><input disabled={form.role_id > 0 || !mayOperate} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label><span>Описание</span><textarea disabled={form.role_id > 0 || !mayOperate} rows="3" value={form.description || ""} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
            <label className="check-row"><input type="checkbox" disabled={form.role_id > 0 || !mayOperate} checked={Boolean(form.is_system_role)} onChange={(e) => setForm({ ...form, is_system_role: e.target.checked })} /><span>Системная роль</span></label>
            <div><span className="field-caption">Permissions</span><div className="permission-grid">{catalog.map((permission) => <label key={permission} className="check-row"><input type="checkbox" disabled={form.role_id > 0 || !mayOperate} checked={(form.permissions || []).includes(permission)} onChange={() => togglePermission(permission)} /><span>{permission}</span></label>)}</div></div>
          </div>
          <div className="card-actions">
            {!form.role_id && mayOperate && <button className="btn btn-primary" disabled={!form.name.trim() || !form.permissions.length} onClick={save}>Создать</button>}
            {form.role_id > 0 && mayOperate && <button className="btn btn-danger" onClick={remove}>Удалить</button>}
          </div>
        </Modal>
      )}
    </div>
  );
}
