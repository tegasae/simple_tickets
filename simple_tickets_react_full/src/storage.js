const PREFIX = "simpleTickets.react.";

export function loadSetting(key, fallback) {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    return raw === null ? fallback : JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export function saveSetting(key, value) {
  localStorage.setItem(PREFIX + key, JSON.stringify(value));
}

export function removeSetting(key) {
  localStorage.removeItem(PREFIX + key);
}

export function loadTheme() {
  return loadSetting("theme", "onec");
}

export function saveTheme(theme) {
  saveSetting("theme", theme);
}

export function loadTokens() {
  return loadSetting("tokens", null);
}

export function saveTokens(tokens) {
  saveSetting("tokens", tokens);
}

export function clearTokens() {
  removeSetting("tokens");
}
