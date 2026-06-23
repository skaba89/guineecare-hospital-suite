/**
 * Composant de pagination réutilisable (offset classique).
 *
 * Affiche : [Précédent] [1] [2] ... [N] [Suivant] + "Page X sur Y (Z éléments)"
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

  const btnStyle = (active: boolean): React.CSSProperties => ({
    padding: "6px 10px",
    margin: "0 2px",
    border: `1px solid ${active ? "#0f766e" : "#e5e7eb"}`,
    background: active ? "#0f766e" : "white",
    color: active ? "white" : "#374151",
    borderRadius: 4,
    cursor: loading ? "not-allowed" : "pointer",
    fontSize: 13,
    opacity: loading ? 0.6 : 1,
    minWidth: 32,
  });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 0",
        borderTop: "1px solid #e5e7eb",
        marginTop: 12,
      }}
    >
      <div className="muted" style={{ fontSize: 12 }}>
        Page <strong>{page}</strong> sur {totalPages || 1} · {total} élément{total > 1 ? "s" : ""}
      </div>
      <div style={{ display: "flex", alignItems: "center" }}>
        <button
          style={btnStyle(false)}
          onClick={() => onPageChange(page - 1)}
          disabled={loading || page <= 1}
          title="Page précédente"
        >
          ←
        </button>
        {pages.map((p, idx) =>
          p === "..." ? (
            <span key={`ellipsis-${idx}`} style={{ padding: "0 4px", color: "#9ca3af" }}>
              …
            </span>
          ) : (
            <button
              key={p}
              style={btnStyle(p === page)}
              onClick={() => onPageChange(p)}
              disabled={loading}
            >
              {p}
            </button>
          )
        )}
        <button
          style={btnStyle(false)}
          onClick={() => onPageChange(page + 1)}
          disabled={loading || page >= totalPages}
          title="Page suivante"
        >
          →
        </button>
      </div>
    </div>
  );
}
