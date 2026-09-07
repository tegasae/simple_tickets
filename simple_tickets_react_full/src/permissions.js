export function normalizePermissions(payload) {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload.map(String);
  if (Array.isArray(payload.permissions)) return payload.permissions.map(String);
  return [];
}

export function hasPermission(permissions, permission) {
  return permissions.includes(permission);
}

export const can = {
  clientsView: (p) => hasPermission(p, "client.view") || hasPermission(p, "client.operation"),
  clientsOperate: (p) => hasPermission(p, "client.operation"),
  usersView: (p) => hasPermission(p, "user.view") || hasPermission(p, "user.operation"),
  usersOperate: (p) => hasPermission(p, "user.operation"),
  adminsView: (p) => hasPermission(p, "admin.view") || hasPermission(p, "admin.operation"),
  adminsOperate: (p) => hasPermission(p, "admin.operation"),
  ticketsView: (p) => hasPermission(p, "ticket.view") || hasPermission(p, "ticket.operation"),
  ticketsOperate: (p) => hasPermission(p, "ticket.operation"),
  ticketsAccept: (p) => hasPermission(p, "ticket.accepted"),
  // Current backend DepartmentApplicationService and RoleService both use admin.operation.
  departmentsView: (p) => hasPermission(p, "admin.operation"),
  departmentsOperate: (p) => hasPermission(p, "admin.operation"),
  rolesView: (p) => hasPermission(p, "admin.operation"),
  rolesOperate: (p) => hasPermission(p, "admin.operation"),
  // Assignment/revocation of roles on employees is a separate permission family.
  rolesAssign: (p) => hasPermission(p, "role.assign") || hasPermission(p, "role_user.assign"),
  rolesRevoke: (p) => hasPermission(p, "role.revoke"),
};

export function canAccessPage(page, permissions) {
  switch (page) {
    case "clients": return can.clientsView(permissions);
    case "users": return can.usersView(permissions);
    case "admins": return can.adminsView(permissions);
    case "tickets": return can.ticketsView(permissions);
    case "departments": return can.departmentsView(permissions);
    case "roles": return can.rolesView(permissions);
    default: return false;
  }
}

export const PAGE_ORDER = ["clients", "users", "admins", "tickets", "departments", "roles"];

// Compatibility for components from the first React prototype.
export const canClientOperate = can.clientsOperate;
export const canClientView = can.clientsView;
export const canUserOperate = can.usersOperate;
export const canUserView = can.usersView;
