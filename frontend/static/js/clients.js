const CLIENTS_API = "/frontend-api/clients";
const PERMISSIONS_API = "/frontend-api/permissions";

let clients = [];
let selectedClientId = null;
let permissions = new Set();


document.addEventListener("DOMContentLoaded", async () => {
    bindEvents();

    await loadPermissions();
    applyPermissions();

    await loadClients();
});


function bindEvents() {
    document
        .getElementById("btnAddClient")
        .addEventListener("click", openCreateDialog);

    document
        .getElementById("btnRefresh")
        .addEventListener("click", loadClients);

    document
        .getElementById("btnOpenSelected")
        .addEventListener("click", openSelectedClient);

    document
        .getElementById("btnDeleteSelected")
        .addEventListener("click", deleteSelectedClient);

    document
        .getElementById("btnLogout")
        .addEventListener("click", logout);

    document
        .getElementById("searchInput")
        .addEventListener("input", renderClientsTable);

    document
        .getElementById("btnCloseDialog")
        .addEventListener("click", closeDialog);

    document
        .getElementById("btnCancelDialog")
        .addEventListener("click", closeDialog);

    document
        .getElementById("btnSaveClient")
        .addEventListener("click", async () => {
            await saveClient(false);
        });

    document
        .getElementById("btnSaveAndCloseClient")
        .addEventListener("click", async () => {
            await saveClient(true);
        });
}


async function loadPermissions() {
    try {
        const data = await requestJson(PERMISSIONS_API);
        permissions = new Set(data.permissions || []);
    } catch (error) {
        console.error(error);
        setStatus("Не удалось получить permissions");
    }
}


function applyPermissions() {
    const canOperateClients = can("client.operation");

    document.getElementById("btnAddClient").disabled = !canOperateClients;
    document.getElementById("btnSaveClient").disabled = !canOperateClients;
    document.getElementById("btnSaveAndCloseClient").disabled = !canOperateClients;
    document.getElementById("btnDeleteSelected").disabled = !canOperateClients;
}


function can(permission) {
    return permissions.has(permission);
}


async function loadClients() {
    setStatus("Загрузка клиентов...");

    try {
        clients = await requestJson(CLIENTS_API);

        if (!Array.isArray(clients)) {
            clients = [];
        }

        selectedClientId = null;
        renderClientsTable();
        setStatus(`Загружено клиентов: ${clients.length}`);
    } catch (error) {
        console.error(error);
        setStatus(`Ошибка загрузки клиентов: ${error.message}`);
    }
}


function renderClientsTable() {
    const tbody = document.getElementById("clientsTableBody");
    const searchText = document
        .getElementById("searchInput")
        .value
        .trim()
        .toLowerCase();

    tbody.innerHTML = "";

    const visibleClients = clients.filter((client) => {
        if (!searchText) {
            return true;
        }

        return [
            client.client_id,
            client.name,
            client.email,
            client.phone,
            client.address,
        ]
            .filter((value) => value !== null && value !== undefined)
            .join(" ")
            .toLowerCase()
            .includes(searchText);
    });

    for (const client of visibleClients) {
        const row = document.createElement("tr");
        row.dataset.clientId = client.client_id;

        if (client.client_id === selectedClientId) {
            row.classList.add("selected");
        }

        row.innerHTML = `
            <td class="col-id">${safeText(client.client_id)}</td>
            <td>${safeText(client.name)}</td>
            <td>${safeText(client.email)}</td>
            <td>${safeText(client.phone)}</td>
            <td>${safeText(client.address)}</td>
            <td class="col-enabled">${client.enabled ? "Да" : "Нет"}</td>
            <td class="col-date">${formatDate(client.date_created)}</td>
            <td class="col-id">${safeText(client.created_by_admin)}</td>
        `;

        row.addEventListener("click", () => {
            selectedClientId = client.client_id;
            renderClientsTable();
        });

        row.addEventListener("dblclick", () => {
            selectedClientId = client.client_id;
            openClientDialog(client);
        });

        tbody.appendChild(row);
    }
}


function openSelectedClient() {
    if (selectedClientId === null) {
        setStatus("Клиент не выбран");
        return;
    }

    const client = clients.find(
        (item) => item.client_id === selectedClientId,
    );

    if (!client) {
        setStatus("Клиент не найден");
        return;
    }

    openClientDialog(client);
}


function openCreateDialog() {
    openClientDialog({
        client_id: 0,
        name: "",
        email: "",
        address: "",
        phone: "",
        enabled: true,
    });
}


function openClientDialog(client) {
    const isExisting = Number(client.client_id || 0) > 0;

    document.getElementById("clientDialogTitle").textContent = isExisting
        ? `Клиент ${client.client_id}`
        : "Новый клиент";

    document.getElementById("clientId").value = client.client_id || 0;
    document.getElementById("clientOriginalEnabled").value = client.enabled ? "true" : "false";

    const nameInput = document.getElementById("clientName");
    const nameHint = document.getElementById("clientNameHint");

    nameInput.value = client.name || "";
    nameInput.disabled = isExisting;
    nameHint.classList.toggle("hidden", !isExisting);

    document.getElementById("clientEmail").value = client.email || "";
    document.getElementById("clientPhone").value = client.phone || "";
    document.getElementById("clientAddress").value = client.address || "";
    document.getElementById("clientEnabled").checked = client.enabled !== false;

    document
        .getElementById("clientDialogBackdrop")
        .classList
        .remove("hidden");
}


function closeDialog() {
    document
        .getElementById("clientDialogBackdrop")
        .classList
        .add("hidden");
}


async function saveClient(closeAfterSave) {
    if (!can("client.operation")) {
        setStatus("Нет права client.operation");
        return;
    }

    const clientId = Number(document.getElementById("clientId").value || 0);
    const enabled = document.getElementById("clientEnabled").checked;
    const originalEnabled = document.getElementById("clientOriginalEnabled").value === "true";

    try {
        let savedClient;

        if (clientId > 0) {
            savedClient = await requestJson(
                `${CLIENTS_API}/${clientId}/contact`,
                {
                    method: "PUT",
                    body: JSON.stringify(getClientContactFormData()),
                },
            );

            if (enabled !== originalEnabled) {
                savedClient = await requestJson(
                    `${CLIENTS_API}/${clientId}/enabled`,
                    {
                        method: "PATCH",
                        body: JSON.stringify({
                            enabled,
                        }),
                    },
                );
            }
        } else {
            const payload = getClientCreateFormData();

            if (!payload.name) {
                setStatus("Наименование клиента обязательно");
                document.getElementById("clientName").focus();
                return;
            }

            savedClient = await requestJson(
                CLIENTS_API,
                {
                    method: "POST",
                    body: JSON.stringify(payload),
                },
            );

            if (!enabled) {
                savedClient = await requestJson(
                    `${CLIENTS_API}/${savedClient.client_id}/enabled`,
                    {
                        method: "PATCH",
                        body: JSON.stringify({
                            enabled: false,
                        }),
                    },
                );
            }
        }

        upsertClientInList(savedClient);
        renderClientsTable();
        setStatus("Клиент записан");

        if (closeAfterSave) {
            closeDialog();
        } else {
            openClientDialog(savedClient);
        }
    } catch (error) {
        console.error(error);
        setStatus(`Ошибка записи клиента: ${error.message}`);
    }
}


async function deleteSelectedClient() {
    if (!can("client.operation")) {
        setStatus("Нет права client.operation");
        return;
    }

    if (selectedClientId === null) {
        setStatus("Клиент не выбран");
        return;
    }

    const client = clients.find((item) => item.client_id === selectedClientId);

    if (!client) {
        setStatus("Клиент не найден");
        return;
    }

    if (!confirm(`Удалить клиента "${client.name}"?`)) {
        return;
    }

    try {
        await requestJson(
            `${CLIENTS_API}/${selectedClientId}`,
            {
                method: "DELETE",
            },
        );

        clients = clients.filter((item) => item.client_id !== selectedClientId);
        selectedClientId = null;
        renderClientsTable();
        setStatus("Клиент удалён");
    } catch (error) {
        console.error(error);
        setStatus(`Ошибка удаления клиента: ${error.message}`);
    }
}


function getClientCreateFormData() {
    return {
        name: document.getElementById("clientName").value.trim(),
        email: document.getElementById("clientEmail").value.trim(),
        address: document.getElementById("clientAddress").value.trim(),
        phone: document.getElementById("clientPhone").value.trim(),
    };
}


function getClientContactFormData() {
    return {
        email: document.getElementById("clientEmail").value.trim(),
        address: document.getElementById("clientAddress").value.trim(),
        phone: document.getElementById("clientPhone").value.trim(),
    };
}


function upsertClientInList(client) {
    const index = clients.findIndex(
        (item) => item.client_id === client.client_id,
    );

    if (index >= 0) {
        clients[index] = client;
    } else {
        clients.unshift(client);
    }

    selectedClientId = client.client_id;
}


async function logout() {
    try {
        await fetch("/frontend-api/logout", {
            method: "POST",
            credentials: "same-origin",
        });
    } finally {
        window.location.href = "/login";
    }
}


async function requestJson(url, options = {}) {
    const response = await fetch(
        url,
        {
            credentials: "same-origin",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
            ...options,
        },
    );

    if (response.status === 401) {
        window.location.href = "/login";
        throw new Error("Не авторизован");
    }

    if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(detail);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}


async function readErrorDetail(response) {
    try {
        const data = await response.json();

        if (typeof data.detail === "string") {
            return data.detail;
        }

        if (data.detail) {
            return JSON.stringify(data.detail);
        }

        return JSON.stringify(data);
    } catch (_error) {
        return await response.text();
    }
}


function setStatus(text) {
    document.getElementById("statusText").textContent = text;
}


function formatDate(value) {
    if (!value) {
        return "";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return safeText(value);
    }

    return date.toLocaleString("ru-RU");
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
