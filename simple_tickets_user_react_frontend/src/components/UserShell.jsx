import ThemeSwitcher from "./ThemeSwitcher.jsx";

export default function UserShell({ clientId, userId, theme, themes, onThemeChange, onLogout, children }) {
  return (
    <div className="app-shell user-shell">
      <aside className="side-nav">
        <div className="side-logo">
          <div className="brand-mark small">ST</div>
          <div>
            <strong>Simple Tickets</strong>
            <span>Кабинет пользователя</span>
          </div>
        </div>

        <nav>
          <button className="nav-item active">Мои заявки</button>
        </nav>

        <div className="user-context-card">
          <span>Организация</span>
          <strong>Client #{clientId}</strong>
          {userId ? <small>User #{userId}</small> : null}
        </div>
      </aside>

      <main className="main-area">
        <header className="top-bar">
          <div>
            <h2>Мои заявки</h2>
            <p>Создание и контроль обращений</p>
          </div>
          <div className="top-actions">
            <ThemeSwitcher compact theme={theme} themes={themes} onThemeChange={onThemeChange} />
            <button className="btn" onClick={onLogout}>Выйти</button>
          </div>
        </header>
        <section className="workspace">{children}</section>
      </main>
    </div>
  );
}
