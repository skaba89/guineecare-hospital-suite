/**
 * v1.2.0 — Global search Command Palette.
 *
 * Opens with Ctrl+K (or Cmd+K on macOS). Calls /api/v1/search?q=…
 * (debounced 250ms) and displays categorized results. Clicking a
 * result navigates to its URL via React Router.
 *
 * The palette is intentionally minimal: no virtualization, no fuzzy
 * matching — the backend already caps results at 10 per category and
 * 50 total. For >1000 results we'd add keyboard navigation, but that
 * is not needed at the pilote volume.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, X, Users, Receipt, FlaskConical, Scan, FileText } from "lucide-react";
import { apiRequest } from "../services/api";
import { showToast } from "./Toast";

type SearchResult = {
  resource_type: string;
  id: string;
  label: string;
  subtitle: string;
  url: string;
};

type SearchResponse = {
  query: string;
  categories: Record<string, SearchResult[]>;
  total: number;
};

const CATEGORY_META: Record<
  string,
  { label: string; icon: React.ComponentType<{ size?: number }>; color: string }
> = {
  patient: { label: "Patients", icon: Users, color: "#0f6b3e" },
  invoice: { label: "Factures", icon: Receipt, color: "#1a3a5c" },
  lab_order: { label: "Laboratoire", icon: FlaskConical, color: "#7c3aed" },
  imaging_order: { label: "Imagerie", icon: Scan, color: "#b45309" },
  clinical_note: { label: "Notes cliniques", icon: FileText, color: "#475569" },
};

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Global Ctrl+K / Cmd+K shortcut + custom open event
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      } else if (e.key === "Escape" && open) {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", handler);
    // Allow external components (sidebar button) to open the palette
    function openHandler() {
      setOpen(true);
    }
    window.addEventListener("guineecare:open-search", openHandler);
    return () => {
      window.removeEventListener("keydown", handler);
      window.removeEventListener("guineecare:open-search", openHandler);
    };
  }, [open]);

  // Focus input when opening
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery("");
      setResults(null);
      setActiveIndex(0);
    }
  }, [open]);

  // Debounced search
  useEffect(() => {
    if (!open) return;
    const q = query.trim();
    if (q.length < 2) {
      setResults(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const resp = await apiRequest<{ data: SearchResponse }>(
          `/search?q=${encodeURIComponent(q)}&limit=8&max_total=40`,
        );
        setResults(resp.data);
      } catch (e: any) {
        // Silently fail — the user is typing, an error toast would be noisy
        console.error("search error", e);
        setResults({ query: q, categories: {}, total: 0 });
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, open]);

  // Flatten results for keyboard navigation
  const flatResults = useMemo(() => {
    if (!results) return [] as SearchResult[];
    return Object.values(results.categories).flat();
  }, [results]);

  function selectResult(r: SearchResult) {
    setOpen(false);
    // Strip the leading slash since navigate() expects a path without domain
    navigate(r.url);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, flatResults.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && flatResults[activeIndex]) {
      e.preventDefault();
      selectResult(flatResults[activeIndex]);
    }
  }

  if (!open) return null;

  let runningIndex = 0;

  return (
    <div
      className="cmdk-overlay"
      onClick={() => setOpen(false)}
      role="dialog"
      aria-modal="true"
      aria-label="Recherche globale"
    >
      <div
        className="cmdk-modal"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <div className="cmdk-input-row">
          <Search size={18} className="cmdk-search-icon" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIndex(0);
            }}
            placeholder="Rechercher patient, facture, analyse, examen… (Ctrl+K)"
            className="cmdk-input"
          />
          {loading && <span className="cmdk-loading">…</span>}
          <button
            type="button"
            className="cmdk-close"
            onClick={() => setOpen(false)}
            aria-label="Fermer"
          >
            <X size={16} />
          </button>
        </div>

        <div className="cmdk-results">
          {!loading && query.trim().length < 2 && (
            <div className="cmdk-empty">
              Saisissez au moins 2 caractères pour lancer la recherche.
            </div>
          )}
          {!loading && results && results.total === 0 && query.trim().length >= 2 && (
            <div className="cmdk-empty">
              Aucun résultat pour « {results.query} ».
            </div>
          )}
          {results &&
            Object.entries(results.categories).map(([cat, items]) => {
              const meta = CATEGORY_META[cat] || {
                label: cat,
                icon: FileText,
                color: "#475569",
              };
              const Icon = meta.icon;
              return (
                <div key={cat} className="cmdk-category">
                  <div className="cmdk-category-header">
                    <Icon size={14} />
                    <span>{meta.label}</span>
                    <span className="cmdk-category-count">{items.length}</span>
                  </div>
                  {items.map((r) => {
                    const idx = runningIndex++;
                    const isActive = idx === activeIndex;
                    return (
                      <button
                        key={`${cat}-${r.id}`}
                        type="button"
                        className={`cmdk-item ${isActive ? "active" : ""}`}
                        onMouseEnter={() => setActiveIndex(idx)}
                        onClick={() => selectResult(r)}
                      >
                        <div className="cmdk-item-main">
                          <div className="cmdk-item-label">{r.label}</div>
                          <div className="cmdk-item-subtitle">{r.subtitle}</div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              );
            })}
        </div>

        <div className="cmdk-footer">
          <span>
            <kbd>↑</kbd> <kbd>↓</kbd> naviguer
          </span>
          <span>
            <kbd>Enter</kbd> ouvrir
          </span>
          <span>
            <kbd>Esc</kbd> fermer
          </span>
        </div>
      </div>
    </div>
  );
}
