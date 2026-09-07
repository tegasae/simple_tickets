import { clearTokens, loadTokens, saveTokens } from "./storage.js";

const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api";

function buildUrl(path) {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_PREFIX}${path}`;
}

function authHeader() {
  const tokens = loadTokens();
  if (!tokens?.access_token) return {};
  return { Authorization: `${tokens.token_type || "bearer"} ${tokens.access_token}` };
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

  const response = await fetch(buildUrl("/auth/user/refresh"), {
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
    const error = new Error(extractError(payload, `HTTP ${response.status}`));
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}

function json(method, body) {
  return { method, body: JSON.stringify(body ?? {}) };
}

export const api = {
  async loginUser(username, password) {
    const form = new URLSearchParams();
    form.set("username", username);
    form.set("password", password);

    const response = await fetch(buildUrl("/auth/user/login"), {
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
      expires_in: payload?.expires_in,
    };
    if (!tokens.access_token) throw new Error("Backend не вернул access_token");
    saveTokens(tokens);
    return tokens;
  },

  async logoutUser() {
    const tokens = loadTokens();
    try {
      if (tokens?.refresh_token) {
        await request(
          "/auth/user/logout",
          json("POST", { refresh_token: tokens.refresh_token }),
          false,
        );
      }
    } finally {
      clearTokens();
    }
  },

  getMyTickets(clientId) {
    return request(`/user/tickets/?client_id=${encodeURIComponent(clientId)}`, { method: "GET" });
  },

  getTicket(ticketUserId) {
    return request(`/user/tickets/${ticketUserId}`, { method: "GET" });
  },

  createTicket(payload) {
    return request("/user/tickets/", json("POST", payload));
  },

  cancelTicket(ticketUserId, comment = "") {
    return request(`/user/tickets/${ticketUserId}/cancel`, json("PATCH", { comment }));
  },

  confirmExecution(ticketUserId, comment = "") {
    return request(`/user/tickets/${ticketUserId}/confirm-execution`, json("PATCH", { comment }));
  },
};
