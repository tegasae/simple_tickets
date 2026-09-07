import ThemeSwitcher from "./ThemeSwitcher.jsx";
import { canAccessPage } from "../permissions.js";

const NAV = [
  ["clients", "Клиенты"],
  ["users", "Пользователи"],
  ["admins", "Admin"],
  ["tickets", "Заявки"],
  ["departments", "Отделы"],
  ["roles", "Роли"],
];

export default function Shell({ children, activePage, onNavigate, theme, themes, onThemeChange, onLogout, permissions, loadingSession }) {
  const visibleNav = NAV.filter(([id]) => canAccessPage(id, permissions));

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="side-logo">
          <div className="brand-mark small">ST</div>
          <div>
            <strong>Simple Tickets</strong>
            <span>Admin workspace</span>
          </div>
        </div>
        <nav>
          {visibleNav.map(([id, label]) => (
            <button
              key={id}
              className={activePage === id ? "nav-item active" : "nav-item"}
              onClick={() => onNavigate(id)}
            >
              {label}
            </button>
          ))}
          {!loadingSession && !visibleNav.length && (
            <div className="muted">Нет доступных разделов</div>
          )}
        </nav>
        <div className="side-permissions">
          <span>Права</span>
          <strong>{loadingSession ? "..." : permissions.length}</strong>
        </div>
      </aside>

      <div className="main-area">
        <header className="top-bar">
          <div>
            <h2>Simple Tickets</h2>
            <p>Клиенты · пользователи · admin · Ticket · отделы · роли</p>
          </div>
          <div className="top-actions">
            <ThemeSwitcher theme={theme} themes={themes} onThemeChange={onThemeChange} />
            <button className="btn" onClick={onLogout}>Выйти</button>
          </div>
        </header>
        <main className="workspace">{children}</main>
      </div>
    </div>
  );
}
