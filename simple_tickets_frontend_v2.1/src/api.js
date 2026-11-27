import {
  clearSession,
  loadAdminUsername,
  loadTokens,
  saveAdminUsername,
  saveTokens,
} from "./storage.js";

const API_PREFIX = import.meta.env.VITE_API_PREFIX ?? "/api";
let refreshPromise = null;

function decodeJwtPayload(token) {
  try {
    const part = String(token || "").split(".")[1];
    if (!part) return {};
    const normalized = part.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized + "=".repeat((4 - normalized.length % 4) % 4);
    return JSON.parse(atob(padded));
  } catch {
    return {};
  }
}

function extractCurrentEmployeeId() {
  const tokens = loadTokens() || {};
  const jwt = decodeJwtPayload(tokens.access_token);
  const candidates = [
    tokens.employee_id, tokens.admin_id, tokens.actor_admin_id,
    jwt.employee_id, jwt.admin_id, jwt.actor_admin_id, jwt.user_id, jwt.sub,
  ];
  for (const candidate of candidates) {
    const value = Number(candidate);
    if (Number.isInteger(value) && value > 0) return value;
  }
  return 0;
}

function buildUrl(path) {
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_PREFIX}${path}`;
}

function authorizationHeader() {
  const tokens = loadTokens();
  if (!tokens?.access_token) return {};
  return { Authorization: `${tokens.token_type || "bearer"} ${tokens.access_token}` };
}

async function parseResponse(response) {
  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return response.json();
  const text = await response.text();
  return text || null;
}

function extractError(payload, fallback) {
  if (!payload) return fallback;
  if (typeof payload === "string") return payload;
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((item) => item?.msg || JSON.stringify(item)).join("; ");
  }
  if (payload.message) return payload.message;
  return fallback;
}

function authExpired() {
  clearSession();
  window.dispatchEvent(new CustomEvent("simple-tickets:auth-expired"));
}

async function performRefresh() {
  const tokens = loadTokens();
  if (!tokens?.refresh_token) return false;

  const response = await fetch(buildUrl("/auth/admin/refresh"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: tokens.refresh_token }),
  });

  if (!response.ok) return false;
  const payload = await parseResponse(response);
  if (!payload?.access_token && !payload?.accessToken) return false;

  saveTokens({
    ...tokens,
    ...payload,
    access_token: payload.access_token || payload.accessToken,
    refresh_token: payload.refresh_token || payload.refreshToken || tokens.refresh_token,
    token_type: payload.token_type || payload.tokenType || tokens.token_type || "bearer",
  });
  return true;
}

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function request(path, options = {}, { allowRefresh = true } = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...authorizationHeader(),
    ...(options.headers || {}),
  };

  const response = await fetch(buildUrl(path), { ...options, headers });

  if (response.status === 401 && allowRefresh) {
    let refreshed = false;
    try {
      refreshed = await refreshAccessToken();
    } catch {
      refreshed = false;
    }
    if (refreshed) return request(path, options, { allowRefresh: false });
    authExpired();
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
  return {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  };
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
      ...payload,
      access_token: payload?.access_token || payload?.accessToken || "",
      refresh_token: payload?.refresh_token || payload?.refreshToken || "",
      token_type: payload?.token_type || payload?.tokenType || "bearer",
    };
    if (!tokens.access_token) throw new Error("Backend не вернул access_token");
    saveTokens(tokens);
    saveAdminUsername(username);
    return tokens;
  },

  async logoutAdmin() {
    const tokens = loadTokens();
    try {
      if (tokens?.refresh_token) {
        await request(
          "/auth/admin/logout",
          json("POST", { refresh_token: tokens.refresh_token, username: loadAdminUsername() }),
          { allowRefresh: false },
        );
      }
    } finally {
      clearSession();
    }
  },

  getPermissions() { return request("/admin/admins/permissions", { method: "GET" }); },
  getCurrentAdmin() {
    const employeeId = extractCurrentEmployeeId();
    if (employeeId > 0) return Promise.resolve({ employee_id: employeeId });
    const username = loadAdminUsername();
    if (!username) return Promise.reject(new Error("Не удалось определить текущего сотрудника"));
    return request(`/admin/admins/by-login/${encodeURIComponent(username)}`, { method: "GET" });
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
  getUserByLogin(login) { return request(`/admin/users/by-login/${encodeURIComponent(login)}`, { method: "GET" }); },
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
  getAdminByLogin(login) { return request(`/admin/admins/by-login/${encodeURIComponent(login)}`, { method: "GET" }); },
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
  changeAdminDepartment(employeeId, departmentId) { return request(`/admin/admins/${employeeId}/department`, json("PATCH", { department_id: departmentId })); },
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
  getAdminPermissionsCatalog() { return request("/admin/roles/admin/permissions", { method: "GET" }); },
  getUserPermissionsCatalog() { return request("/admin/roles/user/permissions", { method: "GET" }); },
  getAdminRoles() { return request("/admin/roles/admin", { method: "GET" }); },
  getAdminRole(roleId) { return request(`/admin/roles/admin/${roleId}`, { method: "GET" }); },
  createAdminRole(payload) { return request("/admin/roles/admin", json("POST", payload)); },
  deleteAdminRole(roleId) { return request(`/admin/roles/admin/${roleId}`, { method: "DELETE" }); },
  getUserRoles() { return request("/admin/roles/user", { method: "GET" }); },
  getUserRole(roleId) { return request(`/admin/roles/user/${roleId}`, { method: "GET" }); },
  createUserRole(payload) { return request("/admin/roles/user", json("POST", payload)); },
  deleteUserRole(roleId) { return request(`/admin/roles/user/${roleId}`, { method: "DELETE" }); },

  // Tickets
  getTickets() { return request("/admin/tickets/", { method: "GET" }); },
  getOpenTickets() { return request("/admin/tickets/open", { method: "GET" }); },
  getClosedTickets() { return request("/admin/tickets/closed", { method: "GET" }); },
  getTicketsByClient(clientId) { return request(`/admin/tickets/by-client/${clientId}`, { method: "GET" }); },
  getTicketsByUser(userId) { return request(`/admin/tickets/by-user/${userId}`, { method: "GET" }); },
  getTicketsByContactUser(userId) { return request(`/admin/tickets/by-contact-user/${userId}`, { method: "GET" }); },
  getTicketsByDepartment(departmentId) { return request(`/admin/tickets/by-department/${departmentId}`, { method: "GET" }); },
  getTicketsByExecutor(executorId) { return request(`/admin/tickets/by-executor/${executorId}`, { method: "GET" }); },
  getTicket(ticketId) { return request(`/admin/tickets/${ticketId}`, { method: "GET" }); },
  createTicket(payload) { return request("/admin/tickets/", json("POST", payload)); },
  addTicketComment(ticketId, comment) { return request(`/admin/tickets/${ticketId}/comments`, json("POST", { comment })); },
  updateTicketDescription(ticketId, description) { return request(`/admin/tickets/${ticketId}/description`, json("PATCH", { description })); },
  changeTicketContactUser(ticketId, contactUserId) { return request(`/admin/tickets/${ticketId}/contact-user`, json("PATCH", { contact_user_id: contactUserId })); },
  changeTicketDepartment(ticketId, departmentId) { return request(`/admin/tickets/${ticketId}/department`, json("PATCH", { department_id: departmentId })); },
  setTicketRemoteWorkRecommended(ticketId, value) { return request(`/admin/tickets/${ticketId}/remote-work-recommended`, json("PATCH", { remote_work_recommended: Boolean(value) })); },
  changeTicketUrgency(ticketId, urgency) { return request(`/admin/tickets/${ticketId}/urgency`, json("PATCH", { urgency })); },
  scheduleTicket(ticketId, plannedAt) { return request(`/admin/tickets/${ticketId}/schedule`, json("PATCH", { planned_at: plannedAt })); },
  clearTicketSchedule(ticketId) { return request(`/admin/tickets/${ticketId}/schedule`, { method: "DELETE" }); },
  acceptTicket(ticketId, comment = "") { return request(`/admin/tickets/${ticketId}/accept`, json("PATCH", { comment })); },
  rejectTicket(ticketId, comment) { return request(`/admin/tickets/${ticketId}/reject`, json("PATCH", { comment })); },
  deferTicket(ticketId, comment) { return request(`/admin/tickets/${ticketId}/defer`, json("PATCH", { comment })); },
  assignTicket(ticketId, executorId, comment = "") { return request(`/admin/tickets/${ticketId}/executor`, json("PATCH", { executor_id: executorId, comment })); },
  startTicketWork(ticketId, workIsRemote = false, comment = "") { return request(`/admin/tickets/${ticketId}/start-work`, json("PATCH", { work_is_remote: Boolean(workIsRemote), comment })); },
  startRemoteTicketWork(ticketId, comment = "") { return request(`/admin/tickets/${ticketId}/start-remote-work`, json("PATCH", { comment })); },
  pauseTicketWork(ticketId, comment = "") { return request(`/admin/tickets/${ticketId}/pause-work`, json("PATCH", { comment })); },
  resumeTicketWork(ticketId, workIsRemote = false, comment = "") { return request(`/admin/tickets/${ticketId}/resume-work`, json("PATCH", { work_is_remote: Boolean(workIsRemote), comment })); },
  finishTicketWork(ticketId, comment = "") { return request(`/admin/tickets/${ticketId}/finish-work`, json("PATCH", { comment })); },
  completeTicketWorkRetroactively(ticketId, payload) { return request(`/admin/tickets/${ticketId}/complete-work-retroactively`, json("PATCH", payload)); },
  executeTicket(ticketId, comment = "") { return request(`/admin/tickets/${ticketId}/execute`, json("PATCH", { comment })); },
  cancelTicket(ticketId, comment) { return request(`/admin/tickets/${ticketId}/cancel`, json("PATCH", { comment })); },
};
