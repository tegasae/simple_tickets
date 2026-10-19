import ThemeSwitcher from "./ThemeSwitcher.jsx";

export default function Shell({ children, theme, themes, onThemeChange, onLogout, permissions, loadingSession }) {
  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="side-logo">
          <div className="brand-mark small">ST</div>
          <div>
            <strong>Simple Tickets</strong>
            <span>Admin</span>
          </div>
        </div>
        <nav>
          <button className="nav-item active">Клиенты</button>
          <button className="nav-item disabled">Заявки</button>
          <button className="nav-item disabled">Справочники</button>
        </nav>
        <div className="side-permissions">
          <span>Права</span>
          <strong>{loadingSession ? "..." : permissions.length}</strong>
        </div>
      </aside>

      <div className="main-area">
        <header className="top-bar">
          <div>
            <h2>Клиенты и пользователи</h2>
            <p>React frontend · локальные настройки таблиц и тем</p>
          </div>
          <div className="top-actions">
            <ThemeSwitcher theme={theme} themes={themes} onThemeChange={onThemeChange} />
            <button className="btn" onClick={onLogout}>Выйти</button>
          </div>
        </header>
        <section className="workspace">{children}</section>
      </div>
    </div>
  );
}
