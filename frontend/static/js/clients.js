const API = {
    permissions: "/frontend-api/permissions",
    clients: "/frontend-api/clients",
    users: "/frontend-api/users",
    logout: "/frontend-api/logout",
};

const SETTINGS_KEY = "simpleTickets.ui.settings";
const THEMES = ["onec", "classic", "futuristic"];

const DEFAULT_SETTINGS = {
    theme: "onec",
    clientTab: "main",
    clientsTable: {
        sortKey: "client_id",
        sortDir: "asc",
        page: 1,
        pageSize: 25,
        enabledFilter: "all",
        filters: {},
    },
    usersTable: {
        sortKey: "employee_id",
        sortDir: "asc",
        page: 1,
        pageSize: 10,
        enabledFilter: "all",
        filters: {},
    },
};

const state = {
    permissions: new Set(),
    clients: [],
    users: [],
    selectedClientId: null,
    openedClient: null,
    selectedUserId: null,
    openedUser: null,
    settings: loadSettings(),
};

function loadSettings() {
    try {
        const stored = JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {};
        return mergeSettings(DEFAULT_SETTINGS, stored);
    } catch (_) {
        return structuredClone(DEFAULT_SETTINGS);
    }
}

function mergeSettings(base, override) {
    const result = structuredClone(base);

    for (const [key, value] of Object.entries(override || {})) {
        if (
            value &&
            typeof value === "object" &&
            !Array.isArray(value) &&
            result[key] &&
            typeof result[key] === "object"
        ) {
            result[key] = mergeSettings(result[key], value);
        } else {
            result[key] = value;
        }
    }

    return result;
}

function saveSettings() {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(state.settings));
}

function applyTheme(theme) {
    const normalized = THEMES.includes(theme) ? theme : "onec";
    state.settings.theme = normalized;
    document.body.classList.remove("theme-onec", "theme-classic", "theme-futuristic");
    document.body.classList.add(`theme-${normalized}`);
    document.getElementById("themeSelect").value = normalized;
    saveSettings();
}

function setStatus(message) {
    document.getElementById("statusLine").textContent = message || "";
}

function setClientDialogStatus(message) {
    document.getElementById("clientDialogStatus").textContent = message || "";
}

function setUserStatus(message) {
    document.getElementById("userStatusLine").textContent = message || "";
}

async function requestJson(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
    });

    if (response.status === 401) {
        window.location.href = "/login";
        return null;
    }

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

function safeText(value) {
    if (value === null || value === undefined) {
        return "";
    }
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function norm(value) {
    if (value === null || value === undefined) {
        return "";
    }
    return String(value).toLowerCase();
}

function formatDate(value) {
    if (!value) {
        return "";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleString("ru-RU");
}

function can(permission) {
    return state.permissions.has(permission);
}

function canAny(...permissions) {
    return permissions.some((permission) => can(permission));
}

document.addEventListener("DOMContentLoaded", async () => {
    bindEvents();
    restoreSettingsToControls();
    applyTheme(state.settings.theme);

    await loadPermissions();
    applyPermissions();
    await loadClients();
});

function bindEvents() {
    document.getElementById("themeSelect").addEventListener("change", (event) => {
        applyTheme(event.target.value);
    });

    document.getElementById("btnLogout").addEventListener("click", logout);
    document.getElementById("btnAddClient").addEventListener("click", openCreateClientDialog);
    document.getElementById("btnRefresh").addEventListener("click", loadClients);
    document.getElementById("btnOpenSelected").addEventListener("click", openSelectedClient);
    document.getElementById("btnDeleteSelected").addEventListener("click", deleteSelectedClient);
    document.getElementById("btnResetClientFilters").addEventListener("click", resetClientFilters);

    document.getElementById("clientsEnabledFilter").addEventListener("change", (event) => {
        state.settings.clientsTable.enabledFilter = event.target.value;
        state.settings.clientsTable.page = 1;
        saveSettings();
        renderClientsTable();
    });

    document.getElementById("clientsPageSize").addEventListener("change", (event) => {
        state.settings.clientsTable.pageSize = Number(event.target.value);
        state.settings.clientsTable.page = 1;
        saveSettings();
        renderClientsTable();
    });

    document.querySelectorAll("[data-filter]").forEach((input) => {
        input.addEventListener("input", () => {
            state.settings.clientsTable.filters[input.dataset.filter] = input.value;
            state.settings.clientsTable.page = 1;
            saveSettings();
            renderClientsTable();
        });
    });

    document.querySelectorAll("[data-sort]").forEach((th) => {
        th.addEventListener("click", () => {
            changeSort(state.settings.clientsTable, th.dataset.sort);
            saveSettings();
            renderClientsTable();
        });
    });

    document.getElementById("clientsPrevPage").addEventListener("click", () => {
        state.settings.clientsTable.page = Math.max(1, state.settings.clientsTable.page - 1);
        saveSettings();
        renderClientsTable();
    });

    document.getElementById("clientsNextPage").addEventListener("click", () => {
        state.settings.clientsTable.page += 1;
        saveSettings();
        renderClientsTable();
    });

    document.getElementById("btnCloseDialog").addEventListener("click", closeClientDialog);
    document.getElementById("btnCancelDialog").addEventListener("click", closeClientDialog);
    document.getElementById("btnSaveClient").addEventListener("click", async () => saveClient(false));
    document.getElementById("btnSaveAndCloseClient").addEventListener("click", async () => saveClient(true));

    document.querySelectorAll("[data-client-tab]").forEach((button) => {
        button.addEventListener("click", () => switchClientTab(button.dataset.clientTab));
    });

    document.getElementById("btnAddUser").addEventListener("click", openCreateUserCard);
    document.getElementById("btnRefreshUsers").addEventListener("click", loadUsersForOpenedClient);
    document.getElementById("btnResetUserFilters").addEventListener("click", resetUserFilters);
    document.getElementById("btnSaveUser").addEventListener("click", saveUser);
    document.getElementById("btnDeleteUser").addEventListener("click", deleteSelectedUser);
    document.getElementById("btnClearUserCard").addEventListener("click", clearUserCard);
    document.getElementById("btnAttachAccount").addEventListener("click", attachAccount);
    document.getElementById("btnChangePassword").addEventListener("click", changePassword);
    document.getElementById("btnDetachAccount").addEventListener("click", detachAccount);

    document.getElementById("usersEnabledFilter").addEventListener("change", (event) => {
        state.settings.usersTable.enabledFilter = event.target.value;
        state.settings.usersTable.page = 1;
        saveSettings();
        renderUsersTable();
    });

    document.getElementById("usersPageSize").addEventListener("change", (event) => {
        state.settings.usersTable.pageSize = Number(event.target.value);
        state.settings.usersTable.page = 1;
        saveSettings();
        renderUsersTable();
    });

    document.querySelectorAll("[data-user-filter]").forEach((input) => {
        input.addEventListener("input", () => {
            state.settings.usersTable.filters[input.dataset.userFilter] = input.value;
            state.settings.usersTable.page = 1;
            saveSettings();
            renderUsersTable();
        });
    });

    document.querySelectorAll("[data-user-sort]").forEach((th) => {
        th.addEventListener("click", () => {
            changeSort(state.settings.usersTable, th.dataset.userSort);
            saveSettings();
            renderUsersTable();
        });
    });

    document.getElementById("usersPrevPage").addEventListener("click", () => {
        state.settings.usersTable.page = Math.max(1, state.settings.usersTable.page - 1);
        saveSettings();
        renderUsersTable();
    });

    document.getElementById("usersNextPage").addEventListener("click", () => {
        state.settings.usersTable.page += 1;
        saveSettings();
        renderUsersTable();
    });
}

function restoreSettingsToControls() {
    document.getElementById("clientsEnabledFilter").value = state.settings.clientsTable.enabledFilter;
    document.getElementById("clientsPageSize").value = String(state.settings.clientsTable.pageSize);
    for (const [key, value] of Object.entries(state.settings.clientsTable.filters || {})) {
        const input = document.querySelector(`[data-filter="${key}"]`);
        if (input) {
            input.value = value;
        }
    }

    document.getElementById("usersEnabledFilter").value = state.settings.usersTable.enabledFilter;
    document.getElementById("usersPageSize").value = String(state.settings.usersTable.pageSize);
    for (const [key, value] of Object.entries(state.settings.usersTable.filters || {})) {
        const input = document.querySelector(`[data-user-filter="${key}"]`);
        if (input) {
            input.value = value;
        }
    }
}

async function loadPermissions() {
    try {
        const data = await requestJson(API.permissions);
        state.permissions = new Set(data?.permissions || []);
    } catch (error) {
        console.error(error);
        setStatus(`Не удалось получить permissions: ${error.message}`);
    }
}

function applyPermissions() {
    const clientOperation = can("client.operation");
    const userOperation = can("user.operation");

    ["btnAddClient", "btnSaveClient", "btnSaveAndCloseClient", "btnDeleteSelected"].forEach((id) => {
        document.getElementById(id).disabled = !clientOperation;
    });

    [
        "btnAddUser",
        "btnSaveUser",
        "btnDeleteUser",
        "btnAttachAccount",
        "btnDetachAccount",
        "btnChangePassword",
    ].forEach((id) => {
        document.getElementById(id).disabled = !userOperation;
    });
}

async function logout() {
    try {
        await requestJson(API.logout, { method: "POST" });
    } finally {
        window.location.href = "/login";
    }
}

async function loadClients() {
    setStatus("Загрузка клиентов...");
    try {
        const data = await requestJson(API.clients);
        state.clients = Array.isArray(data) ? data : [];
        state.selectedClientId = null;
        renderClientsTable();
        setStatus(`Загружено клиентов: ${state.clients.length}`);
    } catch (error) {
        console.error(error);
        setStatus(`Ошибка загрузки клиентов: ${error.message}`);
    }
}

function renderClientsTable() {
    updateSortHeaders("[data-sort]", state.settings.clientsTable);
    const tbody = document.getElementById("clientsTableBody");
    tbody.innerHTML = "";

    const rows = applyTableTransform(
        state.clients,
        state.settings.clientsTable,
        ["client_id", "name", "email", "phone", "address", "description", "date_created", "created_by_admin"],
    );

    const pageData = paginate(rows, state.settings.clientsTable);
    state.settings.clientsTable.page = pageData.page;

    for (const client of pageData.items) {
        const row = document.createElement("tr");
        row.dataset.clientId = client.client_id;
        if (client.client_id === state.selectedClientId) {
            row.classList.add("selected");
        }

        row.innerHTML = `
            <td>${safeText(client.client_id)}</td>
            <td>${safeText(client.name)}</td>
            <td>${safeText(client.email)}</td>
            <td>${safeText(client.phone)}</td>
            <td>${safeText(client.address)}</td>
            <td title="${safeText(client.description)}">${safeText(clip(client.description, 60))}</td>
            <td>${client.enabled ? "Да" : "Нет"}</td>
            <td>${safeText(formatDate(client.date_created))}</td>
            <td>${safeText(client.created_by_admin)}</td>
        `;

        row.addEventListener("click", () => {
            state.selectedClientId = client.client_id;
            renderClientsTable();
        });

        row.addEventListener("dblclick", () => {
            state.selectedClientId = client.client_id;
            openClientDialog(client);
        });

        tbody.appendChild(row);
    }

    updatePager("clients", pageData, rows.length, state.clients.length);
    saveSettings();
}

function applyTableTransform(items, tableSettings, filterKeys) {
    const filters = tableSettings.filters || {};
    const enabledFilter = tableSettings.enabledFilter || "all";

    const filtered = items.filter((item) => {
        if (enabledFilter === "enabled" && item.enabled === false) {
            return false;
        }
        if (enabledFilter === "disabled" && item.enabled !== false) {
            return false;
        }

        return filterKeys.every((key) => {
            const expected = norm(filters[key] || "").trim();
            if (!expected) {
                return true;
            }
            const value = key.includes("date") ? formatDate(item[key]) : item[key];
            return norm(value).includes(expected);
        });
    });

    return filtered.sort((left, right) => compareByKey(left, right, tableSettings.sortKey, tableSettings.sortDir));
}

function compareByKey(left, right, key, direction) {
    const dir = direction === "desc" ? -1 : 1;
    const a = left?.[key];
    const b = right?.[key];

    if (typeof a === "number" && typeof b === "number") {
        return (a - b) * dir;
    }

    if (typeof a === "boolean" && typeof b === "boolean") {
        return (Number(a) - Number(b)) * dir;
    }

    return String(a ?? "").localeCompare(String(b ?? ""), "ru", { numeric: true }) * dir;
}

function changeSort(tableSettings, key) {
    if (tableSettings.sortKey === key) {
        tableSettings.sortDir = tableSettings.sortDir === "asc" ? "desc" : "asc";
    } else {
        tableSettings.sortKey = key;
        tableSettings.sortDir = "asc";
    }
}

function updateSortHeaders(selector, tableSettings) {
    document.querySelectorAll(selector).forEach((th) => {
        th.classList.remove("th-sort", "asc", "desc");
        const key = th.dataset.sort || th.dataset.userSort;
        if (key === tableSettings.sortKey) {
            th.classList.add("th-sort", tableSettings.sortDir);
        }
    });
}

function paginate(items, tableSettings) {
    const pageSize = Number(tableSettings.pageSize) || 25;
    const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
    const page = Math.min(Math.max(1, Number(tableSettings.page) || 1), totalPages);
    const start = (page - 1) * pageSize;
    return {
        page,
        pageSize,
        totalPages,
        items: items.slice(start, start + pageSize),
    };
}

function updatePager(prefix, pageData, filteredCount, totalCount) {
    document.getElementById(`${prefix}PageInfo`).textContent = `Страница ${pageData.page} из ${pageData.totalPages}`;
    document.getElementById(`${prefix}PrevPage`).disabled = pageData.page <= 1;
    document.getElementById(`${prefix}NextPage`).disabled = pageData.page >= pageData.totalPages;
    const totalInfo = document.getElementById(`${prefix}TotalInfo`);
    if (totalInfo) {
        totalInfo.textContent = `Показано по фильтру: ${filteredCount}; всего: ${totalCount}`;
    }
}

function resetClientFilters() {
    state.settings.clientsTable.filters = {};
    state.settings.clientsTable.enabledFilter = "all";
    state.settings.clientsTable.page = 1;
    document.querySelectorAll("[data-filter]").forEach((input) => {
        input.value = "";
    });
    document.getElementById("clientsEnabledFilter").value = "all";
    saveSettings();
    renderClientsTable();
}

function clip(value, length) {
    const text = String(value || "");
    if (text.length <= length) {
        return text;
    }
    return `${text.slice(0, length)}…`;
}

function openSelectedClient() {
    if (state.selectedClientId === null) {
        setStatus("Клиент не выбран");
        return;
    }
    const client = state.clients.find((item) => item.client_id === state.selectedClientId);
    if (!client) {
        setStatus("Клиент не найден");
        return;
    }
    openClientDialog(client);
}

function openCreateClientDialog() {
    openClientDialog({
        client_id: 0,
        name: "",
        email: "",
        phone: "",
        address: "",
        description: "",
        enabled: true,
        date_created: "",
        created_by_admin: "",
    });
}

function openClientDialog(client) {
    const isExisting = Number(client.client_id || 0) > 0;
    state.openedClient = client;
    state.selectedClientId = client.client_id || null;
    state.users = [];
    state.selectedUserId = null;
    state.openedUser = null;

    document.getElementById("clientDialogTitle").textContent = isExisting ? `Клиент ${client.client_id}` : "Новый клиент";
    document.getElementById("clientDialogSubtitle").textContent = isExisting ? safeText(client.name || "") : "Создание клиента";

    document.getElementById("clientId").value = client.client_id || 0;
    document.getElementById("clientOriginalEnabled").value = client.enabled === false ? "false" : "true";
    document.getElementById("clientIdReadonly").value = client.client_id || "новый";
    document.getElementById("clientDateCreated").value = formatDate(client.date_created);
    document.getElementById("clientCreatedByAdmin").value = client.created_by_admin || "";
    document.getElementById("clientName").value = client.name || "";
    document.getElementById("clientEmail").value = client.email || "";
    document.getElementById("clientPhone").value = client.phone || "";
    document.getElementById("clientAddress").value = client.address || "";
    document.getElementById("clientDescription").value = client.description || "";
    document.getElementById("clientEnabled").checked = client.enabled !== false;

    clearUserCard();
    switchClientTab(state.settings.clientTab || "main", { skipLoad: !isExisting });
    document.getElementById("clientDialogBackdrop").classList.remove("hidden");
    setClientDialogStatus("");
    setUserStatus("");
}

function closeClientDialog() {
    document.getElementById("clientDialogBackdrop").classList.add("hidden");
    state.openedClient = null;
    state.users = [];
    state.openedUser = null;
}

function switchClientTab(tab, options = {}) {
    const normalized = tab === "users" ? "users" : "main";
    state.settings.clientTab = normalized;
    saveSettings();

    document.querySelectorAll("[data-client-tab]").forEach((button) => {
        button.classList.toggle("active", button.dataset.clientTab === normalized);
    });
    document.getElementById("clientTabMain").classList.toggle("active", normalized === "main");
    document.getElementById("clientTabUsers").classList.toggle("active", normalized === "users");

    if (normalized === "users" && !options.skipLoad) {
        loadUsersForOpenedClient();
    }
}

function collectClientPayload({ forCreate }) {
    const payload = {
        name: document.getElementById("clientName").value.trim(),
        email: document.getElementById("clientEmail").value.trim(),
        address: document.getElementById("clientAddress").value.trim(),
        phone: document.getElementById("clientPhone").value.trim(),
        description: document.getElementById("clientDescription").value.trim(),
    };

    if (forCreate && !payload.name) {
        throw new Error("Имя клиента обязательно");
    }

    return payload;
}

async function saveClient(closeAfterSave) {
    if (!can("client.operation")) {
        setClientDialogStatus("Недостаточно прав для изменения клиента");
        return;
    }

    const clientId = Number(document.getElementById("clientId").value || 0);
    const isExisting = clientId > 0;

    try {
        setClientDialogStatus("Сохранение клиента...");
        const payload = collectClientPayload({ forCreate: !isExisting });
        let saved;

        if (isExisting) {
            saved = await requestJson(`${API.clients}/${clientId}/contact`, {
                method: "PUT",
                body: JSON.stringify(payload),
            });

            const originalEnabled = document.getElementById("clientOriginalEnabled").value === "true";
            const nextEnabled = document.getElementById("clientEnabled").checked;
            if (originalEnabled !== nextEnabled) {
                saved = await requestJson(`${API.clients}/${clientId}/enabled`, {
                    method: "PATCH",
                    body: JSON.stringify({ enabled: nextEnabled }),
                });
            }
        } else {
            saved = await requestJson(API.clients, {
                method: "POST",
                body: JSON.stringify(payload),
            });
        }

        upsertById(state.clients, saved, "client_id");
        state.selectedClientId = saved.client_id;
        state.openedClient = saved;
        openClientDialog(saved);
        renderClientsTable();
        setClientDialogStatus("Клиент сохранён");

        if (closeAfterSave) {
            closeClientDialog();
        }
    } catch (error) {
        console.error(error);
        setClientDialogStatus(`Ошибка сохранения: ${error.message}`);
    }
}

async function deleteSelectedClient() {
    if (!can("client.operation")) {
        setStatus("Недостаточно прав для удаления клиента");
        return;
    }
    if (state.selectedClientId === null) {
        setStatus("Клиент не выбран");
        return;
    }
    if (!confirm(`Удалить клиента ${state.selectedClientId}?`)) {
        return;
    }

    try {
        await requestJson(`${API.clients}/${state.selectedClientId}`, { method: "DELETE" });
        state.clients = state.clients.filter((client) => client.client_id !== state.selectedClientId);
        state.selectedClientId = null;
        renderClientsTable();
        setStatus("Клиент удалён");
    } catch (error) {
        console.error(error);
        setStatus(`Ошибка удаления клиента: ${error.message}`);
    }
}

async function loadUsersForOpenedClient() {
    const clientId = Number(document.getElementById("clientId").value || 0);
    if (clientId <= 0) {
        state.users = [];
        renderUsersTable();
        setUserStatus("Сначала сохраните клиента");
        return;
    }

    if (!canAny("user.view", "user.operation", "user.view.all", "user.operation.all")) {
        setUserStatus("Недостаточно прав для просмотра пользователей");
        return;
    }

    try {
        setUserStatus("Загрузка пользователей...");
        const data = await requestJson(`${API.users}?client_id=${clientId}`);
        state.users = Array.isArray(data) ? data : [];
        state.selectedUserId = null;
        clearUserCard();
        renderUsersTable();
        setUserStatus(`Загружено пользователей: ${state.users.length}`);
    } catch (error) {
        console.error(error);
        setUserStatus(`Ошибка загрузки пользователей: ${error.message}`);
    }
}

function renderUsersTable() {
    updateSortHeaders("[data-user-sort]", state.settings.usersTable);
    const tbody = document.getElementById("usersTableBody");
    tbody.innerHTML = "";

    const rows = applyTableTransform(
        state.users,
        state.settings.usersTable,
        ["employee_id", "first_name", "last_name", "email", "phone", "login"],
    );

    const pageData = paginate(rows, state.settings.usersTable);
    state.settings.usersTable.page = pageData.page;

    for (const user of pageData.items) {
        const row = document.createElement("tr");
        row.dataset.employeeId = user.employee_id;
        if (user.employee_id === state.selectedUserId) {
            row.classList.add("selected");
        }
        row.innerHTML = `
            <td>${safeText(user.employee_id)}</td>
            <td>${safeText(user.first_name)}</td>
            <td>${safeText(user.last_name)}</td>
            <td>${safeText(user.email)}</td>
            <td>${safeText(user.phone)}</td>
            <td>${safeText(user.login)}</td>
            <td>${user.enabled ? "Да" : "Нет"}</td>
        `;
        row.addEventListener("click", () => {
            state.selectedUserId = user.employee_id;
            openUserCard(user);
            renderUsersTable();
        });
        tbody.appendChild(row);
    }

    updatePager("users", pageData, rows.length, state.users.length);
    saveSettings();
}

function resetUserFilters() {
    state.settings.usersTable.filters = {};
    state.settings.usersTable.enabledFilter = "all";
    state.settings.usersTable.page = 1;
    document.querySelectorAll("[data-user-filter]").forEach((input) => {
        input.value = "";
    });
    document.getElementById("usersEnabledFilter").value = "all";
    saveSettings();
    renderUsersTable();
}

function openCreateUserCard() {
    const clientId = Number(document.getElementById("clientId").value || 0);
    if (clientId <= 0) {
        setUserStatus("Сначала сохраните клиента");
        return;
    }
    openUserCard({
        employee_id: 0,
        client_id: clientId,
        first_name: "",
        last_name: "",
        email: "",
        phone: "",
        login: "",
        enabled: true,
        enabled_login: false,
        roles: [],
    });
}

function openUserCard(user) {
    const isExisting = Number(user.employee_id || 0) > 0;
    state.openedUser = user;
    state.selectedUserId = isExisting ? user.employee_id : null;

    document.getElementById("userCardTitle").textContent = isExisting ? `Пользователь ${user.employee_id}` : "Новый пользователь";
    document.getElementById("userEmployeeId").value = user.employee_id || 0;
    document.getElementById("userClientId").value = user.client_id || document.getElementById("clientId").value || 0;
    document.getElementById("userOriginalEnabled").value = user.enabled === false ? "false" : "true";
    document.getElementById("userEmployeeIdReadonly").value = isExisting ? user.employee_id : "новый";
    document.getElementById("userEnabled").checked = user.enabled !== false;
    document.getElementById("userFirstName").value = user.first_name || "";
    document.getElementById("userLastName").value = user.last_name || "";
    document.getElementById("userEmail").value = user.email || "";
    document.getElementById("userPhone").value = user.phone || "";
    document.getElementById("userLogin").value = user.login || "";
    document.getElementById("userLoginEnabled").checked = user.enabled_login === true;
    document.getElementById("userPassword").value = "";
    document.getElementById("userPasswordRepeat").value = "";

    document.getElementById("btnChangePassword").disabled = !can("user.operation") || !isExisting;
    document.getElementById("btnDetachAccount").disabled = !can("user.operation") || !isExisting || !user.login;
    document.getElementById("btnAttachAccount").disabled = !can("user.operation") || !isExisting;
    setUserStatus("");
}

function clearUserCard() {
    state.openedUser = null;
    state.selectedUserId = null;
    document.getElementById("userCardTitle").textContent = "Пользователь";
    document.getElementById("userEmployeeId").value = 0;
    document.getElementById("userClientId").value = document.getElementById("clientId")?.value || 0;
    document.getElementById("userOriginalEnabled").value = "true";
    document.getElementById("userEmployeeIdReadonly").value = "";
    document.getElementById("userEnabled").checked = true;
    document.getElementById("userFirstName").value = "";
    document.getElementById("userLastName").value = "";
    document.getElementById("userEmail").value = "";
    document.getElementById("userPhone").value = "";
    document.getElementById("userLogin").value = "";
    document.getElementById("userLoginEnabled").checked = true;
    document.getElementById("userPassword").value = "";
    document.getElementById("userPasswordRepeat").value = "";
}

function collectUserPayload({ forCreate }) {
    const firstName = document.getElementById("userFirstName").value.trim();
    const login = document.getElementById("userLogin").value.trim();
    const password = document.getElementById("userPassword").value;
    const passwordRepeat = document.getElementById("userPasswordRepeat").value;

    if (!firstName) {
        throw new Error("Имя пользователя обязательно");
    }
    if (password || passwordRepeat) {
        if (password !== passwordRepeat) {
            throw new Error("Пароли не совпадают");
        }
    }

    if (forCreate) {
        return {
            client_id: Number(document.getElementById("userClientId").value || 0),
            first_name: firstName,
            last_name: document.getElementById("userLastName").value.trim(),
            email: document.getElementById("userEmail").value.trim(),
            phone: document.getElementById("userPhone").value.trim(),
            login,
            password,
            enable: document.getElementById("userEnabled").checked,
            enable_account: document.getElementById("userLoginEnabled").checked,
            roles: [],
        };
    }

    return {
        first_name: firstName,
        last_name: document.getElementById("userLastName").value.trim(),
        email: document.getElementById("userEmail").value.trim(),
        phone: document.getElementById("userPhone").value.trim(),
    };
}

async function saveUser() {
    if (!can("user.operation")) {
        setUserStatus("Недостаточно прав для изменения пользователя");
        return;
    }

    const employeeId = Number(document.getElementById("userEmployeeId").value || 0);
    const isExisting = employeeId > 0;

    try {
        setUserStatus("Сохранение пользователя...");
        let saved;

        if (isExisting) {
            saved = await requestJson(`${API.users}/${employeeId}`, {
                method: "PUT",
                body: JSON.stringify(collectUserPayload({ forCreate: false })),
            });

            const originalEnabled = document.getElementById("userOriginalEnabled").value === "true";
            const nextEnabled = document.getElementById("userEnabled").checked;
            if (originalEnabled !== nextEnabled) {
                saved = await requestJson(`${API.users}/${employeeId}/enabled`, {
                    method: "PATCH",
                    body: JSON.stringify({ enabled: nextEnabled }),
                });
            }
        } else {
            saved = await requestJson(API.users, {
                method: "POST",
                body: JSON.stringify(collectUserPayload({ forCreate: true })),
            });
        }

        upsertById(state.users, saved, "employee_id");
        state.selectedUserId = saved.employee_id;
        openUserCard(saved);
        renderUsersTable();
        setUserStatus("Пользователь сохранён");
    } catch (error) {
        console.error(error);
        setUserStatus(`Ошибка сохранения пользователя: ${error.message}`);
    }
}

async function deleteSelectedUser() {
    if (!can("user.operation")) {
        setUserStatus("Недостаточно прав для удаления пользователя");
        return;
    }
    const employeeId = Number(document.getElementById("userEmployeeId").value || 0);
    if (employeeId <= 0) {
        setUserStatus("Пользователь не выбран");
        return;
    }
    if (!confirm(`Удалить пользователя ${employeeId}?`)) {
        return;
    }
    try {
        await requestJson(`${API.users}/${employeeId}`, { method: "DELETE" });
        state.users = state.users.filter((user) => user.employee_id !== employeeId);
        clearUserCard();
        renderUsersTable();
        setUserStatus("Пользователь удалён");
    } catch (error) {
        console.error(error);
        setUserStatus(`Ошибка удаления пользователя: ${error.message}`);
    }
}

async function attachAccount() {
    if (!can("user.operation")) {
        setUserStatus("Недостаточно прав для аккаунта");
        return;
    }
    const employeeId = Number(document.getElementById("userEmployeeId").value || 0);
    if (employeeId <= 0) {
        setUserStatus("Сначала сохраните пользователя");
        return;
    }

    const login = document.getElementById("userLogin").value.trim();
    const password = document.getElementById("userPassword").value;
    const passwordRepeat = document.getElementById("userPasswordRepeat").value;

    if (!login || !password) {
        setUserStatus("Для привязки аккаунта нужны логин и пароль");
        return;
    }
    if (password !== passwordRepeat) {
        setUserStatus("Пароли не совпадают");
        return;
    }

    try {
        const saved = await requestJson(`${API.users}/${employeeId}/account`, {
            method: "POST",
            body: JSON.stringify({
                login,
                password,
                enable_account: document.getElementById("userLoginEnabled").checked,
            }),
        });
        upsertById(state.users, saved, "employee_id");
        openUserCard(saved);
        renderUsersTable();
        setUserStatus("Аккаунт привязан");
    } catch (error) {
        console.error(error);
        setUserStatus(`Ошибка аккаунта: ${error.message}`);
    }
}

async function changePassword() {
    if (!can("user.operation")) {
        setUserStatus("Недостаточно прав для смены пароля");
        return;
    }
    const employeeId = Number(document.getElementById("userEmployeeId").value || 0);
    const password = document.getElementById("userPassword").value;
    const passwordRepeat = document.getElementById("userPasswordRepeat").value;

    if (employeeId <= 0) {
        setUserStatus("Пользователь не выбран");
        return;
    }
    if (!password || password !== passwordRepeat) {
        setUserStatus("Введите одинаковые пароли");
        return;
    }

    try {
        const saved = await requestJson(`${API.users}/${employeeId}/password`, {
            method: "PATCH",
            body: JSON.stringify({ password }),
        });
        upsertById(state.users, saved, "employee_id");
        openUserCard(saved);
        renderUsersTable();
        setUserStatus("Пароль изменён");
    } catch (error) {
        console.error(error);
        setUserStatus(`Ошибка смены пароля: ${error.message}`);
    }
}

async function detachAccount() {
    if (!can("user.operation")) {
        setUserStatus("Недостаточно прав для аккаунта");
        return;
    }
    const employeeId = Number(document.getElementById("userEmployeeId").value || 0);
    if (employeeId <= 0) {
        setUserStatus("Пользователь не выбран");
        return;
    }
    if (!confirm(`Отвязать аккаунт пользователя ${employeeId}?`)) {
        return;
    }

    try {
        const saved = await requestJson(`${API.users}/${employeeId}/account`, { method: "DELETE" });
        upsertById(state.users, saved, "employee_id");
        openUserCard(saved);
        renderUsersTable();
        setUserStatus("Аккаунт отвязан");
    } catch (error) {
        console.error(error);
        setUserStatus(`Ошибка отвязки аккаунта: ${error.message}`);
    }
}

function upsertById(collection, item, key) {
    if (!item) {
        return;
    }
    const index = collection.findIndex((existing) => existing[key] === item[key]);
    if (index >= 0) {
        collection[index] = item;
    } else {
        collection.push(item);
    }
}
