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
    const error = new Error(extractError(payload, `HTTP ${response.status}`));
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}

function json(method, body) {
  return { method, body: body === undefined ? undefined : JSON.stringify(body) };
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
    if (!tokens.access_token) throw new Error("Backend не вернул access_token");
    saveTokens(tokens);
    return tokens;
  },

  async logoutAdmin() {
    const tokens = loadTokens();
    try {
      if (tokens?.refresh_token) {
        await request(
          "/auth/admin/logout",
          json("POST", { refresh_token: tokens.refresh_token }),
          false,
        );
      }
    } finally {
      clearTokens();
    }
  },

  getPermissions() {
    return request("/admin/admins/permissions", { method: "GET" });
  },

  // Clients
  getClients() { return request("/admin/clients/", { method: "GET" }); },
  getClient(clientId) { return request(`/admin/clients/${clientId}`, { method: "GET" }); },
  createClient(payload) { return request("/admin/clients/", json("POST", payload)); },
  updateClientContact(clientId, payload) { return request(`/admin/clients/${clientId}/contact`, json("PUT", payload)); },
  enableClient(clientId) { return request(`/admin/clients/${clientId}/enable`, { method: "PATCH" }); },
  disableClient(clientId) { return request(`/admin/clients/${clientId}/disable`, { method: "PATCH" }); },
  deleteClient(clientId) { return request(`/admin/clients/${clientId}`, { method: "DELETE" }); },

  // Users
  getUsers(clientId = 0) {
    const query = clientId ? `?client_id=${encodeURIComponent(clientId)}` : "";
    return request(`/admin/users/${query}`, { method: "GET" });
  },
  getUser(employeeId) { return request(`/admin/users/${employeeId}`, { method: "GET" }); },
  createUser(payload) { return request("/admin/users/", json("POST", payload)); },
  updateUser(employeeId, payload) { return request(`/admin/users/${employeeId}`, json("PUT", payload)); },
  enableUser(employeeId) { return request(`/admin/users/${employeeId}/enable`, { method: "PATCH" }); },
  disableUser(employeeId) { return request(`/admin/users/${employeeId}/disable`, { method: "PATCH" }); },
  deleteUser(employeeId) { return request(`/admin/users/${employeeId}`, { method: "DELETE" }); },
  attachUserAccount(employeeId, payload) { return request(`/admin/users/${employeeId}/account`, json("POST", payload)); },
  detachUserAccount(employeeId) { return request(`/admin/users/${employeeId}/account`, { method: "DELETE" }); },
  changeUserPassword(employeeId, password) { return request(`/admin/users/${employeeId}/password`, json("PATCH", { password })); },
  grantUserRoles(employeeId, roles) { return request(`/admin/users/${employeeId}/roles`, json("POST", { roles })); },
  revokeUserRoles(employeeId, roles) { return request(`/admin/users/${employeeId}/roles`, json("DELETE", { roles })); },

  // Admins
  getAdmins() { return request("/admin/admins/", { method: "GET" }); },
  getAdmin(employeeId) { return request(`/admin/admins/${employeeId}`, { method: "GET" }); },
  createAdmin(payload) { return request("/admin/admins/", json("POST", payload)); },
  updateAdmin(employeeId, payload) { return request(`/admin/admins/${employeeId}`, json("PUT", payload)); },
  enableAdmin(employeeId) { return request(`/admin/admins/${employeeId}/enable`, { method: "PATCH" }); },
  disableAdmin(employeeId) { return request(`/admin/admins/${employeeId}/disable`, { method: "PATCH" }); },
  deleteAdmin(employeeId) { return request(`/admin/admins/${employeeId}`, { method: "DELETE" }); },
  attachAdminAccount(employeeId, payload) { return request(`/admin/admins/${employeeId}/account`, json("POST", payload)); },
  detachAdminAccount(employeeId) { return request(`/admin/admins/${employeeId}/account`, { method: "DELETE" }); },
  changeAdminPassword(employeeId, password) { return request(`/admin/admins/${employeeId}/password`, json("PATCH", { password })); },
  grantAdminRoles(employeeId, roles) { return request(`/admin/admins/${employeeId}/roles`, json("POST", { roles })); },
  revokeAdminRoles(employeeId, roles) { return request(`/admin/admins/${employeeId}/roles`, json("DELETE", { roles })); },
  changeAdminDepartment(employeeId, departmentId) {
    return request(`/admin/admins/${employeeId}/department`, json("PATCH", { department_id: departmentId }));
  },
  removeAdminDepartment(employeeId) { return request(`/admin/admins/${employeeId}/department`, { method: "DELETE" }); },

  // Departments
  getDepartments() { return request("/admin/departments/", { method: "GET" }); },
  getDepartment(departmentId) { return request(`/admin/departments/${departmentId}`, { method: "GET" }); },
  createDepartment(payload) { return request("/admin/departments/", json("POST", payload)); },
  updateDepartment(departmentId, payload) { return request(`/admin/departments/${departmentId}`, json("PUT", payload)); },
  enableDepartment(departmentId) { return request(`/admin/departments/${departmentId}/enable`, { method: "PATCH" }); },
  disableDepartment(departmentId) { return request(`/admin/departments/${departmentId}/disable`, { method: "PATCH" }); },
  deleteDepartment(departmentId) { return request(`/admin/departments/${departmentId}`, { method: "DELETE" }); },

  // Roles
  getAdminRoles() { return request("/admin/roles/admin", { method: "GET" }); },
  getUserRoles() { return request("/admin/roles/user", { method: "GET" }); },
  getAdminPermissionsCatalog() { return request("/admin/roles/admin/permissions", { method: "GET" }); },
  getUserPermissionsCatalog() { return request("/admin/roles/user/permissions", { method: "GET" }); },
  createAdminRole(payload) { return request("/admin/roles/admin", json("POST", payload)); },
  createUserRole(payload) { return request("/admin/roles/user", json("POST", payload)); },
  deleteAdminRole(roleId) { return request(`/admin/roles/admin/${roleId}`, { method: "DELETE" }); },
  deleteUserRole(roleId) { return request(`/admin/roles/user/${roleId}`, { method: "DELETE" }); },

  // Tickets — internal Ticket only. TicketUser endpoints are intentionally absent.
  async getTickets() {
    try {
      return await request("/admin/tickets/", { method: "GET" });
    } catch (error) {
      if (error.status !== 404) throw error;
      return request("/admin/tickets/all", { method: "GET" });
    }
  },
  getTicket(ticketId) { return request(`/admin/tickets/${ticketId}`, { method: "GET" }); },
  createTicket(payload) { return request("/admin/tickets/", json("POST", payload)); },
  updateTicketDetails(ticketId, payload) { return request(`/admin/tickets/${ticketId}/details`, json("PATCH", payload)); },
  changeTicketDepartment(ticketId, departmentId) { return request(`/admin/tickets/${ticketId}/department`, json("PATCH", { department_id: departmentId })); },
  acceptTicket(ticketId, payload = {}) { return request(`/admin/tickets/${ticketId}/accept`, json("PATCH", payload)); },
  rejectTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/reject`, json("PATCH", payload)); },
  deferTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/defer`, json("PATCH", payload)); },
  scheduleTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/schedule`, json("PATCH", payload)); },
  assignTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/executor`, json("PATCH", payload)); },
  readyToWorkTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/ready-to-work`, json("PATCH", payload)); },
  startWorkTicket(ticketId, payload = {}) { return request(`/admin/tickets/${ticketId}/at-work`, json("PATCH", payload)); },
  pauseTicket(ticketId, payload = {}) { return request(`/admin/tickets/${ticketId}/pause`, json("PATCH", payload)); },
  resumeTicket(ticketId, payload = {}) { return request(`/admin/tickets/${ticketId}/resume`, json("PATCH", payload)); },
  submitForReviewTicket(ticketId, payload = {}) { return request(`/admin/tickets/${ticketId}/submit-for-review`, json("PATCH", payload)); },
  recordCompletedTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/record-completed-work-for-review`, json("PATCH", payload)); },
  confirmExecutionTicket(ticketId, payload = {}) { return request(`/admin/tickets/${ticketId}/confirm-execution`, json("PATCH", payload)); },
  returnToWorkTicket(ticketId, payload = {}) { return request(`/admin/tickets/${ticketId}/return-to-work`, json("PATCH", payload)); },
  returnToAssignedTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/return-to-assigned`, json("PATCH", payload)); },
  returnToScheduledTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/return-to-scheduled`, json("PATCH", payload)); },
  returnToReadyToWorkTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/return-to-ready-to-work`, json("PATCH", payload)); },
  returnToDeferredTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/return-to-deferred`, json("PATCH", payload)); },
  cancelTicket(ticketId, payload) { return request(`/admin/tickets/${ticketId}/cancel`, json("PATCH", payload)); },
  addTicketComment(ticketId, comment) { return request(`/admin/tickets/${ticketId}/comments`, json("POST", { comment })); },
  deleteTicket(ticketId) { return request(`/admin/tickets/${ticketId}`, { method: "DELETE" }); },
};
