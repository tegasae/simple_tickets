import { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import {
  clearClientId,
  clearTokens,
  decodeAccessToken,
  loadClientId,
  loadTheme,
  loadTokens,
  saveClientId,
  saveTheme,
} from "./storage.js";
import LoginPage from "./components/LoginPage.jsx";
import UserShell from "./components/UserShell.jsx";
import TicketsPage from "./components/TicketsPage.jsx";
import Toast from "./components/Toast.jsx";

const THEMES = [
  { id: "onec", label: "1С 8.3" },
  { id: "classic", label: "Классика" },
  { id: "futuristic", label: "Футуризм" },
  { id: "barbie", label: "Barbie" },
];

export default function App() {
  const [theme, setTheme] = useState(loadTheme());
  const [tokens, setTokens] = useState(loadTokens());
  const [clientId, setClientId] = useState(loadClientId());
  const [toast, setToast] = useState(null);

  const isAuthenticated = Boolean(tokens?.access_token && clientId > 0);
  const tokenPayload = useMemo(() => decodeAccessToken(), [tokens]);
  const userId = tokenPayload?.subject_type === "user" ? Number(tokenPayload.sub) || 0 : 0;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    saveTheme(theme);
  }, [theme]);

  function showToast(message, type = "info") {
    setToast({ id: Date.now(), message, type });
  }

  async function login(username, password, nextClientId) {
    const nextTokens = await api.loginUser(username, password);
    saveClientId(nextClientId);
    setClientId(nextClientId);
    setTokens(nextTokens);
    showToast("Вход выполнен", "success");
  }

  async function logout() {
    try {
      await api.logoutUser();
    } catch (error) {
      showToast(error.message || "Logout завершён локально", "error");
    } finally {
      clearTokens();
      clearClientId();
      setTokens(null);
      setClientId(0);
    }
  }

  function invalidateSession() {
    clearTokens();
    setTokens(null);
  }

  if (!isAuthenticated) {
    return (
      <>
        <LoginPage
          theme={theme}
          themes={THEMES}
          onThemeChange={setTheme}
          initialClientId={clientId || loadClientId()}
          onLogin={login}
        />
        <Toast toast={toast} onClose={() => setToast(null)} />
      </>
    );
  }

  return (
    <>
      <UserShell
        clientId={clientId}
        userId={userId}
        theme={theme}
        themes={THEMES}
        onThemeChange={setTheme}
        onLogout={logout}
      >
        <TicketsPage clientId={clientId} showToast={showToast} onSessionInvalid={invalidateSession} />
      </UserShell>
      <Toast toast={toast} onClose={() => setToast(null)} />
    </>
  );
}
