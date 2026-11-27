import { ApiError } from '../../api/transport.js';

const field = (name, type = 'text', required = false) => Object.freeze({ name, type, required });
const name = field('name', 'text', true);
const email = field('email', 'email');
const phone = field('phone', 'tel');
const description = field('description', 'textarea');
const client = field('client_id', 'client', true);
const department = field('department_id', 'department');
const employeeFields = [field('first_name', 'text', true), field('last_name'), email, phone];
const adminFields = [...employeeFields, field('job_title')];
const clientFields = [name, email, phone, field('address'), description];
const roleFields = [name, description, field('permissions', 'permissions', true), field('is_system_role', 'checkbox')];

function definition(resource, {
  idKey, read, write, create = [write], columns, createFields, updateFields = createFields,
}) {
  return Object.freeze({
    idKey,
    labelKey: `directory.resource.${resource}`,
    readPermissions: Object.freeze([read]),
    createPermissions: Object.freeze(create),
    updatePermissions: Object.freeze(updateFields.length ? [write] : []),
    removePermissions: Object.freeze([write]),
    columns: Object.freeze(columns),
    fields: Object.freeze({
      create: Object.freeze(createFields),
      update: Object.freeze(updateFields),
    }),
  });
}

export const DIRECTORIES = Object.freeze({
  clients: definition('clients', {
    idKey: 'client_id', read: 'client.view', write: 'client.operation',
    create: ['client.create', 'client.operation', 'client.decision'],
    columns: ['name', 'email', 'phone', 'enabled'], createFields: clientFields,
  }),
  users: definition('users', {
    idKey: 'employee_id', read: 'user.view', write: 'user.operation',
    columns: ['first_name', 'last_name', 'client_id', 'email', 'enabled'],
    createFields: [client, ...employeeFields], updateFields: employeeFields,
  }),
  admins: definition('admins', {
    idKey: 'employee_id', read: 'admin.view', write: 'admin.operation',
    columns: ['first_name', 'last_name', 'job_title', 'department_id', 'enabled'],
    createFields: [...adminFields, department], updateFields: adminFields,
  }),
  departments: definition('departments', {
    idKey: 'department_id', read: 'department.view', write: 'department.operation',
    columns: ['name', 'enabled'], createFields: [name],
  }),
  adminRoles: definition('adminRoles', {
    idKey: 'role_id', read: 'role.assign', write: 'role.assign',
    columns: ['name', 'permissions', 'is_system_role'], createFields: roleFields, updateFields: [],
  }),
  userRoles: definition('userRoles', {
    idKey: 'role_id', read: 'role_user.assign', write: 'role_user.assign',
    columns: ['name', 'permissions', 'is_system_role'], createFields: roleFields, updateFields: [],
  }),
});

const CAPABILITIES = {
  read: 'readPermissions', create: 'createPermissions', update: 'updatePermissions', remove: 'removePermissions',
};
const PROFILE_WRITERS = {
  users: 'user.operation', admins: 'admin.operation', departments: 'department.operation',
};
const ROLE_WRITERS = { users: 'role_user.assign', admins: 'role.assign' };
const ACCOUNT_ACTIONS = ['attachAccount', 'detachAccount', 'enableAccount', 'disableAccount', 'changePassword'];

export function canDirectory(resource, operation, permissions = []) {
  if (!Object.hasOwn(DIRECTORIES, resource) || !Object.hasOwn(CAPABILITIES, operation) ||
      !Array.isArray(permissions)) return false;
  return DIRECTORIES[resource][CAPABILITIES[operation]].some((permission) => permissions.includes(permission));
}

export function canDirectoryAction(resource, action, permissions = []) {
  if (!Object.hasOwn(DIRECTORIES, resource) || !Array.isArray(permissions)) return false;
  const employee = resource === 'users' || resource === 'admins';
  if (action === 'enable' || action === 'disable') {
    const required = resource === 'clients' ? 'client.decision' : PROFILE_WRITERS[resource];
    return typeof required === 'string' && permissions.includes(required);
  }
  if (action === 'grantRoles' || action === 'revokeRoles') {
    return employee && permissions.includes(ROLE_WRITERS[resource]);
  }
  if (action === 'changeDepartment' || action === 'removeDepartment') {
    return resource === 'admins' && permissions.includes('admin.operation');
  }
  return employee && ACCOUNT_ACTIONS.includes(action) && permissions.includes(PROFILE_WRITERS[resource]);
}

export function directoryLabel(resource, row) {
  if (!row || !Object.hasOwn(DIRECTORIES, resource)) return '';
  const label = resource === 'users' || resource === 'admins'
    ? [row.first_name, row.last_name].filter(Boolean).join(' ').trim()
    : row.name;
  return label || String(row[DIRECTORIES[resource].idKey] ?? '');
}

function fieldsFor(resource, mode) {
  if (!Object.hasOwn(DIRECTORIES, resource) || (mode !== 'create' && mode !== 'update')) {
    throw new ApiError(0, 'invalid-request');
  }
  return DIRECTORIES[resource].fields[mode];
}

function initialValue(fieldInfo, value) {
  switch (fieldInfo.type) {
    case 'client':
    case 'department': return value ?? 0;
    case 'permissions': return Array.isArray(value) ? [...value] : [];
    case 'checkbox': return value ?? false;
    default: return value ?? '';
  }
}

export function directoryFormValues(resource, mode, row) {
  return Object.fromEntries(fieldsFor(resource, mode).map((descriptor) => [
    descriptor.name, initialValue(descriptor, row?.[descriptor.name]),
  ]));
}

function validateField({ name, type, required }, value) {
  switch (type) {
    case 'client':
    case 'department': {
      const id = typeof value === 'string' && /^\d+$/.test(value)
        ? Number(value)
        : value === '' ? 0 : value;
      if (Number.isSafeInteger(id) && id >= (required ? 1 : 0)) return id;
      break;
    }
    case 'permissions':
      if (Array.isArray(value) && value.length > 0 &&
          value.every((permission) => typeof permission === 'string' && permission.trim())) {
        return [...new Set(value)];
      }
      break;
    case 'checkbox':
      if (typeof value === 'boolean') return value;
      break;
    default:
      if (typeof value === 'string' && (!required || value.trim())) {
        if (name === 'job_title') return value;
        const text = value.trim();
        return type === 'email' ? text.toLowerCase() : text;
      }
  }
  throw new ApiError(422, 'validation', [name]);
}

export function directoryPayload(resource, mode, draft, current) {
  const fields = fieldsFor(resource, mode);
  if (!fields.length || !draft || typeof draft !== 'object') throw new ApiError(0, 'invalid-request');
  const payload = {};
  const invalid = [];
  for (const descriptor of fields) {
    const key = descriptor.name;
    const value = Object.hasOwn(draft, key)
      ? draft[key]
      : mode === 'create' ? initialValue(descriptor) : current?.[key];
    try {
      payload[key] = validateField(descriptor, value);
    } catch (error) {
      if (error?.status !== 422) throw error;
      invalid.push(...error.fields);
    }
  }
  if (mode === 'update' && resource === 'admins') {
    if (!Number.isSafeInteger(current?.department_id) || current.department_id < 0) {
      throw new ApiError(0, 'invalid-request');
    }
    payload.department_id = current.department_id;
  }
  if (invalid.length) throw new ApiError(422, 'validation', invalid);
  return payload;
}
