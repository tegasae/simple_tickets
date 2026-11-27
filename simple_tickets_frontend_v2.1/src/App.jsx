import { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import { canAccessPage, normalizePermissions, PAGE_ORDER } from "./permissions.js";
import { clearSession, loadSetting, loadTheme, loadTokens, saveSetting, saveTheme } from "./storage.js";
import LoginPage from "./components/LoginPage.jsx";
import Shell from "./components/Shell.jsx";
import ClientsPage from "./components/ClientsPage.jsx";
import UsersPage from "./components/UsersPage.jsx";
import AdminsPage from "./components/AdminsPage.jsx";
import TicketsPage from "./components/TicketsPage.jsx";
import DepartmentsPage from "./components/DepartmentsPage.jsx";
import RolesPage from "./components/RolesPage.jsx";
import Toast from "./components/Toast.jsx";
import { ReferenceDataProvider } from "./referenceData.jsx";

const THEMES = [
  { id: "onec", label: "1С 8.3" },
  { id: "classic", label: "Классика" },
  { id: "futuristic", label: "Футуризм" },
  { id: "barbie", label: "Barbie" },
];

export default function App() {
  const [theme, setTheme] = useState(loadTheme());
  const [tokens, setTokens] = useState(loadTokens());
  const [permissions, setPermissions] = useState([]);
  const [loadingSession, setLoadingSession] = useState(Boolean(tokens?.access_token));
  const [toast, setToast] = useState(null);
  const [activePage, setActivePage] = useState(() => loadSetting("nav.activePage", "tickets"));
  const [pageContext, setPageContext] = useState({});

  const isAuthenticated = Boolean(tokens?.access_token);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    saveTheme(theme);
  }, [theme]);

  useEffect(() => saveSetting("nav.activePage", activePage), [activePage]);

  useEffect(() => {
    const handler = () => {
      setTokens(null);
      setPermissions([]);
      setLoadingSession(false);
      showToast("Сессия истекла. Выполните вход снова.", "error");
    };
    window.addEventListener("simple-tickets:auth-expired", handler);
    return () => window.removeEventListener("simple-tickets:auth-expired", handler);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      setPermissions([]);
      setLoadingSession(false);
      return;
    }
    let alive = true;
    setLoadingSession(true);
    api.getPermissions()
      .then((payload) => alive && setPermissions(normalizePermissions(payload)))
      .catch((error) => {
        if (!alive) return;
        if (error?.status === 401) return;
        setPermissions([]);
        showToast(error.message || "Не удалось загрузить permissions", "error");
      })
      .finally(() => alive && setLoadingSession(false));
    return () => { alive = false; };
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated || loadingSession || !permissions.length) return;
    if (canAccessPage(activePage, permissions)) return;
    const first = PAGE_ORDER.find((page) => canAccessPage(page, permissions));
    if (first) setActivePage(first);
  }, [isAuthenticated, loadingSession, permissions, activePage]);

  function showToast(message, type = "info") {
    setToast({ id: Date.now(), message, type });
  }

  function navigate(page, context = {}) {
    setPageContext(context);
    setActivePage(page);
  }

  async function handleLogin(username, password) {
    const next = await api.loginAdmin(username, password);
    setTokens(next);
    showToast("Вход выполнен", "success");
  }

  async function handleLogout() {
    try {
      await api.logoutAdmin();
    } catch (error) {
      showToast(error.message || "Logout завершён локально", "error");
    } finally {
      clearSession();
      setTokens(null);
      setPermissions([]);
    }
  }

  const page = useMemo(() => {
    const common = { permissions, showToast, onNavigate: navigate, pageContext };
    switch (activePage) {
      case "clients": return <ClientsPage {...common} />;
      case "users": return <UsersPage {...common} />;
      case "admins": return <AdminsPage {...common} />;
      case "departments": return <DepartmentsPage {...common} />;
      case "roles": return <RolesPage {...common} />;
      default: return <TicketsPage {...common} />;
    }
  }, [activePage, permissions, pageContext]);

  if (!isAuthenticated) {
    return <>
      <LoginPage theme={theme} themes={THEMES} onThemeChange={setTheme} onLogin={handleLogin} />
      <Toast toast={toast} onClose={() => setToast(null)} />
    </>;
  }

  return <ReferenceDataProvider>
    <Shell
      activePage={activePage}
      onNavigate={(page) => navigate(page)}
      theme={theme}
      themes={THEMES}
      onThemeChange={setTheme}
      onLogout={handleLogout}
      permissions={permissions}
      loadingSession={loadingSession}
    >
      {page}
    </Shell>
    <Toast toast={toast} onClose={() => setToast(null)} />
  </ReferenceDataProvider>;
}
