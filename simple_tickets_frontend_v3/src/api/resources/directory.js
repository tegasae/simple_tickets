import { ApiError } from '../transport.js';

const EMPLOYEE_FIELDS = ['first_name', 'last_name', 'email', 'phone'];
const PROFILE_FIELDS = {
  clients: ['name', 'email', 'phone', 'address', 'description'],
  users: EMPLOYEE_FIELDS,
  admins: [...EMPLOYEE_FIELDS, 'job_title', 'department_id'],
  departments: ['name'],
};

const RESOURCES = {
  clients: { path: '/admin/clients', id: 'client_id', updateSuffix: '/contact', check: isClient },
  users: { path: '/admin/users', id: 'employee_id', check: isUser },
  admins: { path: '/admin/admins', id: 'employee_id', check: isAdmin },
  departments: { path: '/admin/departments', id: 'department_id', check: isDepartment },
  adminRoles: { path: '/admin/roles/admin', id: 'role_id', roles: true, check: isRole },
  userRoles: { path: '/admin/roles/user', id: 'role_id', roles: true, check: isRole },
};

const EMPLOYEES = ['users', 'admins'];
const ACTIVATABLE = ['clients', 'users', 'admins', 'departments'];
const ACTIONS = {
  enable: { method: 'PATCH', suffix: 'enable', resources: ACTIVATABLE },
  disable: { method: 'PATCH', suffix: 'disable', resources: ACTIVATABLE },
  attachAccount: { method: 'POST', suffix: 'account', resources: EMPLOYEES, body: accountBody },
  detachAccount: { method: 'DELETE', suffix: 'account', resources: EMPLOYEES },
  enableAccount: { method: 'PATCH', suffix: 'account/enable', resources: EMPLOYEES },
  disableAccount: { method: 'PATCH', suffix: 'account/disable', resources: EMPLOYEES },
  changePassword: { method: 'PATCH', suffix: 'password', resources: EMPLOYEES, body: passwordBody },
  changeDepartment: { method: 'PATCH', suffix: 'department', resources: ['admins'], body: departmentBody },
  removeDepartment: { method: 'DELETE', suffix: 'department', resources: ['admins'] },
  grantRoles: { method: 'POST', suffix: 'roles', resources: EMPLOYEES, body: rolesBody },
  revokeRoles: { method: 'DELETE', suffix: 'roles', resources: EMPLOYEES, body: rolesBody },
};

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function isPositiveId(value) {
  return Number.isSafeInteger(value) && value > 0;
}

function isDepartmentId(value) {
  return Number.isSafeInteger(value) && value >= 0;
}

function requireId(value) {
  if (!isPositiveId(value)) throw new ApiError(0, 'invalid-request');
  return value;
}

function hasText(value, fields) {
  return fields.every((field) => typeof value[field] === 'string');
}

function isClient(value) {
  return isRecord(value) && isPositiveId(value.client_id) && typeof value.enabled === 'boolean' &&
    hasText(value, PROFILE_FIELDS.clients);
}

function isEmployee(value) {
  return isRecord(value) && isPositiveId(value.employee_id) &&
    typeof value.enabled === 'boolean' && typeof value.enabled_login === 'boolean' &&
    hasText(value, [...EMPLOYEE_FIELDS, 'login']) &&
    Array.isArray(value.roles) && value.roles.every(isPositiveId);
}

function isUser(value) {
  return isEmployee(value) && isPositiveId(value.client_id);
}

function isAdmin(value) {
  return isEmployee(value) && isDepartmentId(value.department_id) && typeof value.job_title === 'string';
}

function isDepartment(value) {
  return isRecord(value) && isPositiveId(value.department_id) &&
    typeof value.name === 'string' && typeof value.enabled === 'boolean';
}

function isPermissionList(value) {
  return Array.isArray(value) && value.every((permission) => typeof permission === 'string' && permission.length > 0);
}

function isRole(value) {
  return isRecord(value) && isPositiveId(value.role_id) && hasText(value, ['name', 'description']) &&
    typeof value.is_system_role === 'boolean' && isPermissionList(value.permissions);
}

function requireResource(resource) {
  if (!Object.hasOwn(RESOURCES, resource)) throw new ApiError(0, 'invalid-request');
  return RESOURCES[resource];
}

function requireRecord(payload) {
  if (!isRecord(payload)) throw new ApiError(0, 'invalid-request');
  return payload;
}

function requireRow(definition, value, expectedId, status = 200) {
  if (!definition.check(value) || (expectedId !== undefined && value[definition.id] !== expectedId)) {
    throw new ApiError(status, 'invalid-response');
  }
  return value;
}

function collectionPath(definition) {
  return definition.roles ? definition.path : `${definition.path}/`;
}

function requireFields(payload, fields) {
  const invalid = fields.filter((field) => field === 'department_id'
    ? !isDepartmentId(payload[field])
    : typeof payload[field] !== 'string');
  if (invalid.length) throw new ApiError(422, 'validation', invalid);
}

function fullProfile(resource, payload) {
  const fields = PROFILE_FIELDS[resource];
  if (!fields) throw new ApiError(0, 'invalid-request');
  requireFields(requireRecord(payload), fields);
  return Object.fromEntries(fields.map((field) => [field, payload[field]]));
}

function accountBody(payload) {
  const { login, password, enable_account = true } = requireRecord(payload);
  const errors = [];
  if (typeof login !== 'string' || !login.trim()) errors.push('login');
  if (typeof password !== 'string' || !password) errors.push('password');
  if (typeof enable_account !== 'boolean') errors.push('enable_account');
  if (errors.length) throw new ApiError(422, 'validation', errors);
  return { login: login.trim(), password, enable_account };
}

function passwordBody(payload) {
  const { password } = requireRecord(payload);
  if (typeof password !== 'string' || !password) throw new ApiError(422, 'validation', ['password']);
  return { password };
}

function departmentBody(payload) {
  const { department_id } = requireRecord(payload);
  if (!isPositiveId(department_id)) throw new ApiError(422, 'validation', ['department_id']);
  return { department_id };
}

function rolesBody(payload) {
  const { roles } = requireRecord(payload);
  if (!Array.isArray(roles) || !roles.length || !roles.every(isPositiveId)) {
    throw new ApiError(422, 'validation', ['roles']);
  }
  return { roles: [...new Set(roles)] };
}

export function createDirectoryApi(session) {
  return {
    bindSignal: (signal) => session.bindSignal?.(signal) ?? signal,

    async list(resource, { signal } = {}) {
      const definition = requireResource(resource);
      const rows = await session.get(collectionPath(definition), { signal });
      if (!Array.isArray(rows) || !rows.every(definition.check)) {
        throw new ApiError(200, 'invalid-response');
      }
      return rows;
    },

    async get(resource, id, { signal } = {}) {
      const definition = requireResource(resource);
      requireId(id);
      return requireRow(definition, await session.get(`${definition.path}/${id}`, { signal }), id);
    },

    async create(resource, payload, { idempotencyKey, signal } = {}) {
      const definition = requireResource(resource);
      const value = await session.mutate(collectionPath(definition), {
        method: 'POST', json: requireRecord(payload), idempotencyKey, expectedStatus: 201, signal,
      });
      return requireRow(definition, value, undefined, 201);
    },

    async update(resource, id, payload, { signal } = {}) {
      const definition = requireResource(resource);
      requireId(id);
      const value = await session.mutate(`${definition.path}/${id}${definition.updateSuffix ?? ''}`, {
        method: 'PUT', json: fullProfile(resource, payload), expectedStatus: 200, signal,
      });
      return requireRow(definition, value, id);
    },

    async remove(resource, id, { signal } = {}) {
      const definition = requireResource(resource);
      requireId(id);
      const response = await session.mutate(`${definition.path}/${id}`, {
        method: 'DELETE', expectedStatus: 204, signal,
      });
      if (response !== null) throw new ApiError(200, 'invalid-response');
      return null;
    },

    async action(resource, id, action, payload, { idempotencyKey, signal } = {}) {
      const definition = requireResource(resource);
      requireId(id);
      if (idempotencyKey !== undefined ||
          !Object.hasOwn(ACTIONS, action) || !ACTIONS[action].resources.includes(resource)) {
        throw new ApiError(0, 'invalid-request');
      }
      const command = ACTIONS[action];
      if (!command.body && payload != null && (!isRecord(payload) || Object.keys(payload).length > 0)) {
        throw new ApiError(0, 'invalid-request');
      }
      const value = await session.mutate(`${definition.path}/${id}/${command.suffix}`, {
        method: command.method, ...(command.body ? { json: command.body(payload) } : {}),
        expectedStatus: 200, signal,
      });
      return requireRow(definition, value, id);
    },

    async permissions(resource, { signal } = {}) {
      const definition = requireResource(resource);
      if (!definition.roles) throw new ApiError(0, 'invalid-request');
      const value = await session.get(`${definition.path}/permissions`, { signal });
      if (!isPermissionList(value)) throw new ApiError(200, 'invalid-response');
      return value;
    },
  };
}
