import { useEffect, useMemo, useState } from "react";
import { canClientOperate, canClientView } from "../permissions.js";
import { useReferenceData } from "../referenceData.jsx";
import { loadSetting, saveSetting } from "../storage.js";
import DataTable from "./DataTable.jsx";
import ClientDialog from "./ClientDialog.jsx";

const CLIENT_COLUMNS = [
  { key: "client_id", label: "ID", getValue: (row) => row.client_id, className: "num" },
  { key: "name", label: "Наименование", getValue: (row) => row.name },
  { key: "email", label: "Email", getValue: (row) => row.email },
  { key: "phone", label: "Телефон", getValue: (row) => row.phone },
  { key: "address", label: "Адрес", getValue: (row) => row.address },
  { key: "description", label: "Описание", getValue: (row) => row.description },
  {
    key: "enabled",
    label: "Активен",
    getValue: (row) => row.enabled,
    render: (row) => <span className={row.enabled ? "badge badge-ok" : "badge badge-muted"}>{row.enabled ? "Да" : "Нет"}</span>,
  },
];

export default function ClientsPage({ permissions, showToast, onNavigate, pageContext }) {
  const refs = useReferenceData();
  const { clients } = refs;
  const [loading, setLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState(() => loadSetting("clients.activeFilter", "all"));
  const [dialogClient, setDialogClient] = useState(null);
  const [dialogMode, setDialogMode] = useState("view");

  const mayView = canClientView(permissions);
  const mayOperate = canClientOperate(permissions);

  useEffect(() => saveSetting("clients.activeFilter", activeFilter), [activeFilter]);

  useEffect(() => {
    if (!mayView) return;
    refs.ensureClients().catch((error) => showToast(error.message || "Не удалось загрузить клиентов", "error"));
  }, [mayView]);

  useEffect(() => {
    const clientId = Number(pageContext?.openClientId || 0);
    if (!clientId || !mayView) return;
    refs.ensureClient(clientId)
      .then((client) => { setDialogMode("view"); setDialogClient(client); })
      .catch((error) => showToast(error.message, "error"));
  }, [pageContext?.openClientId, mayView]);

  async function loadClients() {
    setLoading(true);
    try { await refs.ensureClients(true); }
    catch (error) { showToast(error.message || "Не удалось загрузить клиентов", "error"); }
    finally { setLoading(false); }
  }

  const extraFilters = useMemo(() => (row) => {
    if (activeFilter === "active") return Boolean(row.enabled);
    if (activeFilter === "inactive") return !row.enabled;
    return true;
  }, [activeFilter]);

  function openCreateDialog() {
    setDialogMode("create");
    setDialogClient({ client_id: 0, name: "", email: "", address: "", phone: "", description: "", enabled: true, date_created: "", created_by_admin: 0 });
  }

  function openClient(client) {
    setDialogMode("view");
    setDialogClient(client);
  }

  function closeDialog() { setDialogClient(null); }

  async function handleClientChanged(nextClient, options = {}) {
    if (nextClient) {
      refs.upsertClient(nextClient);
      setDialogClient(nextClient);
      setDialogMode("view");
    }
    if (options.reload) await loadClients();
  }

  async function handleDeleted(clientId) {
    refs.removeClient(clientId);
    closeDialog();
  }

  if (!mayView) return <div className="empty-permission">Нет права просмотра клиентов.</div>;

  return <div className="clients-page">
    <div className="view-header">
      <div><h1>Клиенты</h1><p>Справочник хранится в общем frontend-кэше и обновляется по запросу.</p></div>
      <div className="view-actions">
        <button className="btn" onClick={loadClients} disabled={loading}>{loading ? "Обновление..." : "Обновить"}</button>
        {mayOperate && <button className="btn btn-primary" onClick={openCreateDialog}>Создать клиента</button>}
      </div>
    </div>

    <div className="segmented-filter">
      {[["all", "Все"], ["active", "Активные"], ["inactive", "Неактивные"]].map(([value, label]) => (
        <button key={value} className={activeFilter === value ? "active" : ""} onClick={() => setActiveFilter(value)}>{label}</button>
      ))}
    </div>

    <DataTable storageKey="table.clients" title="Список клиентов" rows={clients} columns={CLIENT_COLUMNS} selectedId={dialogClient?.client_id} getRowId={(row) => row.client_id} onRowClick={openClient} extraFilters={extraFilters} emptyText={loading ? "Загрузка..." : "Клиенты не найдены"} />

    {dialogClient && <ClientDialog mode={dialogMode} client={dialogClient} permissions={permissions} onClose={closeDialog} onClientChanged={handleClientChanged} onDeleted={handleDeleted} showToast={showToast} onNavigate={onNavigate} />}
  </div>;
}
