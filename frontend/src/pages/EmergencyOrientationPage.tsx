import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { Row } from "../types";
import { showToast } from "../components/Toast";

const PRIORITY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  LOW: { label: "Basse", color: "#047857", bg: "#d1fae5" },
  NORMAL: { label: "Normale", color: "#1d4ed8", bg: "#dbeafe" },
  HIGH: { label: "Haute", color: "#c2410c", bg: "#ffedd5" },
  CRITICAL: { label: "Critique", color: "#b91c1c", bg: "#fee2e2" },
};

const ORIENTATION_OPTIONS = [
  { value: "HOSPITALIZATION", label: "Hospitalisation" },
  { value: "CONSULTATION", label: "Consultation" },
  { value: "SORTIE", label: "Sortie" },
  { value: "TRANSFERT", label: "Transfert" },
];

export function EmergencyOrientationPage({ onCreated }: { onCreated: () => void }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [orientVisitId, setOrientVisitId] = useState<string | null>(null);
  const [selectedOrientation, setSelectedOrientation] = useState("HOSPITALIZATION");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/emergency/queue");
      const allVisits = Array.isArray(payload.data) ? payload.data : [];
      // Show only triaged visits (not yet oriented/closed)
      setRows(allVisits.filter((v: Row) => v.status === "TRIAGED"));
    } catch (err) {
      setError("Impossible de charger les données.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const handler = () => load();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, []);

  function openOrient(visitId: string) {
    setOrientVisitId(visitId);
    setSelectedOrientation("HOSPITALIZATION");
    setNotes("");
  }

  function closeOrient() {
    setOrientVisitId(null);
    setSelectedOrientation("HOSPITALIZATION");
    setNotes("");
  }

  async function submitOrientation() {
    if (!orientVisitId) return;
    setSubmitting(true);
    try {
      await apiRequest(`/emergency/visits/${orientVisitId}/orientation`, {
        method: "POST",
        body: JSON.stringify({ orientation: selectedOrientation, notes }),
      });
      closeOrient();
      load();
      onCreated();
      showToast("Orientation enregistrée avec succès.", "success");
    } catch (err) {
      setError("Erreur lors de l'orientation.");
      showToast("Erreur lors de l'orientation.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section>
      <h1>Orientation des urgences</h1>
      <p className="muted">Orientez les patients triés vers le service approprié.</p>

      {loading && (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
          <p className="muted" style={{ marginTop: "12px" }}>Chargement...</p>
        </div>
      )}

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {!loading && rows.length === 0 && (
        <div className="card">
          <p className="muted">Aucun patient trié en attente d'orientation.</p>
        </div>
      )}

      {!loading && rows.length > 0 && (
        <div className="card">
          <h2>Patients triés en attente d'orientation</h2>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Heure d'arrivée</th>
                  <th>Motif</th>
                  <th>Priorité</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((visit: Row) => {
                  const priority = PRIORITY_CONFIG[visit.priority_level] || PRIORITY_CONFIG.NORMAL;
                  return (
                    <tr key={visit.id}>
                      <td>{visit.patient_id || "—"}</td>
                      <td>{visit.arrived_at ? new Date(visit.arrived_at).toLocaleString("fr-FR") : "—"}</td>
                      <td>{visit.chief_complaint || "—"}</td>
                      <td>
                        <span
                          style={{
                            display: "inline-block",
                            padding: "4px 12px",
                            borderRadius: "9999px",
                            fontSize: "13px",
                            fontWeight: 700,
                            color: priority.color,
                            background: priority.bg,
                          }}
                        >
                          {priority.label}
                        </span>
                      </td>
                      <td>
                        <button
                          className="primary-button"
                          style={{ padding: "6px 16px", fontSize: "14px" }}
                          onClick={() => openOrient(visit.id)}
                        >
                          Orienter
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Orientation Modal */}
      {orientVisitId && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.4)",
            display: "grid",
            placeItems: "center",
            zIndex: 1000,
          }}
          onClick={closeOrient}
        >
          <div
            className="card"
            style={{ width: "100%", maxWidth: "480px", margin: "24px" }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2>Orientation du patient</h2>
            <p className="muted">Choisissez la destination du patient</p>

            <div style={{ display: "grid", gap: "10px", marginTop: "16px" }}>
              {ORIENTATION_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setSelectedOrientation(option.value)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    padding: "12px 16px",
                    borderRadius: "10px",
                    border: selectedOrientation === option.value ? "2px solid var(--primary)" : "2px solid var(--border)",
                    background: selectedOrientation === option.value ? "#f0f4ff" : "white",
                    cursor: "pointer",
                    fontWeight: selectedOrientation === option.value ? 700 : 400,
                    textAlign: "left",
                    color: "var(--text)",
                    font: "inherit",
                  }}
                >
                  <span
                    style={{
                      width: "14px",
                      height: "14px",
                      borderRadius: "50%",
                      border: selectedOrientation === option.value ? "4px solid var(--primary)" : "2px solid var(--muted)",
                      flexShrink: 0,
                    }}
                  />
                  {option.label}
                </button>
              ))}
            </div>

            <label className="form-control" style={{ marginTop: "16px" }}>
              Notes
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Notes complémentaires..."
                style={{
                  width: "100%",
                  border: "1px solid var(--border)",
                  borderRadius: "10px",
                  padding: "12px",
                  font: "inherit",
                  background: "white",
                  minHeight: "80px",
                  resize: "vertical",
                }}
              />
            </label>

            <div style={{ display: "flex", gap: "12px", marginTop: "20px" }}>
              <button
                className="primary-button"
                onClick={submitOrientation}
                disabled={submitting}
              >
                {submitting ? "Enregistrement..." : "Confirmer l'orientation"}
              </button>
              <button className="secondary-button" onClick={closeOrient}>
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
