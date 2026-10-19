import { useEffect, useState } from "react";
import { api } from "../api.js";
import { canClientOperate, canUserOperate, canUserView } from "../permissions.js";
import { loadSetting, saveSetting } from "../storage.js";
import DataTable from "./DataTable.jsx";
import UserCard from "./UserCard.jsx";

const USER_COLUMNS = [
  { key: "employee_id", label: "ID", getValue: (row) => row.employee_id, className: "num" },
  { key: "first_name", label: "Имя", getValue: (row) => row.first_name },
  { key: "last_name", label: "Фамилия", getValue: (row) => row.last_name },
  { key: "email", label: "Email", getValue: (row) => row.email },
  { key: "phone", label: "Телефон", getValue: (row) => row.phone },
  { key: "login", label: "Логин", getValue: (row) => row.login },
  {
    key: "enabled",
    label: "Активен",
    getValue: (row) => row.enabled,
    render: (row) => <span className={row.enabled ? "badge badge-ok" : "badge badge-muted"}>{row.enabled ? "Да" : "Нет"}</span>,
  },
  {
    key: "enabled_login",
    label: "Аккаунт",
    getValue: (row) => row.enabled_login,
    render: (row) => <span className={row.login ? "badge badge-info" : "badge badge-muted"}>{row.login || "—"}</span>,
  },
];

function makeClientForm(client) {
  return {
    name: client.name || "",
    email: client.email || "",
    address: client.address || "",
    phone: client.phone || "",
    description: client.description || "",
  };
}

function emptyUser(clientId) {
  return {
    employee_id: 0,
    client_id: clientId,
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    login: "",
    enabled: true,
    enabled_login: false,
    roles: [],
  };
}

export default function ClientDialog({ mode, client, permissions, onClose, onClientChanged, onDeleted, showToast }) {
  const [activeTab, setActiveTab] = useState(() => loadSetting("clientDialog.activeTab", "main"));
  const [minimized, setMinimized] = useState(false);
  const [form, setForm] = useState(() => makeClientForm(client));
  const [saving, setSaving] = useState(false);
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [activeUserFilter, setActiveUserFilter] = useState(() => loadSetting("users.activeFilter", "all"));

  const mayClientOperate = canClientOperate(permissions);
  const mayUserView = canUserView(permissions);
  const mayUserOperate = canUserOperate(permissions);
  const isCreateMode = mode === "create" || client.client_id === 0;

  useEffect(() => {
    setForm(makeClientForm(client));
  }, [client.client_id]);

  useEffect(() => {
    saveSetting("clientDialog.activeTab", activeTab);
    if (activeTab === "users" && client.client_id && mayUserView) loadUsers();
  }, [activeTab, client.client_id, mayUserView]);

  useEffect(() => {
    saveSetting("users.activeFilter", activeUserFilter);
  }, [activeUserFilter]);

  function updateForm(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function loadUsers() {
    setUsersLoading(true);
    try {
      const payload = await api.getUsers(client.client_id);
      setUsers(Array.isArray(payload) ? payload : []);
    } catch (error) {
      showToast(error.message || "Не удалось загрузить пользователей", "error");
    } finally {
      setUsersLoading(false);
    }
  }

  async function saveClient() {
    setSaving(true);
    try {
      let nextClient;
      if (isCreateMode) {
        nextClient = await api.createClient({
          name: form.name,
          email: form.email,
          address: form.address,
          phone: form.phone,
          description: form.description,
        });
        showToast("Клиент создан", "success");
      } else {
        nextClient = await api.updateClientContact(client.client_id, {
          name: form.name,
          email: form.email,
          address: form.address,
          phone: form.phone,
          description: form.description,
        });
        showToast("Клиент сохранён", "success");
      }
      onClientChanged(nextClient);
    } catch (error) {
      showToast(error.message || "Не удалось сохранить клиента", "error");
    } finally {
      setSaving(false);
    }
  }

  async function toggleClientEnabled() {
    if (isCreateMode) return;
    setSaving(true);
    try {
      const nextClient = client.enabled ? await api.disableClient(client.client_id) : await api.enableClient(client.client_id);
      onClientChanged(nextClient);
      showToast(nextClient.enabled ? "Клиент включён" : "Клиент отключён", "success");
    } catch (error) {
      showToast(error.message || "Не удалось изменить состояние клиента", "error");
    } finally {
      setSaving(false);
    }
  }

  async function deleteClient() {
    if (isCreateMode) return;
    if (!confirm(`Удалить клиента "${client.name}"?`)) return;
    try {
      await api.deleteClient(client.client_id);
      await onDeleted(client.client_id);
      showToast("Клиент удалён", "success");
    } catch (error) {
      showToast(error.message || "Не удалось удалить клиента", "error");
    }
  }

  function selectUser(user) {
    setSelectedUser(user);
  }

  function createUser() {
    setSelectedUser(emptyUser(client.client_id));
  }

  async function handleUserChanged(nextUser, options = {}) {
    if (nextUser) {
      setUsers((current) => {
        const exists = current.some((item) => item.employee_id === nextUser.employee_id);
        if (exists) return current.map((item) => item.employee_id === nextUser.employee_id ? nextUser : item);
        return [nextUser, ...current];
      });
      setSelectedUser(nextUser);
    }
    if (options.reload) await loadUsers();
  }

  async function handleUserDeleted(employeeId) {
    setUsers((current) => current.filter((item) => item.employee_id !== employeeId));
    setSelectedUser(null);
  }

  const filteredUsers = (row) => {
    if (activeUserFilter === "active") return Boolean(row.enabled);
    if (activeUserFilter === "inactive") return !row.enabled;
    return true;
  };

  if (minimized) {
    return (
      <div className="minimized-window" onClick={() => setMinimized(false)}>
        <span>Клиент</span>
        <strong>{client.name || "Новый клиент"}</strong>
        <button className="btn btn-small">Развернуть</button>
      </div>
    );
  }

  return (
    <div className="modal-backdrop">
      <div className="client-dialog window-animate">
        <header className="dialog-titlebar">
          <div>
            <h2>{isCreateMode ? "Новый клиент" : client.name}</h2>
            <p>{isCreateMode ? "Создание карточки клиента" : `ID ${client.client_id}`}</p>
          </div>
          <div className="window-controls">
            <button className="btn btn-icon" title="Свернуть" onClick={() => setMinimized(true)}>—</button>
            <button className="btn btn-icon" title="Закрыть" onClick={onClose}>×</button>
          </div>
        </header>

        <div className="dialog-tabs">
          <button className={activeTab === "main" ? "active" : ""} onClick={() => setActiveTab("main")}>Основное</button>
          <button className={activeTab === "users" ? "active" : ""} onClick={() => setActiveTab("users")} disabled={isCreateMode}>Пользователи</button>
        </div>

        <main className="dialog-body">
          {activeTab === "main" && (
            <section className="client-main-grid">
              <div className="form-panel">
                <div className="form-grid">
                  <label>
                    <span>Наименование</span>
                    <input value={form.name} disabled={!mayClientOperate} onChange={(e) => updateForm("name", e.target.value)} />
                  </label>
                  <label>
                    <span>Email</span>
                    <input value={form.email} disabled={!mayClientOperate} onChange={(e) => updateForm("email", e.target.value)} />
                  </label>
                  <label>
                    <span>Телефон</span>
                    <input value={form.phone} disabled={!mayClientOperate} onChange={(e) => updateForm("phone", e.target.value)} />
                  </label>
                  <label>
                    <span>Адрес</span>
                    <input value={form.address} disabled={!mayClientOperate} onChange={(e) => updateForm("address", e.target.value)} />
                  </label>
                  <label className="wide-field">
                    <span>Описание</span>
                    <textarea value={form.description} disabled={!mayClientOperate} onChange={(e) => updateForm("description", e.target.value)} rows={5} />
                  </label>
                </div>
              </div>

              <aside className="meta-panel">
                <dl>
                  <dt>ID</dt>
                  <dd>{client.client_id || "—"}</dd>
                  <dt>Создан</dt>
                  <dd>{client.date_created || "—"}</dd>
                  <dt>Создал admin</dt>
                  <dd>{client.created_by_admin || "—"}</dd>
                  <dt>Статус</dt>
                  <dd><span className={client.enabled ? "badge badge-ok" : "badge badge-muted"}>{client.enabled ? "Активен" : "Отключён"}</span></dd>
                </dl>
                {mayClientOperate && (
                  <div className="vertical-actions">
                    <button className="btn btn-primary" onClick={saveClient} disabled={saving || !form.name.trim()}>{saving ? "Сохранение..." : "Сохранить"}</button>
                    {!isCreateMode && <button className="btn" onClick={toggleClientEnabled}>{client.enabled ? "Отключить" : "Включить"}</button>}
                    {!isCreateMode && <button className="btn btn-danger" onClick={deleteClient}>Удалить</button>}
                  </div>
                )}
              </aside>
            </section>
          )}

          {activeTab === "users" && (
            <section className="client-users-layout">
              <div className="users-left">
                {!mayUserView ? (
                  <div className="empty-permission">Нет права просмотра пользователей.</div>
                ) : (
                  <>
                    <div className="segmented-filter inline">
                      {[
                        ["all", "Все"],
                        ["active", "Активные"],
                        ["inactive", "Неактивные"],
                      ].map(([value, label]) => (
                        <button key={value} className={activeUserFilter === value ? "active" : ""} onClick={() => setActiveUserFilter(value)}>
                          {label}
                        </button>
                      ))}
                    </div>
                    <DataTable
                      storageKey={`table.users.client.${client.client_id}`}
                      title="Пользователи клиента"
                      rows={users}
                      columns={USER_COLUMNS}
                      selectedId={selectedUser?.employee_id}
                      getRowId={(row) => row.employee_id}
                      onRowClick={selectUser}
                      extraFilters={filteredUsers}
                      emptyText={usersLoading ? "Загрузка..." : "Пользователи не найдены"}
                      actions={(
                        <>
                          <button className="btn btn-small" onClick={loadUsers}>{usersLoading ? "..." : "Обновить"}</button>
                          {mayUserOperate && <button className="btn btn-primary btn-small" onClick={createUser}>Создать пользователя</button>}
                        </>
                      )}
                    />
                  </>
                )}
              </div>
              <div className="users-right">
                <UserCard
                  user={selectedUser}
                  clientId={client.client_id}
                  canOperate={mayUserOperate}
                  onUserChanged={handleUserChanged}
                  onUserDeleted={handleUserDeleted}
                  showToast={showToast}
                />
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
