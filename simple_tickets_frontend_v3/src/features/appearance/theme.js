const colors = [
  "--bg", "--panel", "--panel-soft", "--text", "--muted", "--line", "--line-strong",
  "--accent", "--accent-dark", "--accent-hover", "--accent-soft", "--on-accent", "--focus", "--danger", "--danger-soft",
];
const sizes = { "--radius": [0, 24], "--radius-sm": [0, 24], "--control-height": [40, 56] };

export const themeProperties = Object.freeze([...colors, ...Object.keys(sizes), "--scheme"]);

export const classicTheme = Object.freeze({ id: "classic", label: "Классика", tokens: Object.freeze({}) });

function record(value) {
  return value !== null && typeof value === "object" && Object.getPrototypeOf(value) === Object.prototype;
}

function exactKeys(value, keys) {
  return record(value) && Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key));
}

function validToken(name, value) {
  if (typeof value !== "string") return false;
  if (colors.includes(name)) return /^#[0-9a-f]{6}$/i.test(value);
  if (name === "--scheme") return value === "light" || value === "dark";
  if (!Object.hasOwn(sizes, name) || !/^(?:0|[1-9]\d?)px$/.test(value)) return false;
  const [min, max] = sizes[name];
  const number = Number.parseInt(value, 10);
  return number >= min && number <= max;
}

export function validateThemeCatalog(value) {
  if (!exactKeys(value, ["version", "defaultTheme", "themes"]) || value.version !== 1 ||
      !Array.isArray(value.themes) || value.themes.length < 1 || value.themes.length > 32) return null;
  const ids = new Set();
  const themes = [];
  for (const theme of value.themes) {
    if (!exactKeys(theme, ["id", "label", "tokens"]) || typeof theme.id !== "string" ||
        !/^[a-z][a-z0-9-]{0,31}$/.test(theme.id) || ids.has(theme.id) ||
        typeof theme.label !== "string" || !theme.label.trim() || theme.label.length > 100 ||
        /\p{Cc}/u.test(theme.label) || !record(theme.tokens)) return null;
    const entries = Object.entries(theme.tokens);
    if (!entries.length || !entries.every(([name, token]) => validToken(name, token))) return null;
    ids.add(theme.id);
    themes.push(Object.freeze({ id: theme.id, label: theme.label.trim(), tokens: Object.freeze(Object.fromEntries(entries)) }));
  }
  return ids.has(value.defaultTheme) ? Object.freeze({ defaultTheme: value.defaultTheme, themes: Object.freeze(themes) }) : null;
}

export function selectTheme(catalog, saved) {
  return catalog?.themes.find(({ id }) => id === saved)
    ?? catalog?.themes.find(({ id }) => id === catalog.defaultTheme)
    ?? classicTheme;
}

export function applyTheme(root, theme) {
  root.dataset.theme = theme.id;
  for (const name of themeProperties) {
    if (Object.hasOwn(theme.tokens, name)) root.style.setProperty(name, theme.tokens[name]);
    else root.style.removeProperty(name);
  }
}
