import { clearTokens, loadTokens, saveTokens } from "./storage.js";

const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api";

function buildUrl(path) {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_PREFIX}${path}`;
}

function authHeader() {
  const tokens = loadTokens();
  if (!tokens?.access_token) return {};
  const tokenType = tokens.token_type || "bearer";
  return { Authorization: `${tokenType} ${tokens.access_token}` };
}

async function parseResponse(response) {
  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    const text = await response.text();
    return text || null;
  }
  return response.json();
}

function extractError(payload, fallback) {
  if (!payload) return fallback;
  if (typeof payload === "string") return payload;
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
  }
  if (typeof payload.detail === "string") return payload.detail;
  if (payload.message) return payload.message;
  return fallback;
}

async function refreshAccessToken() {
  const tokens = loadTokens();
  if (!tokens?.refresh_token) return false;

  const response = await fetch(buildUrl("/auth/admin/refresh"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: tokens.refresh_token }),
  });

  if (!response.ok) return false;
  const payload = await parseResponse(response);
  saveTokens({ ...tokens, ...payload });
  return true;
}

async function request(path, options = {}, allowRefresh = true) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...authHeader(),
    ...(options.headers || {}),
  };

  const response = await fetch(buildUrl(path), { ...options, headers });

  if (response.status === 401 && allowRefresh) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return request(path, options, false);
    clearTokens();
  }

  const payload = await parseResponse(response);
  if (!response.ok) {
    throw new Error(extractError(payload, `HTTP ${response.status}`));
  }
  return payload;
}

export const api = {
  async loginAdmin(username, password) {
    const form = new URLSearchParams();
    form.set("username", username);
    form.set("password", password);

    const response = await fetch(buildUrl("/auth/admin/login"), {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    const payload = await parseResponse(response);
    if (!response.ok) throw new Error(extractError(payload, "Ошибка авторизации"));

    const tokens = {
      access_token: payload?.access_token || payload?.accessToken || "",
      refresh_token: payload?.refresh_token || payload?.refreshToken || "",
      token_type: payload?.token_type || payload?.tokenType || "bearer",
    };

    if (!tokens.access_token) {
      throw new Error("Backend не вернул access_token");
    }

    saveTokens(tokens);
    return tokens;
  },

  async logoutAdmin() {
    try {
      await request("/auth/admin/logout", { method: "POST" }, false);
    } finally {
      clearTokens();
    }
  },

  getPermissions() {
    return request("/admin/admins/permissions", { method: "GET" });
  },

  getClients() {
    return request("/admin/clients/", { method: "GET" });
  },

  getClient(clientId) {
    return request(`/admin/clients/${clientId}`, { method: "GET" });
  },

  createClient(payload) {
    return request("/admin/clients/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateClientContact(clientId, payload) {
    return request(`/admin/clients/${clientId}/contact`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  enableClient(clientId) {
    return request(`/admin/clients/${clientId}/enable`, { method: "PATCH" });
  },

  disableClient(clientId) {
    return request(`/admin/clients/${clientId}/disable`, { method: "PATCH" });
  },

  deleteClient(clientId) {
    return request(`/admin/clients/${clientId}`, { method: "DELETE" });
  },

  getUsers(clientId = 0) {
    const query = clientId ? `?client_id=${encodeURIComponent(clientId)}` : "";
    return request(`/admin/users/${query}`, { method: "GET" });
  },

  getUser(employeeId) {
    return request(`/admin/users/${employeeId}`, { method: "GET" });
  },

  createUser(payload) {
    return request("/admin/users/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateUser(employeeId, payload) {
    return request(`/admin/users/${employeeId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  enableUser(employeeId) {
    return request(`/admin/users/${employeeId}/enable`, { method: "PATCH" });
  },

  disableUser(employeeId) {
    return request(`/admin/users/${employeeId}/disable`, { method: "PATCH" });
  },

  deleteUser(employeeId) {
    return request(`/admin/users/${employeeId}`, { method: "DELETE" });
  },

  attachUserAccount(employeeId, payload) {
    return request(`/admin/users/${employeeId}/account`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  detachUserAccount(employeeId) {
    return request(`/admin/users/${employeeId}/account`, { method: "DELETE" });
  },

  changeUserPassword(employeeId, password) {
    return request(`/admin/users/${employeeId}/password`, {
      method: "PATCH",
      body: JSON.stringify({ password }),
    });
  },
};
