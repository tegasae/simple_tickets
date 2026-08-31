const LOGIN_API = "/frontend-api/login";
const SETTINGS_KEY = "simpleTickets.ui.settings";

function loadSettings() {
    try {
        return JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {};
    } catch (_) {
        return {};
    }
}

function saveSettings(settings) {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

function applyTheme(theme) {
    const normalized = ["onec", "classic", "futuristic"].includes(theme) ? theme : "onec";
    document.body.classList.remove("theme-onec", "theme-classic", "theme-futuristic");
    document.body.classList.add(`theme-${normalized}`);
    document.getElementById("themeSelect").value = normalized;
}

async function requestJson(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
    });

    if (!response.ok) {
        let detail = await response.text();
        try {
            const data = JSON.parse(detail);
            detail = data.detail ? JSON.stringify(data.detail) : JSON.stringify(data);
        } catch (_) {}
        throw new Error(detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

document.addEventListener("DOMContentLoaded", () => {
    const settings = loadSettings();
    applyTheme(settings.theme || "onec");

    const themeSelect = document.getElementById("themeSelect");
    themeSelect.addEventListener("change", () => {
        const next = themeSelect.value;
        const updated = { ...loadSettings(), theme: next };
        saveSettings(updated);
        applyTheme(next);
    });

    document.getElementById("loginForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        const status = document.getElementById("loginStatus");
        status.textContent = "Вход...";

        try {
            await requestJson(LOGIN_API, {
                method: "POST",
                body: JSON.stringify({
                    username: document.getElementById("username").value.trim(),
                    password: document.getElementById("password").value,
                }),
            });
            window.location.href = "/clients";
        } catch (error) {
            status.textContent = `Ошибка входа: ${error.message}`;
        }
    });
});
