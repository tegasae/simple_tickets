import { useState } from "react";
import ThemeSwitcher from "./ThemeSwitcher.jsx";

export default function LoginPage({ theme, themes, onThemeChange, initialClientId, onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [clientId, setClientId] = useState(initialClientId || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    const normalizedClientId = Number(clientId);
    if (!Number.isInteger(normalizedClientId) || normalizedClientId <= 0) {
      setError("Укажите положительный Client ID");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await onLogin(username.trim(), password, normalizedClientId);
    } catch (err) {
      setError(err.message || "Не удалось войти");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page user-login-page">
      <div className="login-card window-animate">
        <div className="login-brand">
          <div className="brand-mark">ST</div>
          <div>
            <h1>Simple Tickets</h1>
            <p>Кабинет пользователя клиента</p>
          </div>
        </div>

        <div className="login-theme-row">
          <span className="field-caption">Интерфейс</span>
          <ThemeSwitcher theme={theme} themes={themes} onThemeChange={onThemeChange} />
        </div>

        <form className="login-form" onSubmit={submit}>
          <label>
            <span>Client ID</span>
            <input type="number" min="1" value={clientId} onChange={(e) => setClientId(e.target.value)} required />
          </label>
          <label>
            <span>Логин</span>
            <input autoFocus autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
          </label>
          <label>
            <span>Пароль</span>
            <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          {error ? <div className="form-error">{error}</div> : null}
          <button className="btn btn-primary btn-wide" disabled={busy}>
            {busy ? "Вход…" : "Войти"}
          </button>
        </form>

        <p className="login-hint">
          Client ID используется как контекст организации для списка и создания заявок. Авторизация выполняется только по логину и паролю.
        </p>
      </div>
    </div>
  );
}
