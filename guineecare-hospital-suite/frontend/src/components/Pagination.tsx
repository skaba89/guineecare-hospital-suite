/**
 * Composant de pagination réutilisable (offset classique).
 *
 * Affiche : [Précédent] [1] [2] ... [N] [Suivant] + "Page X sur Y (Z éléments)"
 *
 * v2.1.0 — Phase 3 : styling cohérent avec le design system (variables CSS),
 * accessible (aria-label, disabled), responsive (wrap sur petit écran).
 *
 * Usage :
 *   <Pagination
 *     page={page}
 *     totalPages={totalPages}
 *     total={total}
 *     onPageChange={setPage}
 *   />
 */
type PaginationProps = {
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
  loading?: boolean;
};

export function Pagination({ page, totalPages, total, onPageChange, loading }: PaginationProps) {
  if (total === 0 && !loading) {
    return <div className="muted" style={{ textAlign: "center", padding: 12 }}>Aucun résultat.</div>;
  }

  // Construire la liste des numéros de page à afficher (max 7 visibles)
  const pages: (number | "...")[] = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push("...");
    const start = Math.max(2, page - 1);
    const end = Math.min(totalPages - 1, page + 1);
    for (let i = start; i <= end; i++) pages.push(i);
    if (page < totalPages - 2) pages.push("...");
    pages.push(totalPages);
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 0",
        borderTop: "1px solid var(--border)",
        marginTop: 12,
        flexWrap: "wrap",
        gap: 8,
      }}
    >
      <div className="muted" style={{ fontSize: 12 }}>
        Page <strong>{page}</strong> sur {totalPages || 1} · {total} élément{total > 1 ? "s" : ""}
      </div>
      <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 2 }}>
        <button
          className="secondary-button"
          style={{ padding: "6px 10px", fontSize: 13, minWidth: 32 }}
          onClick={() => onPageChange(page - 1)}
          disabled={loading || page <= 1}
          aria-label="Page précédente"
        >
          ←
        </button>
        {pages.map((p, idx) =>
          p === "..." ? (
            <span key={`ellipsis-${idx}`} style={{ padding: "0 4px", color: "var(--muted)" }}>
              …
            </span>
          ) : (
            <button
              key={p}
              className={p === page ? "primary-button" : "secondary-button"}
              style={{
                padding: "6px 10px",
                fontSize: 13,
                minWidth: 32,
                margin: "0 1px",
              }}
              onClick={() => onPageChange(p)}
              disabled={loading}
              aria-label={`Page ${p}`}
              aria-current={p === page ? "page" : undefined}
            >
              {p}
            </button>
          )
        )}
        <button
          className="secondary-button"
          style={{ padding: "6px 10px", fontSize: 13, minWidth: 32 }}
          onClick={() => onPageChange(page + 1)}
          disabled={loading || page >= totalPages}
          aria-label="Page suivante"
        >
          →
        </button>
      </div>
    </div>
  );
}
