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

export function EmergencyTriagePage({ onCreated }: { onCreated: () => void }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [triageVisitId, setTriageVisitId] = useState<string | null>(null);
  const [selectedPriority, setSelectedPriority] = useState("NORMAL");
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/emergency/queue");
      const allVisits = Array.isArray(payload.data) ? payload.data : [];
      // Show visits that are waiting (not yet triaged)
      setRows(allVisits.filter((v: Row) => v.status === "WAITING" || v.status === "ARRIVED" || !v.status || v.status === "TRIAGED"));
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

  function openTriage(visitId: string, currentPriority: string) {
    setTriageVisitId(visitId);
    setSelectedPriority(currentPriority || "NORMAL");
  }

  function closeTriage() {
    setTriageVisitId(null);
    setSelectedPriority("NORMAL");
  }

  async function submitTriage() {
    if (!triageVisitId) return;
    setSubmitting(true);
    try {
      await apiRequest(`/emergency/visits/${triageVisitId}/triage`, {
        method: "POST",
        body: JSON.stringify({ priority_level: selectedPriority }),
      });
      closeTriage();
      load();
      onCreated();
      showToast("Triage enregistré avec succès.", "success");
    } catch (err) {
      setError("Erreur lors du triage.");
      showToast("Erreur lors du triage.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const waitingRows = rows.filter((v: Row) => v.status !== "TRIAGED" && v.status !== "CLOSED");
  const triagedRows = rows.filter((v: Row) => v.status === "TRIAGED");

  return (
    <section>
      <h1>Triage des urgences</h1>
      <p className="muted">Assignez un niveau de priorité aux patients en attente.</p>

      {loading && (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
          <p className="muted" style={{ marginTop: "12px" }}>Chargement...</p>
        </div>
      )}

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {!loading && waitingRows.length === 0 && (
        <div className="card">
          <p className="muted">Aucun patient en attente de triage.</p>
        </div>
      )}

      {!loading && waitingRows.length > 0 && (
        <div className="card">
          <h2>Patients en attente de triage</h2>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Heure d'arrivée</th>
                  <th>Motif</th>
                  <th>Priorité actuelle</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {waitingRows.map((visit: Row) => {
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
                          onClick={() => openTriage(visit.id, visit.priority_level)}
                        >
                          Trier
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

      {!loading && triagedRows.length > 0 && (
        <div className="card" style={{ marginTop: "18px" }}>
          <h2>Patients déjà triés</h2>
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
                {triagedRows.map((visit: Row) => {
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
                          className="secondary-button"
                          style={{ padding: "6px 16px", fontSize: "14px" }}
                          onClick={() => openTriage(visit.id, visit.priority_level)}
                        >
                          Re-trier
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

      {/* Triage Modal */}
      {triageVisitId && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.4)",
            display: "grid",
            placeItems: "center",
            zIndex: 1000,
          }}
          onClick={closeTriage}
        >
          <div
            className="card"
            style={{ width: "100%", maxWidth: "480px", margin: "24px" }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2>Triage du patient</h2>
            <p className="muted">Sélectionnez le niveau de priorité</p>

            <div style={{ display: "grid", gap: "10px", marginTop: "16px" }}>
              {Object.entries(PRIORITY_CONFIG).map(([value, config]) => (
                <button
                  key={value}
                  onClick={() => setSelectedPriority(value)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    padding: "12px 16px",
                    borderRadius: "10px",
                    border: selectedPriority === value ? `2px solid ${config.color}` : "2px solid var(--border)",
                    background: selectedPriority === value ? config.bg : "white",
                    cursor: "pointer",
                    fontWeight: selectedPriority === value ? 700 : 400,
                    textAlign: "left",
                  }}
                >
                  <span
                    style={{
                      width: "14px",
                      height: "14px",
                      borderRadius: "50%",
                      background: config.color,
                      flexShrink: 0,
                    }}
                  />
                  <span style={{ color: config.color }}>{config.label}</span>
                </button>
              ))}
            </div>

            <div style={{ display: "flex", gap: "12px", marginTop: "20px" }}>
              <button
                className="primary-button"
                onClick={submitTriage}
                disabled={submitting}
              >
                {submitting ? "Enregistrement..." : "Confirmer le triage"}
              </button>
              <button className="secondary-button" onClick={closeTriage}>
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
