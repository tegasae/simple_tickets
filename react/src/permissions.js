export function normalizePermissions(payload) {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload.map(String);
  if (Array.isArray(payload.permissions)) return payload.permissions.map(String);
  return [];
}

export function hasPermission(permissions, permission) {
  return permissions.includes(permission);
}

export function canClientOperate(permissions) {
  return hasPermission(permissions, "client.operation");
}

export function canClientView(permissions) {
  return hasPermission(permissions, "client.view") || canClientOperate(permissions);
}

export function canUserOperate(permissions) {
  return hasPermission(permissions, "user.operation");
}

export function canUserView(permissions) {
  return hasPermission(permissions, "user.view") || canUserOperate(permissions);
}
