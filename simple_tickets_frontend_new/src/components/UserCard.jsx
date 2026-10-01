import { useEffect, useState } from "react";
import { api } from "../api.js";
import AccountPanel from "./AccountPanel.jsx";

function makeForm(user, clientId) {
  return {
    employee_id: user?.employee_id || 0,
    client_id: user?.client_id || clientId,
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
    email: user?.email || "",
    phone: user?.phone || "",
    login: user?.login || "",
    enabled: user?.enabled ?? true,
    enabled_login: user?.enabled_login ?? false,
    roles: user?.roles || [],
  };
}

export default function UserCard({ user, clientId, canOperate, onUserChanged, onUserDeleted, showToast }) {
  const [form, setForm] = useState(() => makeForm(user, clientId));
  const [saving, setSaving] = useState(false);

  const isNew = !form.employee_id;

  useEffect(() => {
    setForm(makeForm(user, clientId));
  }, [user?.employee_id, clientId]);

  if (!user) {
    return (
      <aside className="user-card empty-user-card">
        <h3>Карточка пользователя</h3>
        <p>Выберите пользователя в списке или создайте нового.</p>
      </aside>
    );
  }

  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function saveUser() {
    setSaving(true);
    try {
      let nextUser;
      if (isNew) {
        nextUser = await api.createUser({
          client_id: clientId,
          first_name: form.first_name,
          last_name: form.last_name,
          email: form.email,
          phone: form.phone,
          login: form.login || "",
          password: "",
          enable: form.enabled,
          enable_account: false,
          roles: [],
        });
        showToast("Пользователь создан", "success");
      } else {
        nextUser = await api.updateUser(form.employee_id, {
          first_name: form.first_name,
          last_name: form.last_name,
          email: form.email,
          phone: form.phone,
        });
        showToast("Пользователь сохранён", "success");
      }
      await onUserChanged(nextUser);
    } catch (error) {
      showToast(error.message || "Не удалось сохранить пользователя", "error");
    } finally {
      setSaving(false);
    }
  }

  async function toggleEnabled() {
    if (isNew) return;
    try {
      const nextUser = form.enabled ? await api.disableUser(form.employee_id) : await api.enableUser(form.employee_id);
      await onUserChanged(nextUser);
      showToast(nextUser.enabled ? "Пользователь включён" : "Пользователь отключён", "success");
    } catch (error) {
      showToast(error.message || "Не удалось изменить состояние пользователя", "error");
    }
  }

  async function deleteUser() {
    if (isNew) return;
    if (!confirm(`Удалить пользователя ${form.first_name} ${form.last_name}?`)) return;
    try {
      await api.deleteUser(form.employee_id);
      await onUserDeleted(form.employee_id);
      showToast("Пользователь удалён", "success");
    } catch (error) {
      showToast(error.message || "Не удалось удалить пользователя", "error");
    }
  }

  async function refreshUser() {
    if (isNew) return;
    try {
      const nextUser = await api.getUser(form.employee_id);
      await onUserChanged(nextUser);
    } catch (error) {
      showToast(error.message || "Не удалось обновить пользователя", "error");
    }
  }

  return (
    <aside className="user-card">
      <div className="user-card-header">
        <div>
          <h3>{isNew ? "Новый пользователь" : `${form.first_name || "Пользователь"} ${form.last_name || ""}`}</h3>
          <p>{isNew ? "Создание пользователя клиента" : `ID ${form.employee_id}`}</p>
        </div>
        {!isNew && <span className={form.enabled ? "badge badge-ok" : "badge badge-muted"}>{form.enabled ? "Активен" : "Отключён"}</span>}
      </div>

      <div className="form-grid compact">
        <label>
          <span>Имя</span>
          <input value={form.first_name} disabled={!canOperate} onChange={(e) => update("first_name", e.target.value)} />
        </label>
        <label>
          <span>Фамилия</span>
          <input value={form.last_name} disabled={!canOperate} onChange={(e) => update("last_name", e.target.value)} />
        </label>
        <label>
          <span>Email</span>
          <input value={form.email} disabled={!canOperate} onChange={(e) => update("email", e.target.value)} />
        </label>
        <label>
          <span>Телефон</span>
          <input value={form.phone} disabled={!canOperate} onChange={(e) => update("phone", e.target.value)} />
        </label>
      </div>

      {canOperate && (
        <div className="card-actions">
          <button className="btn btn-primary" disabled={saving || !form.first_name.trim()} onClick={saveUser}>{saving ? "Сохранение..." : "Сохранить"}</button>
          {!isNew && <button className="btn" onClick={toggleEnabled}>{form.enabled ? "Отключить" : "Включить"}</button>}
          {!isNew && <button className="btn btn-danger" onClick={deleteUser}>Удалить</button>}
        </div>
      )}

      {!isNew && (
        <AccountPanel
          user={form}
          canOperate={canOperate}
          onChanged={refreshUser}
          showToast={showToast}
        />
      )}
    </aside>
  );
}
