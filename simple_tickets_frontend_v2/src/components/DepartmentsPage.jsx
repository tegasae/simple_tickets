import { useEffect, useState } from "react";
import { api } from "../api.js";
import { can } from "../permissions.js";
import { useReferenceData } from "../referenceData.jsx";
import DataTable from "./DataTable.jsx";
import Modal from "./Modal.jsx";

const EMPTY = { department_id: 0, name: "", enabled: true };

export default function DepartmentsPage({ permissions, showToast }) {
  const refs = useReferenceData();
  const { departments: rows } = refs;
  const [form, setForm] = useState(EMPTY);
  const mayView = can.departmentsView(permissions);
  const mayOperate = can.departmentsOperate(permissions);

  async function load(force = false) {
    if (!mayView) return;
    try { await refs.ensureDepartments(force); }
    catch (error) { showToast(error.message, "error"); }
  }

  useEffect(() => { load(false); }, [mayView]);

  const columns = [
    { key: "department_id", label: "ID", className: "num" },
    { key: "name", label: "Название" },
    { key: "enabled", label: "Активен", render: (row) => <span className={row.enabled ? "badge badge-ok" : "badge badge-muted"}>{row.enabled ? "Да" : "Нет"}</span> },
    { key: "date_created", label: "Создан" },
  ];

  async function save() {
    try {
      const saved = form.department_id
        ? await api.updateDepartment(form.department_id, { name: form.name })
        : await api.createDepartment({ name: form.name, enabled: true });
      if (saved) refs.upsertDepartment(saved);
      setForm(EMPTY);
      showToast("Отдел сохранён", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  async function toggle() {
    try {
      const saved = await (form.enabled ? api.disableDepartment(form.department_id) : api.enableDepartment(form.department_id));
      if (saved) refs.upsertDepartment(saved);
      setForm(EMPTY);
    } catch (error) { showToast(error.message, "error"); }
  }

  async function remove() {
    if (!confirm("Удалить отдел?")) return;
    try {
      await api.deleteDepartment(form.department_id);
      refs.removeDepartment(form.department_id);
      setForm(EMPTY);
      showToast("Отдел удалён", "success");
    } catch (error) { showToast(error.message, "error"); }
  }

  if (!mayView) return <div className="empty-permission">Нет права управления отделами.</div>;

  return <div>
    <div className="view-header"><div><h1>Отделы</h1><p>Справочник отделов хранится в общем frontend-кэше.</p></div><div className="view-actions"><button className="btn" onClick={() => load(true)}>Обновить</button>{mayOperate && <button className="btn btn-primary" onClick={() => setForm({ ...EMPTY })}>Создать</button>}</div></div>
    <DataTable storageKey="departments" title="Отделы" rows={rows} columns={columns} getRowId={(row) => row.department_id} onRowClick={(row) => setForm({ ...row })} />
    {form !== EMPTY && <Modal title={form.department_id ? `Отдел #${form.department_id}` : "Новый отдел"} onClose={() => setForm(EMPTY)}><div className="form-grid compact"><label><span>Название</span><input disabled={!mayOperate} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label></div>{mayOperate && <div className="card-actions"><button className="btn btn-primary" disabled={!form.name.trim()} onClick={save}>Сохранить</button>{form.department_id > 0 && <><button className="btn" onClick={toggle}>{form.enabled ? "Отключить" : "Включить"}</button><button className="btn btn-danger" onClick={remove}>Удалить</button></>}</div>}</Modal>}
  </div>;
}
