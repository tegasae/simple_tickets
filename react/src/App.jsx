import { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import { normalizePermissions } from "./permissions.js";
import { clearTokens, loadTheme, loadTokens, saveTheme } from "./storage.js";
import LoginPage from "./components/LoginPage.jsx";
import Shell from "./components/Shell.jsx";
import ClientsPage from "./components/ClientsPage.jsx";
import Toast from "./components/Toast.jsx";

const THEMES = [
  { id: "onec", label: "1С 8.3" },
  { id: "classic", label: "Classic" },
  { id: "futuristic", label: "Futuristic" },
];

export default function App() {
  const [theme, setThemeState] = useState(loadTheme());
  const [tokens, setTokens] = useState(loadTokens());
  const [permissions, setPermissions] = useState([]);
  const [loadingSession, setLoadingSession] = useState(Boolean(tokens?.access_token));
  const [toast, setToast] = useState(null);

  const isAuthenticated = Boolean(tokens?.access_token);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    saveTheme(theme);
  }, [theme]);

  useEffect(() => {
    if (!isAuthenticated) {
      setLoadingSession(false);
      setPermissions([]);
      return;
    }

    let alive = true;
    setLoadingSession(true);
    api
      .getPermissions()
      .then((payload) => {
        if (alive) setPermissions(normalizePermissions(payload));
      })
      .catch((error) => {
        if (alive) {
          clearTokens();
          setTokens(null);
          showToast(error.message || "Сессия недействительна", "error");
        }
      })
      .finally(() => alive && setLoadingSession(false));

    return () => {
      alive = false;
    };
  }, [isAuthenticated]);

  function setTheme(themeId) {
    setThemeState(themeId);
  }

  function showToast(message, type = "info") {
    setToast({ message, type, id: Date.now() });
  }

  async function handleLogin(username, password) {
    const nextTokens = await api.loginAdmin(username, password);
    setTokens(nextTokens);
    showToast("Вход выполнен", "success");
  }

  async function handleLogout() {
    await api.logoutAdmin();
    setTokens(null);
    setPermissions([]);
    showToast("Вы вышли из системы", "info");
  }

  const themeOptions = useMemo(() => THEMES, []);

  if (!isAuthenticated) {
    return (
      <>
        <LoginPage
          theme={theme}
          themes={themeOptions}
          onThemeChange={setTheme}
          onLogin={handleLogin}
        />
        <Toast toast={toast} onClose={() => setToast(null)} />
      </>
    );
  }

  return (
    <>
      <Shell
        theme={theme}
        themes={themeOptions}
        onThemeChange={setTheme}
        onLogout={handleLogout}
        permissions={permissions}
        loadingSession={loadingSession}
      >
        <ClientsPage permissions={permissions} showToast={showToast} />
      </Shell>
      <Toast toast={toast} onClose={() => setToast(null)} />
    </>
  );
}
