import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { Row } from "../types";
import { PaginationInfo, ResourceTable } from "./ResourceTable";

export function ResourcePage({ title, path, form }: { title: string; path: string; form?: React.ReactNode }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [pagination, setPagination] = useState<PaginationInfo>({
    total: 0,
    page: 1,
    page_size: 20,
    total_pages: 0,
  });

  const load = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      if (search) params.set("search", search);
      const separator = path.includes("?") ? "&" : "?";
      const payload = await apiRequest<any>(`${path}${separator}${params.toString()}`);

      if (Array.isArray(payload.data)) {
        setRows(payload.data);
      } else {
        setRows([]);
      }

      if (payload.total !== undefined) {
        setPagination({
          total: payload.total,
          page: payload.page,
          page_size: payload.page_size,
          total_pages: payload.total_pages,
        });
      }
    } catch (err) {
      setError("Impossible de charger les données.");
    } finally {
      setLoading(false);
    }
  }, [path, page, search]);

  useEffect(() => {
    load();
    const handler = () => {
      setPage(1);
      setSearch("");
      load();
    };
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [load]);

  useEffect(() => {
    load();
  }, [page, search, load]);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleSearchChange = (newSearch: string) => {
    setSearch(newSearch);
    setPage(1);
  };

  return (
    <section>
      <h1>{title}</h1>
      <p className="muted">Données chargées depuis l'API backend.</p>
      {form}
      {loading && (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
          <p className="muted" style={{ marginTop: "12px" }}>Chargement...</p>
        </div>
      )}
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {!loading && (
        <ResourceTable
          rows={rows}
          pagination={pagination}
          onPageChange={handlePageChange}
          serverSearch={search}
          onServerSearchChange={handleSearchChange}
        />
      )}
    </section>
  );
}
