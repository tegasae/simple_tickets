const TOKENS_KEY = "simpleTickets.user.tokens";
const THEME_KEY = "simpleTickets.theme";
const CLIENT_KEY = "simpleTickets.user.clientId";

export function loadTokens() {
  try {
    return JSON.parse(localStorage.getItem(TOKENS_KEY) || "null");
  } catch {
    return null;
  }
}

export function saveTokens(tokens) {
  localStorage.setItem(TOKENS_KEY, JSON.stringify(tokens));
}

export function clearTokens() {
  localStorage.removeItem(TOKENS_KEY);
}

export function loadTheme() {
  return localStorage.getItem(THEME_KEY) || "classic";
}

export function saveTheme(theme) {
  localStorage.setItem(THEME_KEY, theme);
}

export function loadClientId() {
  const value = Number(localStorage.getItem(CLIENT_KEY) || 0);
  return Number.isInteger(value) && value > 0 ? value : 0;
}

export function saveClientId(clientId) {
  const value = Number(clientId);
  if (Number.isInteger(value) && value > 0) {
    localStorage.setItem(CLIENT_KEY, String(value));
  }
}

export function clearClientId() {
  localStorage.removeItem(CLIENT_KEY);
}

export function decodeAccessToken() {
  const token = loadTokens()?.access_token;
  if (!token) return null;
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    return JSON.parse(decodeURIComponent(escape(atob(padded))));
  } catch {
    return null;
  }
}
