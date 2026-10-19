import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { canClientOperate, canClientView } from "../permissions.js";
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

export default function ClientsPage({ permissions, showToast }) {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState(() => loadSetting("clients.activeFilter", "all"));
  const [dialogClient, setDialogClient] = useState(null);
  const [dialogMode, setDialogMode] = useState("view");

  const mayView = canClientView(permissions);
  const mayOperate = canClientOperate(permissions);

  useEffect(() => {
    saveSetting("clients.activeFilter", activeFilter);
  }, [activeFilter]);

  useEffect(() => {
    if (mayView) loadClients();
  }, [mayView]);

  async function loadClients() {
    setLoading(true);
    try {
      const payload = await api.getClients();
      setClients(Array.isArray(payload) ? payload : []);
    } catch (error) {
      showToast(error.message || "Не удалось загрузить клиентов", "error");
    } finally {
      setLoading(false);
    }
  }

  const extraFilters = useMemo(() => {
    return (row) => {
      if (activeFilter === "active") return Boolean(row.enabled);
      if (activeFilter === "inactive") return !row.enabled;
      return true;
    };
  }, [activeFilter]);

  function openCreateDialog() {
    setDialogMode("create");
    setDialogClient({
      client_id: 0,
      name: "",
      email: "",
      address: "",
      phone: "",
      description: "",
      enabled: true,
      date_created: "",
      created_by_admin: 0,
    });
  }

  async function openClient(client) {
    try {
      const fresh = await api.getClient(client.client_id);
      setDialogMode("view");
      setDialogClient(fresh);
    } catch (error) {
      showToast(error.message || "Не удалось открыть клиента", "error");
    }
  }

  function closeDialog() {
    setDialogClient(null);
  }

  async function handleClientChanged(nextClient, options = {}) {
    if (nextClient) {
      setClients((current) => {
        const exists = current.some((item) => item.client_id === nextClient.client_id);
        if (exists) return current.map((item) => item.client_id === nextClient.client_id ? nextClient : item);
        return [nextClient, ...current];
      });
      setDialogClient(nextClient);
      setDialogMode("view");
    }
    if (options.reload) await loadClients();
  }

  async function handleDeleted(clientId) {
    setClients((current) => current.filter((item) => item.client_id !== clientId));
    closeDialog();
  }

  if (!mayView) {
    return <div className="empty-permission">Нет права просмотра клиентов.</div>;
  }

  return (
    <div className="clients-page">
      <div className="view-header">
        <div>
          <h1>Клиенты</h1>
          <p>Список загружается целиком, фильтрация и пагинация выполняются в браузере.</p>
        </div>
        <div className="view-actions">
          <button className="btn" onClick={loadClients} disabled={loading}>{loading ? "Обновление..." : "Обновить"}</button>
          {mayOperate && <button className="btn btn-primary" onClick={openCreateDialog}>Создать клиента</button>}
        </div>
      </div>

      <div className="segmented-filter">
        {[
          ["all", "Все"],
          ["active", "Активные"],
          ["inactive", "Неактивные"],
        ].map(([value, label]) => (
          <button key={value} className={activeFilter === value ? "active" : ""} onClick={() => setActiveFilter(value)}>
            {label}
          </button>
        ))}
      </div>

      <DataTable
        storageKey="table.clients"
        title="Список клиентов"
        rows={clients}
        columns={CLIENT_COLUMNS}
        selectedId={dialogClient?.client_id}
        getRowId={(row) => row.client_id}
        onRowClick={openClient}
        extraFilters={extraFilters}
        emptyText={loading ? "Загрузка..." : "Клиенты не найдены"}
      />

      {dialogClient && (
        <ClientDialog
          mode={dialogMode}
          client={dialogClient}
          permissions={permissions}
          onClose={closeDialog}
          onClientChanged={handleClientChanged}
          onDeleted={handleDeleted}
          showToast={showToast}
        />
      )}
    </div>
  );
}
