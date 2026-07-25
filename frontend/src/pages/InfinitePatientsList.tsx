import { useState, useMemo } from "react";
import { apiRequest } from "../services/api";
import { showToast } from "../components/Toast";
import { useInfiniteScroll, Sentinel } from "../hooks/useInfiniteScroll";
import { LookupData, Row } from "../types";
import { useT } from "../i18n";
import { User, MapPin, Calendar, RefreshCw, List, Loader2 } from "lucide-react";

/**
 * Infinite Patients List — v2.9.2
 *
 * Démonstration du hook `useInfiniteScroll` appliqué à la liste des patients.
 * Charge automatiquement la page suivante quand l'utilisateur scroll près
 * du bas de la liste (préchargement 200px avant).
 *
 * Comparé à ResourcePage (pagination classique) :
 *   - ✅ UX plus fluide (pas de clic "Page suivante")
 *   - ✅ Append-only : les résultats précédents restent visibles
 *   - ⚠️ Pas de saut direct à une page (recherche par scroll)
 *   - ⚠️ Peut charger beaucoup de données si l'utilisateur scroll beaucoup
 *
 * Recommandation : utiliser pour les listes de consultation rapide (patients,
 * audit logs, notifications). Préférer ResourcePage pour les listes
 * administratives où la navigation par page est utile.
 */

type Patient = Row & {
  first_name: string;
  last_name: string;
  gender: string;
  birth_date: string | null;
  phone: string | null;
  patient_number: string | null;
};

function calculateAge(birthDate: string | null): string {
  if (!birthDate) return "—";
  try {
    const birth = new Date(birthDate);
    const now = new Date();
    let age = now.getFullYear() - birth.getFullYear();
    const m = now.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) age--;
    return `${age} ans`;
  } catch {
    return "—";
  }
}

function getGenderLabel(g: string): string {
  const map: Record<string, string> = {
    M: "Masculin",
    F: "Féminin",
    O: "Autre",
  };
  return map[g] || g || "—";
}

export function InfinitePatientsList({
  lookups,
  search,
  onSearchChange,
  onViewToggle,
}: {
  lookups: LookupData;
  search: string;
  onSearchChange: (s: string) => void;
  onViewToggle: () => void;
}) {
  const t = useT();
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);

  // Hook infinite scroll — charge la page suivante automatiquement
  const { items, total, loading, hasMore, loadMore, error } = useInfiniteScroll<Patient>(
    "/patients",
    {
      pageSize: 20,
      search,
      debounceMs: 300,
    }
  );

  // Calcul de l'âge pour chaque patient (memo pour éviter recompute)
  const patientsWithAge = useMemo(() => {
    return items.map((p) => ({
      ...p,
      id: (p as Row).id,
      _age: calculateAge(p.birth_date as string | null),
    }));
  }, [items]);

  return (
    <div style={{ padding: "20px" }}>
      {/* ── En-tête avec recherche + toggle vue ───────────────── */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
          gap: "16px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: "24px", color: "var(--text)" }}>
            👥 Patients — Vue scroll infini
          </h1>
          <p
            style={{
              margin: "4px 0 0",
              color: "var(--muted)",
              fontSize: "13px",
            }}
          >
            {total > 0 ? `${total} patient(s) — ` : ""}
            {items.length} chargé(s) · scroll pour en charger plus
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <input
            type="search"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Rechercher un patient…"
            style={{
              padding: "8px 12px",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              background: "var(--card)",
              color: "var(--text)",
              fontSize: "14px",
              minWidth: "240px",
            }}
          />
          <button
            onClick={onViewToggle}
            className="btn-secondary"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              whiteSpace: "nowrap",
            }}
            title="Revenir à la vue paginée"
          >
            <List size={16} /> Vue paginée
          </button>
        </div>
      </div>

      {/* ── Erreur ────────────────────────────────────────────── */}
      {error && (
        <div
          style={{
            background: "var(--danger-light)",
            border: "1px solid var(--danger)",
            borderRadius: "var(--radius-md)",
            padding: "12px 16px",
            marginBottom: "16px",
            color: "var(--danger)",
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* ── Liste des patients ────────────────────────────────── */}
      {patientsWithAge.length === 0 && !loading ? (
        <div
          style={{
            padding: "48px",
            textAlign: "center",
            color: "var(--muted)",
            background: "var(--card)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border)",
          }}
        >
          <User size={48} style={{ opacity: 0.3, marginBottom: "12px" }} />
          <div style={{ fontSize: "16px", marginBottom: "4px" }}>
            Aucun patient trouvé
          </div>
          <div style={{ fontSize: "13px" }}>
            {search
              ? `Aucun résultat pour « ${search} »`
              : "Aucun patient dans la base"}
          </div>
        </div>
      ) : (
        <div
          style={{
            background: "var(--card)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border)",
            overflow: "hidden",
          }}
        >
          {patientsWithAge.map((p, idx) => (
            <div
              key={p.id}
              onClick={() => setSelectedPatient(p)}
              style={{
                padding: "12px 16px",
                borderBottom:
                  idx < patientsWithAge.length - 1
                    ? "1px solid var(--border-light)"
                    : "none",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                transition: "background 0.1s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--primary-light)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
              }}
            >
              {/* Avatar initiales */}
              <div
                style={{
                  width: "40px",
                  height: "40px",
                  borderRadius: "var(--radius-full)",
                  background: "var(--primary)",
                  color: "white",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "14px",
                  fontWeight: 600,
                  flexShrink: 0,
                }}
              >
                {(p.first_name?.[0] || "?") + (p.last_name?.[0] || "")}
              </div>

              {/* Infos patient */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: "14px",
                    fontWeight: 600,
                    color: "var(--text)",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {p.first_name} {p.last_name}
                </div>
                <div
                  style={{
                    fontSize: "12px",
                    color: "var(--muted)",
                    display: "flex",
                    gap: "12px",
                    flexWrap: "wrap",
                  }}
                >
                  <span>🆔 {p.patient_number || "—"}</span>
                  <span>👤 {getGenderLabel(p.gender)}</span>
                  <span>
                    <Calendar size={11} style={{ verticalAlign: "middle" }} />{" "}
                    {(p as any)._age}
                  </span>
                  {p.phone && (
                    <span>
                      <MapPin size={11} style={{ verticalAlign: "middle" }} />{" "}
                      {p.phone}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* ── Indicateur de chargement ───────────────────────── */}
          {loading && (
            <div
              style={{
                padding: "16px",
                textAlign: "center",
                color: "var(--muted)",
                fontSize: "13px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
              }}
            >
              <Loader2 size={16} className="spin" />
              Chargement de plus de patients…
            </div>
          )}

          {/* ── Indicateur fin de liste ────────────────────────── */}
          {!hasMore && items.length > 0 && !loading && (
            <div
              style={{
                padding: "16px",
                textAlign: "center",
                color: "var(--muted)",
                fontSize: "12px",
                background: "var(--bg)",
              }}
            >
              ✓ Tous les patients chargés ({items.length}/{total})
            </div>
          )}

          {/* ── Sentinel — déclenche loadMore quand visible ────── */}
          {!loading && hasMore && <Sentinel onVisible={loadMore} />}
        </div>
      )}

      {/* ── Patient sélectionné (modal simple) ────────────────── */}
      {selectedPatient && (
        <div
          onClick={() => setSelectedPatient(null)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="card"
            style={{
              padding: "24px",
              maxWidth: "480px",
              width: "90%",
              background: "var(--card)",
              borderRadius: "var(--radius-lg)",
            }}
          >
            <h3 style={{ marginTop: 0, color: "var(--text)" }}>
              {selectedPatient.first_name} {selectedPatient.last_name}
            </h3>
            <div style={{ fontSize: "14px", color: "var(--text-secondary)" }}>
              <p>🆔 N° patient : {selectedPatient.patient_number || "—"}</p>
              <p>👤 Sexe : {getGenderLabel(selectedPatient.gender)}</p>
              <p>
                <Calendar size={14} style={{ verticalAlign: "middle" }} /> Âge :{" "}
                {calculateAge(selectedPatient.birth_date)}
              </p>
              {selectedPatient.phone && (
                <p>📞 Téléphone : {selectedPatient.phone}</p>
              )}
            </div>
            <button
              onClick={() => setSelectedPatient(null)}
              className="btn-primary"
              style={{ marginTop: "16px", width: "100%" }}
            >
              Fermer
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
