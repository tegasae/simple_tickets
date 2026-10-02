import { createContext, useCallback, useContext, useRef, useState } from "react";
import { api } from "./api.js";

const ReferenceDataContext = createContext(null);

function normalizeRows(payload) {
  return Array.isArray(payload) ? payload : [];
}

function upsertInto(rows, item, key) {
  if (!item) return rows;
  const id = Number(item[key] || 0);
  if (!id) return rows;
  const index = rows.findIndex((row) => Number(row[key]) === id);
  if (index < 0) return [...rows, item];
  const next = [...rows];
  next[index] = item;
  return next;
}

export function ReferenceDataProvider({ children }) {
  const [clients, setClients] = useState([]);
  const [admins, setAdmins] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [usersById, setUsersById] = useState({});
  const [usersByClient, setUsersByClient] = useState({});

  const clientsRef = useRef([]);
  const adminsRef = useRef([]);
  const departmentsRef = useRef([]);
  const usersByIdRef = useRef({});
  const usersByClientRef = useRef({});

  const loadedRef = useRef({ clients: false, admins: false, departments: false, allUsers: false });
  const loadedUserClientsRef = useRef(new Set());
  const inFlightRef = useRef({});

  const replaceClients = useCallback((rows) => {
    const next = normalizeRows(rows);
    clientsRef.current = next;
    setClients(next);
    return next;
  }, []);

  const replaceAdmins = useCallback((rows) => {
    const next = normalizeRows(rows);
    adminsRef.current = next;
    setAdmins(next);
    return next;
  }, []);

  const replaceDepartments = useCallback((rows) => {
    const next = normalizeRows(rows);
    departmentsRef.current = next;
    setDepartments(next);
    return next;
  }, []);

  const mergeUsers = useCallback((rows, { clientId = 0, all = false } = {}) => {
    const list = normalizeRows(rows);
    let nextById = all ? {} : { ...usersByIdRef.current };
    let nextByClient = all ? {} : { ...usersByClientRef.current };

    if (clientId > 0 && !all) {
      const previousIds = new Set(nextByClient[clientId] || []);
      for (const previousId of previousIds) delete nextById[previousId];
    }

    for (const user of list) {
      const id = Number(user?.employee_id || 0);
      if (id) nextById[id] = user;
    }

    if (all) {
      loadedUserClientsRef.current = new Set();
      for (const user of list) {
        const cid = Number(user?.client_id || 0);
        const id = Number(user?.employee_id || 0);
        if (!cid || !id) continue;
        if (!nextByClient[cid]) nextByClient[cid] = [];
        nextByClient[cid].push(id);
        loadedUserClientsRef.current.add(cid);
      }
      loadedRef.current.allUsers = true;
    } else if (clientId > 0) {
      nextByClient[clientId] = list.map((user) => Number(user.employee_id)).filter(Boolean);
      loadedUserClientsRef.current.add(Number(clientId));
    } else {
      for (const user of list) {
        const cid = Number(user?.client_id || 0);
        const id = Number(user?.employee_id || 0);
        if (!cid || !id) continue;
        if (!loadedRef.current.allUsers && !loadedUserClientsRef.current.has(cid)) continue;
        const current = nextByClient[cid] || [];
        if (!current.includes(id)) nextByClient[cid] = [...current, id];
      }
    }

    usersByIdRef.current = nextById;
    usersByClientRef.current = nextByClient;
    setUsersById(nextById);
    setUsersByClient(nextByClient);
    return list;
  }, []);

  const ensureCollection = useCallback(async (name, force, loader, replace) => {
    if (!force && loadedRef.current[name]) {
      if (name === "clients") return clientsRef.current;
      if (name === "admins") return adminsRef.current;
      if (name === "departments") return departmentsRef.current;
    }
    const key = `${name}:${force ? "force" : "normal"}`;
    if (!inFlightRef.current[key]) {
      inFlightRef.current[key] = loader()
        .then((payload) => {
          loadedRef.current[name] = true;
          return replace(payload);
        })
        .finally(() => { delete inFlightRef.current[key]; });
    }
    return inFlightRef.current[key];
  }, [replaceAdmins, replaceClients, replaceDepartments]);

  const ensureClients = useCallback((force = false) => ensureCollection("clients", force, api.getClients, replaceClients), [ensureCollection, replaceClients]);
  const ensureAdmins = useCallback((force = false) => ensureCollection("admins", force, api.getAdmins, replaceAdmins), [ensureCollection, replaceAdmins]);
  const ensureDepartments = useCallback((force = false) => ensureCollection("departments", force, api.getDepartments, replaceDepartments), [ensureCollection, replaceDepartments]);

  const ensureClient = useCallback(async (clientId) => {
    const id = Number(clientId || 0);
    if (!id) return null;
    const cached = clientsRef.current.find((row) => Number(row.client_id) === id);
    if (cached) return cached;
    const key = `client:${id}`;
    if (!inFlightRef.current[key]) {
      inFlightRef.current[key] = api.getClient(id).then((item) => {
        const next = upsertInto(clientsRef.current, item, "client_id");
        clientsRef.current = next;
        setClients(next);
        return item;
      }).finally(() => { delete inFlightRef.current[key]; });
    }
    return inFlightRef.current[key];
  }, []);

  const ensureAdmin = useCallback(async (employeeId) => {
    const id = Number(employeeId || 0);
    if (!id) return null;
    const cached = adminsRef.current.find((row) => Number(row.employee_id) === id);
    if (cached) return cached;
    const key = `admin:${id}`;
    if (!inFlightRef.current[key]) {
      inFlightRef.current[key] = api.getAdmin(id).then((item) => {
        const next = upsertInto(adminsRef.current, item, "employee_id");
        adminsRef.current = next;
        setAdmins(next);
        return item;
      }).finally(() => { delete inFlightRef.current[key]; });
    }
    return inFlightRef.current[key];
  }, []);

  const ensureDepartment = useCallback(async (departmentId) => {
    const id = Number(departmentId || 0);
    if (!id) return null;
    const cached = departmentsRef.current.find((row) => Number(row.department_id) === id);
    if (cached) return cached;
    const key = `department:${id}`;
    if (!inFlightRef.current[key]) {
      inFlightRef.current[key] = api.getDepartment(id).then((item) => {
        const next = upsertInto(departmentsRef.current, item, "department_id");
        departmentsRef.current = next;
        setDepartments(next);
        return item;
      }).finally(() => { delete inFlightRef.current[key]; });
    }
    return inFlightRef.current[key];
  }, []);

  const ensureUser = useCallback(async (employeeId) => {
    const id = Number(employeeId || 0);
    if (!id) return null;
    if (usersByIdRef.current[id]) return usersByIdRef.current[id];
    const key = `user:${id}`;
    if (!inFlightRef.current[key]) {
      inFlightRef.current[key] = api.getUser(id).then((item) => {
        mergeUsers([item]);
        return item;
      }).finally(() => { delete inFlightRef.current[key]; });
    }
    return inFlightRef.current[key];
  }, [mergeUsers]);

  const ensureUsersByClient = useCallback(async (clientId, force = false) => {
    const id = Number(clientId || 0);
    if (!id) return [];
    if (!force && (loadedRef.current.allUsers || loadedUserClientsRef.current.has(id))) {
      return (usersByClientRef.current[id] || []).map((userId) => usersByIdRef.current[userId]).filter(Boolean);
    }
    const key = `users-client:${id}:${force ? "force" : "normal"}`;
    if (!inFlightRef.current[key]) {
      inFlightRef.current[key] = api.getUsers(id).then((payload) => mergeUsers(payload, { clientId: id })).finally(() => { delete inFlightRef.current[key]; });
    }
    return inFlightRef.current[key];
  }, [mergeUsers]);

  const ensureAllUsers = useCallback(async (force = false) => {
    if (!force && loadedRef.current.allUsers) return Object.values(usersByIdRef.current);
    const key = `users-all:${force ? "force" : "normal"}`;
    if (!inFlightRef.current[key]) {
      inFlightRef.current[key] = api.getUsers().then((payload) => mergeUsers(payload, { all: true })).finally(() => { delete inFlightRef.current[key]; });
    }
    return inFlightRef.current[key];
  }, [mergeUsers]);

  const upsertClient = useCallback((item) => {
    const next = upsertInto(clientsRef.current, item, "client_id");
    clientsRef.current = next;
    setClients(next);
    return item;
  }, []);
  const removeClient = useCallback((clientId) => {
    const id = Number(clientId);
    const next = clientsRef.current.filter((row) => Number(row.client_id) !== id);
    clientsRef.current = next;
    setClients(next);
  }, []);

  const upsertAdmin = useCallback((item) => {
    const next = upsertInto(adminsRef.current, item, "employee_id");
    adminsRef.current = next;
    setAdmins(next);
    return item;
  }, []);
  const removeAdmin = useCallback((employeeId) => {
    const id = Number(employeeId);
    const next = adminsRef.current.filter((row) => Number(row.employee_id) !== id);
    adminsRef.current = next;
    setAdmins(next);
  }, []);

  const upsertDepartment = useCallback((item) => {
    const next = upsertInto(departmentsRef.current, item, "department_id");
    departmentsRef.current = next;
    setDepartments(next);
    return item;
  }, []);
  const removeDepartment = useCallback((departmentId) => {
    const id = Number(departmentId);
    const next = departmentsRef.current.filter((row) => Number(row.department_id) !== id);
    departmentsRef.current = next;
    setDepartments(next);
  }, []);

  const upsertUser = useCallback((item) => {
    mergeUsers([item]);
    return item;
  }, [mergeUsers]);
  const removeUser = useCallback((employeeId) => {
    const id = Number(employeeId);
    const current = { ...usersByIdRef.current };
    const user = current[id];
    delete current[id];
    usersByIdRef.current = current;
    setUsersById(current);
    if (user?.client_id) {
      const cid = Number(user.client_id);
      const byClient = { ...usersByClientRef.current, [cid]: (usersByClientRef.current[cid] || []).filter((x) => Number(x) !== id) };
      usersByClientRef.current = byClient;
      setUsersByClient(byClient);
    }
  }, []);

  const users = Object.values(usersById);
  const getUsersForClient = useCallback((clientId) => {
    const ids = usersByClient[Number(clientId)] || [];
    return ids.map((id) => usersById[id]).filter(Boolean);
  }, [usersByClient, usersById]);

  const value = {
    clients, admins, departments, users, usersById,
    ensureClients, ensureClient, upsertClient, removeClient,
    ensureAdmins, ensureAdmin, upsertAdmin, removeAdmin,
    ensureDepartments, ensureDepartment, upsertDepartment, removeDepartment,
    ensureAllUsers, ensureUsersByClient, ensureUser, upsertUser, removeUser, getUsersForClient,
  };

  return <ReferenceDataContext.Provider value={value}>{children}</ReferenceDataContext.Provider>;
}

export function useReferenceData() {
  const value = useContext(ReferenceDataContext);
  if (!value) throw new Error("useReferenceData must be used inside ReferenceDataProvider");
  return value;
}
