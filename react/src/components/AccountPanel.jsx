import { useState } from "react";
import { api } from "../api.js";

export default function AccountPanel({ user, canOperate, onChanged, showToast }) {
  const [attachLogin, setAttachLogin] = useState(user.login || "");
  const [attachPassword, setAttachPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [busy, setBusy] = useState(false);

  async function attachAccount() {
    setBusy(true);
    try {
      await api.attachUserAccount(user.employee_id, {
        login: attachLogin,
        password: attachPassword,
        enable_account: true,
      });
      setAttachPassword("");
      await onChanged();
      showToast("Аккаунт подключён", "success");
    } catch (error) {
      showToast(error.message || "Не удалось подключить аккаунт", "error");
    } finally {
      setBusy(false);
    }
  }

  async function detachAccount() {
    if (!confirm("Отключить аккаунт пользователя?")) return;
    setBusy(true);
    try {
      await api.detachUserAccount(user.employee_id);
      await onChanged();
      showToast("Аккаунт отключён", "success");
    } catch (error) {
      showToast(error.message || "Не удалось отключить аккаунт", "error");
    } finally {
      setBusy(false);
    }
  }

  async function changePassword() {
    setBusy(true);
    try {
      await api.changeUserPassword(user.employee_id, newPassword);
      setNewPassword("");
      await onChanged();
      showToast("Пароль изменён", "success");
    } catch (error) {
      showToast(error.message || "Не удалось изменить пароль", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="account-panel">
      <h4>Аккаунт</h4>
      <dl className="mini-dl">
        <dt>Логин</dt>
        <dd>{user.login || "—"}</dd>
        <dt>Вход</dt>
        <dd>{user.enabled_login ? "включён" : "не включён"}</dd>
      </dl>

      {canOperate && (
        <div className="account-actions">
          <label>
            <span>Логин</span>
            <input value={attachLogin} onChange={(e) => setAttachLogin(e.target.value)} />
          </label>
          <label>
            <span>Пароль для attach</span>
            <input type="password" value={attachPassword} onChange={(e) => setAttachPassword(e.target.value)} />
          </label>
          <button className="btn btn-small" disabled={busy || !attachLogin || !attachPassword} onClick={attachAccount}>Подключить / заменить</button>
          <button className="btn btn-small" disabled={busy || !user.login} onClick={detachAccount}>Отключить аккаунт</button>

          <label>
            <span>Новый пароль</span>
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </label>
          <button className="btn btn-small" disabled={busy || !newPassword || !user.login} onClick={changePassword}>Сменить пароль</button>
        </div>
      )}
    </section>
  );
}
