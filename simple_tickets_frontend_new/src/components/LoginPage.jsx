import { useState } from "react";
import ThemeSwitcher from "./ThemeSwitcher.jsx";

export default function LoginPage({ theme, themes, onThemeChange, onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await onLogin(username.trim(), password);
    } catch (err) {
      setError(err.message || "Не удалось войти");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-brand">
          <div className="brand-mark">ST</div>
          <div>
            <h1>Simple Tickets</h1>
            <p>Администрирование заявок</p>
          </div>
        </div>

        <div className="login-theme-row">
          <span>Интерфейс</span>
          <ThemeSwitcher theme={theme} themes={themes} onThemeChange={onThemeChange} compact />
        </div>

        <form className="login-form" onSubmit={submit}>
          <label>
            <span>Логин</span>
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          </label>
          <label>
            <span>Пароль</span>
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
          </label>
          {error && <div className="form-error">{error}</div>}
          <button className="btn btn-primary btn-wide" disabled={loading || !username || !password}>
            {loading ? "Вход..." : "Войти"}
          </button>
        </form>
      </section>
    </main>
  );
}
