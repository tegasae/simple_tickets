import { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import { canAccessPage, normalizePermissions, PAGE_ORDER } from "./permissions.js";
import { clearTokens, loadSetting, loadTheme, loadTokens, saveSetting, saveTheme } from "./storage.js";
import LoginPage from "./components/LoginPage.jsx";
import Shell from "./components/Shell.jsx";
import ClientsPage from "./components/ClientsPage.jsx";
import UsersPage from "./components/UsersPage.jsx";
import AdminsPage from "./components/AdminsPage.jsx";
import TicketsPage from "./components/TicketsPage.jsx";
import DepartmentsPage from "./components/DepartmentsPage.jsx";
import RolesPage from "./components/RolesPage.jsx";
import Toast from "./components/Toast.jsx";

const THEMES = [
  { id: "onec", label: "1С 8.3" },
  { id: "classic", label: "Классика" },
  { id: "futuristic", label: "Футуризм" },
  { id: "barbie", label: "Barbie" },
];

export default function App() {
  const [theme, setThemeState] = useState(loadTheme());
  const [tokens, setTokens] = useState(loadTokens());
  const [permissions, setPermissions] = useState([]);
  const [loadingSession, setLoadingSession] = useState(Boolean(tokens?.access_token));
  const [toast, setToast] = useState(null);
  const [activePage, setActivePage] = useState(() => loadSetting("nav.activePage", "clients"));

  const isAuthenticated = Boolean(tokens?.access_token);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    saveTheme(theme);
  }, [theme]);

  useEffect(() => saveSetting("nav.activePage", activePage), [activePage]);

  useEffect(() => {
    if (!isAuthenticated || loadingSession || !permissions.length) return;
    if (canAccessPage(activePage, permissions)) return;
    const firstAllowed = PAGE_ORDER.find((pageId) => canAccessPage(pageId, permissions));
    if (firstAllowed) setActivePage(firstAllowed);
  }, [isAuthenticated, loadingSession, permissions, activePage]);

  useEffect(() => {
    if (!isAuthenticated) {
      setLoadingSession(false);
      setPermissions([]);
      return;
    }
    let alive = true;
    setLoadingSession(true);
    api.getPermissions()
      .then((payload) => alive && setPermissions(normalizePermissions(payload)))
      .catch((error) => {
        if (!alive) return;
        setPermissions([]);
        if (error?.status === 401) {
          clearTokens();
          setTokens(null);
          showToast(error.message || "Сессия недействительна", "error");
          return;
        }
        showToast(
          error.message || "Не удалось загрузить permissions текущего Admin",
          "error",
        );
      })
      .finally(() => alive && setLoadingSession(false));
    return () => { alive = false; };
  }, [isAuthenticated]);

  function showToast(message, type = "info") {
    setToast({ message, type, id: Date.now() });
  }

  async function handleLogin(username, password) {
    const nextTokens = await api.loginAdmin(username, password);
    setTokens(nextTokens);
    showToast("Вход выполнен", "success");
  }

  async function handleLogout() {
    try {
      await api.logoutAdmin();
    } catch (error) {
      showToast(error.message || "Logout завершён локально", "error");
    } finally {
      setTokens(null);
      setPermissions([]);
    }
  }

  const page = useMemo(() => {
    const props = { permissions, showToast };
    switch (activePage) {
      case "users": return <UsersPage {...props} />;
      case "admins": return <AdminsPage {...props} />;
      case "tickets": return <TicketsPage {...props} />;
      case "departments": return <DepartmentsPage {...props} />;
      case "roles": return <RolesPage {...props} />;
      default: return <ClientsPage {...props} />;
    }
  }, [activePage, permissions]);

  const themeOptions = useMemo(() => THEMES, []);

  if (!isAuthenticated) {
    return (
      <>
        <LoginPage theme={theme} themes={themeOptions} onThemeChange={setThemeState} onLogin={handleLogin} />
        <Toast toast={toast} onClose={() => setToast(null)} />
      </>
    );
  }

  return (
    <>
      <Shell
        activePage={activePage}
        onNavigate={setActivePage}
        theme={theme}
        themes={themeOptions}
        onThemeChange={setThemeState}
        onLogout={handleLogout}
        permissions={permissions}
        loadingSession={loadingSession}
      >
        {page}
      </Shell>
      <Toast toast={toast} onClose={() => setToast(null)} />
    </>
  );
}
