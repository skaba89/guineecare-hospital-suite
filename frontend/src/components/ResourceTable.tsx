import { useMemo, useState } from "react";
import { Row } from "../types";
import { Search, Filter, RotateCcw, ChevronUp, ChevronDown, Inbox } from "lucide-react";
import { useT } from "../i18n";
import { EmptyState } from "./States";

export interface PaginationInfo {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export function ResourceTable({
  rows,
  pagination,
  onPageChange,
  serverSearch,
  onServerSearchChange,
  searchPlaceholder,
}: {
  rows: Row[];
  pagination?: PaginationInfo;
  onPageChange?: (page: number) => void;
  serverSearch?: string;
  onServerSearchChange?: (search: string) => void;
  searchPlaceholder?: string;
}) {
  const t = useT();
  const [localSearch, setLocalSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState("");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const columns = rows.length ? Object.keys(rows[0]).slice(0, 7) : [];
  const statusOptions = useMemo(() => {
    return Array.from(new Set(rows.map((row) => row.status).filter(Boolean))).sort();
  }, [rows]);

  const visibleRows = useMemo(() => {
    const lowerSearch = localSearch.trim().toLowerCase();
    let nextRows = rows.filter((row) => {
      // v2.8.7 — Fix : convertir proprement les valeurs en string pour la recherche
      // Avant : Object.values(row).join(" ") convertissait les Dates et objets
      // en "[object Object]" → recherche ne matchait pas les dates
      const matchesSearch = !lowerSearch || Object.values(row).some((v) => {
        if (v === null || v === undefined) return false;
        if (typeof v === "object") {
          // Date → ISO string, autres objets → JSON
          if (v instanceof Date) return v.toISOString().toLowerCase().includes(lowerSearch);
          try { return JSON.stringify(v).toLowerCase().includes(lowerSearch); } catch { return false; }
        }
        return String(v).toLowerCase().includes(lowerSearch);
      });
      const matchesStatus = !statusFilter || String(row.status || "") === statusFilter;
      return matchesSearch && matchesStatus;
    });

    if (sortKey) {
      nextRows = [...nextRows].sort((a, b) => compareValues(a[sortKey], b[sortKey], sortDirection));
    }

    return nextRows;
  }, [rows, localSearch, statusFilter, sortKey, sortDirection]);

  function toggleSort(column: string) {
    if (sortKey === column) {
      setSortDirection((direction) => (direction === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(column);
    setSortDirection("asc");
  }

  function resetFilters() {
    setLocalSearch("");
    setStatusFilter("");
    setSortKey("");
    setSortDirection("asc");
    if (onServerSearchChange) onServerSearchChange("");
  }

  const hasServerPagination = !!pagination && !!onPageChange;
  const hasActiveFilters = !!(localSearch || statusFilter || serverSearch);

  return (
    <div className="card">
      <div className="table-toolbar">
        {onServerSearchChange ? (
          <label className="toolbar-control">
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Search size={12} />
              {t("action.search")}
            </span>
            <input
              placeholder={searchPlaceholder ?? t("label.no_results")}
              value={serverSearch || ""}
              onChange={(event) => onServerSearchChange(event.target.value)}
              aria-label={t("action.search")}
            />
          </label>
        ) : (
          <label className="toolbar-control">
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Search size={12} />
              {t("action.search")}
            </span>
            <input
              placeholder={searchPlaceholder ?? t("label.no_results")}
              value={localSearch}
              onChange={(event) => setLocalSearch(event.target.value)}
              aria-label={t("action.search")}
            />
          </label>
        )}
        {statusOptions.length > 0 && (
          <label className="toolbar-control">
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Filter size={12} />
              {t("label.status")}
            </span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              aria-label={t("label.status")}
            >
              <option value="">{t("action.view") === "Voir" ? "Tous" : "All"}</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </label>
        )}
        {hasActiveFilters && (
          <button
            className="secondary-button"
            type="button"
            onClick={resetFilters}
            style={{ display: "flex", alignItems: "center", gap: 4 }}
            title={t("label.refresh")}
          >
            <RotateCcw size={12} />
            {t("action.reset")}
          </button>
        )}
        <span className="muted" style={{ fontSize: 12 }}>
          {hasServerPagination
            ? `${pagination.total} résultat(s) — Page ${pagination.page} / ${pagination.total_pages || 1}`
            : `${visibleRows.length} / ${rows.length} ligne(s)`}
        </span>
      </div>

      {rows.length === 0 ? (
        <EmptyState
          icon={<Inbox size={24} />}
          title={t("label.no_data")}
          description={t("label.no_results")}
        />
      ) : visibleRows.length === 0 && !hasServerPagination ? (
        <EmptyState
          icon={<Inbox size={24} />}
          title={t("label.no_results")}
          description="Aucune ligne ne correspond aux filtres actuels."
          action={
            <button className="btn btn-outline btn-sm" onClick={resetFilters}>
              {t("action.reset")}
            </button>
          }
        />
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col}>
                    <button
                      className="table-sort-button"
                      type="button"
                      onClick={() => toggleSort(col)}
                      aria-label={`Trier par ${col}`}
                      style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
                    >
                      {col}
                      {sortKey === col && (
                        sortDirection === "asc"
                          ? <ChevronUp size={12} />
                          : <ChevronDown size={12} />
                      )}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(hasServerPagination ? rows : visibleRows).map((row, index) => (
                <tr key={row.id || index}>
                  {columns.map((col) => <td key={col}>{String(row[col] ?? "")}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {hasServerPagination && pagination.total_pages > 1 && (
        <div className="pagination-controls">
          <button
            className="secondary-button"
            type="button"
            disabled={pagination.page <= 1}
            onClick={() => onPageChange(pagination.page - 1)}
            aria-label="Page précédente"
          >
            ← {t("action.previous")}
          </button>
          <span className="pagination-info">
            {t("label.page")} {pagination.page} / {pagination.total_pages}
          </span>
          <button
            className="secondary-button"
            type="button"
            disabled={pagination.page >= pagination.total_pages}
            onClick={() => onPageChange(pagination.page + 1)}
            aria-label="Page suivante"
          >
            {t("action.next")} →
          </button>
        </div>
      )}
    </div>
  );
}

function compareValues(a: unknown, b: unknown, direction: "asc" | "desc") {
  const multiplier = direction === "asc" ? 1 : -1;
  const aNumber = Number(a);
  const bNumber = Number(b);

  if (!Number.isNaN(aNumber) && !Number.isNaN(bNumber)) {
    return (aNumber - bNumber) * multiplier;
  }

  return String(a ?? "").localeCompare(String(b ?? "")) * multiplier;
}
