import { useCallback, useEffect, useRef, useState } from "react";
import { apiRequest } from "../services/api";

/**
 * Hook de liste paginée avec recherche server-side + debounce.
 *
 * Usage :
 *   const { items, total, page, totalPages, loading, error, setPage, setSearch, reload } =
 *     usePaginatedList<Invoice>("/billing/invoices", { pageSize: 20, debounceMs: 300 });
 *
 * Filtres serveur additionnels (status, date_from, etc.) via `extraParams` :
 *   const { items, ... } = usePaginatedList<LabOrder>("/laboratory/orders", {
 *     pageSize: 20,
 *     extraParams: { status: "ORDERED", patient_id: "..." },
 *   });
 *
 * Le hook reconstruit l'URL à chaque changement de page/search/extraParams.
 */
type PaginatedResponse<T> = {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

type UsePaginatedListOptions = {
  pageSize?: number;
  debounceMs?: number;
  extraParams?: Record<string, string | number | boolean | null | undefined>;
  /** Si true, ne déclenche pas de fetch au montage (ex: onglet inactif). */
  enabled?: boolean;
};

export function usePaginatedList<T = any>(
  basePath: string,
  options: UsePaginatedListOptions = {}
) {
  const { pageSize = 20, debounceMs = 300, extraParams = {}, enabled = true } = options;

  const [items, setItems] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearchState] = useState("");

  // Debounce timer
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Stable extraParams (JSON string pour détecter les changements)
  const extraParamsKey = JSON.stringify(extraParams || {});

  const buildUrl = useCallback(
    (pageNum: number, searchTerm: string) => {
      const params = new URLSearchParams();
      params.set("page", String(pageNum));
      params.set("page_size", String(pageSize));
      if (searchTerm.trim()) {
        params.set("search", searchTerm.trim());
      }
      // Append extraParams
      const extra = JSON.parse(extraParamsKey) as Record<string, any>;
      Object.entries(extra).forEach(([k, v]) => {
        if (v !== null && v !== undefined && v !== "") {
          params.set(k, String(v));
        }
      });
      const sep = basePath.includes("?") ? "&" : "?";
      return `${basePath}${sep}${params.toString()}`;
    },
    [basePath, pageSize, extraParamsKey]
  );

  const fetchPage = useCallback(
    async (pageNum: number, searchTerm: string) => {
      if (!enabled) return;
      setLoading(true);
      setError("");
      try {
        const url = buildUrl(pageNum, searchTerm);
        const payload = await apiRequest<PaginatedResponse<T>>(url);
        setItems(payload.data || []);
        setTotal(payload.total || 0);
        setPage(payload.page || pageNum);
        setTotalPages(payload.total_pages || 0);
      } catch (e: any) {
        setError(e.message || "Erreur de chargement");
        setItems([]);
        setTotal(0);
        setTotalPages(0);
      } finally {
        setLoading(false);
      }
    },
    [buildUrl, enabled]
  );

  // Fetch initial + on page/extraParams change
  useEffect(() => {
    fetchPage(page, search);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, extraParamsKey, enabled]);

  // Debounced search
  const setSearch = useCallback(
    (term: string) => {
      setSearchState(term);
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      debounceRef.current = setTimeout(() => {
        setPage(1); // reset à la page 1 sur nouvelle recherche
        fetchPage(1, term);
      }, debounceMs);
    },
    [debounceMs, fetchPage]
  );

  // Reload (force refetch current page)
  const reload = useCallback(() => {
    fetchPage(page, search);
  }, [fetchPage, page, search]);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  return {
    items,
    total,
    page,
    totalPages,
    pageSize,
    loading,
    error,
    search,
    setSearch,
    setPage,
    reload,
  };
}
