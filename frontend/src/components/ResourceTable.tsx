import { useMemo, useState } from "react";
import { Row } from "../types";

export function ResourceTable({ rows }: { rows: Row[] }) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState("");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const columns = rows.length ? Object.keys(rows[0]).slice(0, 7) : [];
  const statusOptions = useMemo(() => {
    return Array.from(new Set(rows.map((row) => row.status).filter(Boolean))).sort();
  }, [rows]);

  const visibleRows = useMemo(() => {
    const lowerSearch = search.trim().toLowerCase();
    let nextRows = rows.filter((row) => {
      const matchesSearch = !lowerSearch || Object.values(row).join(" ").toLowerCase().includes(lowerSearch);
      const matchesStatus = !statusFilter || String(row.status || "") === statusFilter;
      return matchesSearch && matchesStatus;
    });

    if (sortKey) {
      nextRows = [...nextRows].sort((a, b) => compareValues(a[sortKey], b[sortKey], sortDirection));
    }

    return nextRows;
  }, [rows, search, statusFilter, sortKey, sortDirection]);

  function toggleSort(column: string) {
    if (sortKey === column) {
      setSortDirection((direction) => (direction === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(column);
    setSortDirection("asc");
  }

  return (
    <div className="card">
      <div className="table-toolbar">
        <label className="toolbar-control">
          Recherche
          <input
            placeholder="Rechercher dans le tableau"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
        {statusOptions.length > 0 && (
          <label className="toolbar-control">
            Statut
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">Tous</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </label>
        )}
        <button
          className="secondary-button"
          type="button"
          onClick={() => {
            setSearch("");
            setStatusFilter("");
            setSortKey("");
            setSortDirection("asc");
          }}
        >
          Reinitialiser
        </button>
        <span className="muted">{visibleRows.length} / {rows.length} ligne(s)</span>
      </div>

      {rows.length === 0 ? (
        <p className="muted">Aucune donnee disponible pour le moment.</p>
      ) : visibleRows.length === 0 ? (
        <p className="muted">Aucun resultat ne correspond aux filtres.</p>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col}>
                    <button className="table-sort-button" type="button" onClick={() => toggleSort(col)}>
                      {col} {sortKey === col ? (sortDirection === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleRows.map((row, index) => (
                <tr key={row.id || index}>
                  {columns.map((col) => <td key={col}>{String(row[col] ?? "")}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
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
