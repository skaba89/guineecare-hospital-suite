import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { Row } from "../types";
import { PaginationInfo, ResourceTable } from "./ResourceTable";
import { useT } from "../i18n";
import { ErrorState, PageHeader, SkeletonTable } from "./States";
import { RefreshCw } from "lucide-react";

export function ResourcePage({
  title,
  path,
  form,
  searchPlaceholder,
  subtitle,
}: {
  title: string;
  path: string;
  form?: React.ReactNode;
  searchPlaceholder?: string;
  subtitle?: string;
}) {
  const t = useT();
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
      const msg = err instanceof Error ? err.message : String(err);
      setError(`${t("label.error")}: ${msg}`);
    } finally {
      setLoading(false);
    }
  }, [path, page, search, t]);

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
      <PageHeader
        title={title}
        subtitle={subtitle ?? t("label.no_data")}
        actions={
          <button
            className="btn btn-outline btn-sm"
            onClick={() => load()}
            disabled={loading}
            style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
            title={t("label.refresh")}
          >
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            {t("label.refresh")}
          </button>
        }
      />
      {form}
      {loading && <SkeletonTable rows={6} cols={5} />}
      {error && !loading && (
        <ErrorState
          description={error}
          onRetry={load}
          retryLabel={t("label.retry")}
        />
      )}
      {!loading && !error && (
        <ResourceTable
          rows={rows}
          pagination={pagination}
          onPageChange={handlePageChange}
          serverSearch={search}
          onServerSearchChange={handleSearchChange}
          searchPlaceholder={searchPlaceholder}
        />
      )}
    </section>
  );
}
