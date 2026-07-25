import { useEffect, useRef, useState } from "react";
import { apiRequest } from "../services/api";
import { Search, X } from "lucide-react";

/**
 * ICD-11 Search Component — v2.9.2
 *
 * Composant de recherche de codes ICD-11 (classification OMS) avec
 * autocomplétion. À intégrer dans les formulaires de diagnostic pour
 * proposer les codes officiels plutôt que de laisser l'utilisateur
 * saisir du texte libre.
 *
 * Usage :
 *   <ICD11Search
 *     value={{ code: diagnosisCode, label: diagnosisLabel }}
 *     onChange={(code, label) => {
 *       setDiagnosisCode(code);
 *       setDiagnosisLabel(label);
 *     }}
 *   />
 *
 * Fonctionnement :
 *   - L'utilisateur tape dans le champ de recherche (code ou libellé)
 *   - Débounce 300ms puis appel GET /api/v1/icd11/search?q=...
 *   - Affiche une liste déroulante avec les 10 premiers résultats
 *   - Au clic sur un résultat, remplit code + libellé
 *   - Effacement possible via bouton ✕
 */

type ICD11Result = {
  code: string;
  label_fr: string;
  label_en: string;
  category: string;
};

type ICD11SearchProps = {
  value: { code: string; label: string };
  onChange: (code: string, label: string) => void;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
};

const CATEGORY_COLORS: Record<string, string> = {
  Infectious: "#dc2626",
  Respiratory: "#0ea5e9",
  Cardiovascular: "#ef4444",
  Digestive: "#f59e0b",
  Endocrine: "#8b5cf6",
  Pregnancy: "#ec4899",
  Perinatal: "#10b981",
  Neurological: "#6366f1",
  Mental: "#a855f7",
  Genitourinary: "#06b6d4",
  Skin: "#84cc16",
  Injury: "#f97316",
  External: "#64748b",
};

function getCategoryColor(cat: string): string {
  return CATEGORY_COLORS[cat] || "#64748b";
}

export function ICD11Search({
  value,
  onChange,
  placeholder = "Rechercher un diagnostic (ex: paludisme, hypertension, 1F03…)",
  disabled = false,
  required = false,
}: ICD11SearchProps) {
  const [query, setQuery] = useState(value.label || "");
  const [results, setResults] = useState<ICD11Result[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Met à jour le champ si la valeur change externellement
  useEffect(() => {
    if (value.label && value.label !== query) {
      setQuery(value.label);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value.code, value.label]);

  // Ferme le dropdown si clic en dehors
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Recherche debounced
  function search(q: string) {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (q.trim().length < 2) {
      setResults([]);
      setShowDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ q, limit: "10" });
        const resp = await apiRequest<{ data: ICD11Result[]; total: number }>(
          `/icd11/search?${params.toString()}`
        );
        setResults(resp.data || []);
        setShowDropdown(true);
        setHighlightIndex(-1);
      } catch {
        setResults([]);
        setShowDropdown(false);
      } finally {
        setLoading(false);
      }
    }, 300);
  }

  function selectResult(r: ICD11Result) {
    onChange(r.code, r.label_fr);
    setQuery(r.label_fr);
    setShowDropdown(false);
    setHighlightIndex(-1);
  }

  function clear() {
    onChange("", "");
    setQuery("");
    setResults([]);
    setShowDropdown(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!showDropdown || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && highlightIndex >= 0) {
      e.preventDefault();
      selectResult(results[highlightIndex]);
    } else if (e.key === "Escape") {
      setShowDropdown(false);
    }
  }

  return (
    <div
      ref={containerRef}
      style={{ position: "relative", width: "100%" }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          background: "var(--card, #fff)",
          border: "1px solid var(--border, #e2e8f0)",
          borderRadius: "var(--radius-md, 6px)",
          padding: "0 10px",
        }}
      >
        <Search
          size={16}
          color="var(--muted, #64748b)"
          style={{ flexShrink: 0 }}
        />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            search(e.target.value);
            // Si l'utilisateur modifie le libellé manuellement, on garde le code
            // uniquement si le libellé correspond toujours à un résultat sélectionné
            if (value.code && e.target.value !== value.label) {
              onChange("", e.target.value);
            }
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setShowDropdown(true)}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          style={{
            flex: 1,
            border: "none",
            outline: "none",
            padding: "10px 0",
            background: "transparent",
            color: "var(--text, #1e293b)",
            fontSize: "14px",
          }}
        />
        {loading && (
          <span
            style={{
              fontSize: "11px",
              color: "var(--muted)",
              flexShrink: 0,
            }}
          >
            …
          </span>
        )}
        {value.code && !disabled && (
          <button
            type="button"
            onClick={clear}
            aria-label="Effacer"
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              color: "var(--muted)",
              padding: "4px",
              display: "flex",
              alignItems: "center",
              flexShrink: 0,
            }}
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Badge du code sélectionné */}
      {value.code && (
        <div
          style={{
            marginTop: "6px",
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            background: "var(--accent-light, #eff6ff)",
            color: "var(--accent, #2563eb)",
            padding: "3px 10px",
            borderRadius: "var(--radius-full, 9999px)",
            fontSize: "12px",
            fontFamily: "monospace",
            fontWeight: 600,
          }}
        >
          ICD-11: {value.code}
        </div>
      )}

      {/* Dropdown des résultats */}
      {showDropdown && results.length > 0 && (
        <div
          role="listbox"
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            marginTop: "4px",
            background: "var(--card, #fff)",
            border: "1px solid var(--border, #e2e8f0)",
            borderRadius: "var(--radius-md, 6px)",
            boxShadow: "var(--shadow-md, 0 4px 12px rgba(0,0,0,0.08))",
            maxHeight: "320px",
            overflowY: "auto",
            zIndex: 1000,
          }}
        >
          {results.map((r, idx) => {
            const catColor = getCategoryColor(r.category);
            const isHighlighted = idx === highlightIndex;
            return (
              <div
                key={r.code}
                role="option"
                aria-selected={isHighlighted}
                onClick={() => selectResult(r)}
                style={{
                  padding: "10px 12px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  background: isHighlighted
                    ? "var(--primary-light, #e8f5ee)"
                    : "transparent",
                  borderBottom:
                    idx < results.length - 1
                      ? "1px solid var(--border-light, #f1f5f9)"
                      : "none",
                  transition: "background 0.1s",
                }}
                onMouseEnter={() => setHighlightIndex(idx)}
              >
                <div
                  style={{
                    fontFamily: "monospace",
                    fontSize: "12px",
                    fontWeight: 700,
                    color: catColor,
                    background: `${catColor}20`,
                    padding: "3px 8px",
                    borderRadius: "var(--radius-sm, 4px)",
                    minWidth: "60px",
                    textAlign: "center",
                    flexShrink: 0,
                  }}
                >
                  {r.code}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: "14px",
                      color: "var(--text, #1e293b)",
                      fontWeight: 500,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {r.label_fr}
                  </div>
                  <div
                    style={{
                      fontSize: "11px",
                      color: "var(--muted, #64748b)",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {r.label_en} · {r.category}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Message si aucun résultat */}
      {showDropdown && !loading && results.length === 0 && query.length >= 2 && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            marginTop: "4px",
            background: "var(--card, #fff)",
            border: "1px solid var(--border, #e2e8f0)",
            borderRadius: "var(--radius-md, 6px)",
            boxShadow: "var(--shadow-md, 0 4px 12px rgba(0,0,0,0.08))",
            padding: "12px",
            color: "var(--muted, #64748b)",
            fontSize: "13px",
            textAlign: "center",
            zIndex: 1000,
          }}
        >
          Aucun code ICD-11 trouvé pour « {query} »
        </div>
      )}
    </div>
  );
}
