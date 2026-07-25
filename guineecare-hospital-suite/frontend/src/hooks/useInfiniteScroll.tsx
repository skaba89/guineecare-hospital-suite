import { useCallback, useEffect, useRef, useState } from "react";
import { apiRequest } from "../services/api";

/**
 * Hook de liste avec infinite scroll — v2.9.2
 *
 * Comme usePaginatedList, mais au lieu d'afficher une pagination classique,
 * charge automatiquement la page suivante quand l'utilisateur scroll
 * près du bas de la liste.
 *
 * Usage :
 *   const { items, loading, hasMore, loadMore, reset } = useInfiniteScroll<Patient>(
 *     "/patients",
 *     { pageSize: 20, search: "diallo" }
 *   );
 *
 *   // Dans le composant :
 *   <ul>
 *     {items.map(p => <li key={p.id}>{p.first_name}</li>)}
 *     {loading && <li>Chargement...</li>}
 *     <Sentinel onVisible={loadMore} disabled={!hasMore || loading} />
 *   </ul>
 *
 * Implémentation :
 * - Append-only : les nouvelles pages sont ajoutées à `items` (pas de remplacement)
 * - Debounce sur le search pour éviter les appels en rafale
 * - Reset quand `search` ou `extraParams` changent
 * - IntersectionObserver pour détecter le scroll en bas
 */
type PaginatedResponse<T> = {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

type UseInfiniteScrollOptions<T> = {
  pageSize?: number;
  search?: string;
  debounceMs?: number;
  extraParams?: Record<string, string | number | boolean | null | undefined>;
  enabled?: boolean;
  /** Transformer la réponse API si elle n'est pas au format standard */
  transform?: (resp: any) => PaginatedResponse<T>;
};

export function useInfiniteScroll<T = any>(
  basePath: string,
  options: UseInfiniteScrollOptions<T> = {},
) {
  const {
    pageSize = 20,
    search = "",
    debounceMs = 300,
    extraParams = {},
    enabled = true,
    transform,
  } = options;

  const [items, setItems] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasMore, setHasMore] = useState(true);

  // Refs pour éviter les fermetures stale
  const loadingRef = useRef(false);
  const pageRef = useRef(1);
  const hasMoreRef = useRef(true);
  const searchRef = useRef(search);
  const extraParamsKey = JSON.stringify(extraParams || {});

  // Reset quand search ou extraParams changent
  useEffect(() => {
    if (searchRef.current !== search || pageRef.current !== 1) {
      searchRef.current = search;
      pageRef.current = 1;
      setPage(1);
      setItems([]);
      setHasMore(true);
      hasMoreRef.current = true;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, extraParamsKey]);

  // Debounce search
  const [debouncedSearch, setDebouncedSearch] = useState(search);
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), debounceMs);
    return () => clearTimeout(t);
  }, [search, debounceMs]);

  const fetchPage = useCallback(
    async (pageNum: number, replace: boolean = false) => {
      if (loadingRef.current || !enabled) return;
      if (!replace && !hasMoreRef.current) return;

      loadingRef.current = true;
      setLoading(true);
      setError("");

      try {
        const params = new URLSearchParams({
          page: String(pageNum),
          page_size: String(pageSize),
        });
        if (debouncedSearch) params.set("search", debouncedSearch);
        for (const [k, v] of Object.entries(extraParams || {})) {
          if (v != null && v !== "") params.set(k, String(v));
        }

        const url = `${basePath}?${params.toString()}`;
        const resp = await apiRequest(url);
        const data = (transform ? transform(resp) : resp) as PaginatedResponse<T>;

        setItems((prev) => (replace ? data.data : [...prev, ...data.data]));
        setTotal(data.total);
        setTotalPages(data.total_pages);
        setPage(data.page);
        pageRef.current = data.page;

        const newHasMore = data.page < data.total_pages;
        setHasMore(newHasMore);
        hasMoreRef.current = newHasMore;
      } catch (e: any) {
        setError(e?.message || "Erreur de chargement");
      } finally {
        loadingRef.current = false;
        setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [basePath, pageSize, debouncedSearch, extraParamsKey, enabled, transform],
  );

  // Fetch initial quand search/extraParams changent (après reset)
  useEffect(() => {
    if (enabled) {
      fetchPage(1, true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch, extraParamsKey, enabled]);

  const loadMore = useCallback(() => {
    if (!loadingRef.current && hasMoreRef.current) {
      fetchPage(pageRef.current + 1);
    }
  }, [fetchPage]);

  const reset = useCallback(() => {
    pageRef.current = 1;
    setPage(1);
    setItems([]);
    setHasMore(true);
    hasMoreRef.current = true;
    fetchPage(1, true);
  }, [fetchPage]);

  return {
    items,
    total,
    page,
    totalPages,
    loading,
    error,
    hasMore,
    loadMore,
    reset,
  };
}

/**
 * Composant Sentinel — à placer en bas de liste.
 * Déclenche `onVisible` quand l'élément devient visible (IntersectionObserver).
 */
export function Sentinel({
  onVisible,
  disabled,
}: {
  onVisible: () => void;
  disabled?: boolean;
}) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (disabled) return;
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            onVisible();
          }
        }
      },
      { rootMargin: "200px" }, // préchargement 200px avant le bas
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [onVisible, disabled]);

  return (
    <div
      ref={ref}
      data-testid="infinite-scroll-sentinel"
      style={{ height: "1px", width: "100%" }}
      aria-hidden="true"
    />
  );
}
