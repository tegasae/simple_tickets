import { useEffect, useMemo, useState } from "react";
import { loadSetting, saveSetting } from "../storage.js";

const DEFAULT_SETTINGS = {
  sortKey: "",
  sortDirection: "asc",
  filters: {},
  page: 1,
  pageSize: 25,
};

function stringValue(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "boolean") return value ? "да" : "нет";
  return String(value).toLowerCase();
}

function compareValues(a, b) {
  if (typeof a === "number" && typeof b === "number") return a - b;
  if (typeof a === "boolean" && typeof b === "boolean") return Number(a) - Number(b);
  return stringValue(a).localeCompare(stringValue(b), "ru");
}

export default function DataTable({
  storageKey,
  title,
  rows,
  columns,
  selectedId,
  getRowId,
  onRowClick,
  extraFilters,
  actions,
  emptyText = "Нет данных",
}) {
  const [settings, setSettings] = useState(() => ({ ...DEFAULT_SETTINGS, ...loadSetting(storageKey, {}) }));

  useEffect(() => {
    saveSetting(storageKey, settings);
  }, [storageKey, settings]);

  function patchSettings(patch) {
    setSettings((current) => ({ ...current, ...patch }));
  }

  function updateFilter(key, value) {
    patchSettings({
      page: 1,
      filters: { ...settings.filters, [key]: value },
    });
  }

  function changeSort(key) {
    const nextDirection = settings.sortKey === key && settings.sortDirection === "asc" ? "desc" : "asc";
    patchSettings({ sortKey: key, sortDirection: nextDirection, page: 1 });
  }

  const filteredRows = useMemo(() => {
    const activeColumns = columns.filter((column) => column.filterable !== false);
    return rows.filter((row) => {
      if (extraFilters && !extraFilters(row)) return false;
      return activeColumns.every((column) => {
        const filter = stringValue(settings.filters[column.key]).trim();
        if (!filter) return true;
        return stringValue(column.getValue ? column.getValue(row) : row[column.key]).includes(filter);
      });
    });
  }, [rows, columns, settings.filters, extraFilters]);

  const sortedRows = useMemo(() => {
    if (!settings.sortKey) return filteredRows;
    const column = columns.find((item) => item.key === settings.sortKey);
    if (!column) return filteredRows;
    const multiplier = settings.sortDirection === "asc" ? 1 : -1;
    return [...filteredRows].sort((left, right) => {
      const a = column.getValue ? column.getValue(left) : left[column.key];
      const b = column.getValue ? column.getValue(right) : right[column.key];
      return compareValues(a, b) * multiplier;
    });
  }, [filteredRows, columns, settings.sortKey, settings.sortDirection]);

  const totalPages = Math.max(1, Math.ceil(sortedRows.length / settings.pageSize));
  const page = Math.min(settings.page, totalPages);
  const pageRows = sortedRows.slice((page - 1) * settings.pageSize, page * settings.pageSize);

  useEffect(() => {
    if (settings.page > totalPages) patchSettings({ page: totalPages });
  }, [settings.page, totalPages]);

  return (
    <div className="data-table-card">
      <div className="table-toolbar">
        <div>
          <h3>{title}</h3>
          <span>{filteredRows.length} из {rows.length}</span>
        </div>
        <div className="table-actions">{actions}</div>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key} onClick={() => column.sortable === false ? undefined : changeSort(column.key)}>
                  <span>{column.label}</span>
                  {settings.sortKey === column.key && <b>{settings.sortDirection === "asc" ? "↑" : "↓"}</b>}
                </th>
              ))}
            </tr>
            <tr className="filter-row">
              {columns.map((column) => (
                <th key={column.key}>
                  {column.filterable === false ? null : (
                    <input
                      value={settings.filters[column.key] || ""}
                      placeholder="Фильтр"
                      onChange={(e) => updateFilter(column.key, e.target.value)}
                    />
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row) => {
              const rowId = getRowId(row);
              return (
                <tr
                  key={rowId}
                  className={rowId === selectedId ? "selected" : ""}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((column) => (
                    <td key={column.key} className={column.className || ""}>
                      {column.render ? column.render(row) : String(column.getValue ? column.getValue(row) ?? "" : row[column.key] ?? "")}
                    </td>
                  ))}
                </tr>
              );
            })}
            {pageRows.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="empty-cell">{emptyText}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination-row">
        <button className="btn btn-small" disabled={page <= 1} onClick={() => patchSettings({ page: page - 1 })}>Назад</button>
        <span>Страница {page} / {totalPages}</span>
        <button className="btn btn-small" disabled={page >= totalPages} onClick={() => patchSettings({ page: page + 1 })}>Вперёд</button>
        <label>
          <span>На странице</span>
          <select value={settings.pageSize} onChange={(e) => patchSettings({ pageSize: Number(e.target.value), page: 1 })}>
            {[10, 25, 50, 100, 500].map((size) => <option key={size} value={size}>{size}</option>)}
          </select>
        </label>
      </div>
    </div>
  );
}
