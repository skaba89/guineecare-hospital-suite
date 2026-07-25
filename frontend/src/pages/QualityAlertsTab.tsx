import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData } from "../types";
import { showToast } from "../components/Toast";

// ── Types ───────────────────────────────────────────────────────────────────

type QualityAlert = {
  id: string;
  created_at: string;
  facility_id: string | null;
  department_id: string | null;
  threshold_id: string | null;
  measurement_id: string | null;
  notification_id: string | null;
  indicator_id: string | null;
  status: string;
  severity: string;
  title: string;
  message: string | null;
  observed_value: string | null;
  threshold_value: string | null;
  comparator: string | null;
  assigned_to: string | null;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_note: string | null;
  closed_at: string | null;
};

type Threshold = {
  id: string;
  created_at: string;
  updated_at: string;
  facility_id: string | null;
  department_id: string | null;
  indicator_id: string;
  comparator: string;
  threshold_value: string;
  severity: string;
  alert_message: string | null;
  notify_roles: string[];
  channels: string[];
  enabled: boolean;
  cooldown_hours: number;
};

const SEVERITY_BADGE: Record<string, string> = {
  LOW: "badge-gray",
  MEDIUM: "badge-yellow",
  HIGH: "badge-orange",
  CRITICAL: "badge-red",
};

const SEVERITY_LABEL: Record<string, string> = {
  LOW: "Faible",
  MEDIUM: "Moyenne",
  HIGH: "Haute",
  CRITICAL: "Critique",
};

const STATUS_BADGE: Record<string, string> = {
  OPEN: "badge-red",
  ACKNOWLEDGED: "badge-yellow",
  RESOLVED: "badge-green",
  CLOSED: "badge-gray",
};

const STATUS_LABEL: Record<string, string> = {
  OPEN: "Ouverte",
  ACKNOWLEDGED: "Prise en charge",
  RESOLVED: "Résolue",
  CLOSED: "Clos",
};

const COMPARATOR_LABEL: Record<string, string> = {
  LT: "<",
  LE: "≤",
  GT: ">",
  GE: "≥",
  EQ: "=",
};

type TabKey = "alerts" | "thresholds";

// ── Component ───────────────────────────────────────────────────────────────

export function QualityAlertsTab({ lookups }: { lookups: LookupData }) {
  const [subTab, setSubTab] = useState<TabKey>("alerts");

  return (
    <>
      <div className="tab-bar">
        <button
          className={`tab-button ${subTab === "alerts" ? "active" : ""}`}
          onClick={() => setSubTab("alerts")}
        >
          Alertes
        </button>
        <button
          className={`tab-button ${subTab === "thresholds" ? "active" : ""}`}
          onClick={() => setSubTab("thresholds")}
        >
          Seuils
        </button>
      </div>

      {subTab === "alerts" && <AlertsList />}
      {subTab === "thresholds" && <ThresholdsList lookups={lookups} />}
    </>
  );
}

// ── Alerts List ─────────────────────────────────────────────────────────────

function AlertsList() {
  const [alerts, setAlerts] = useState<QualityAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [resolveTarget, setResolveTarget] = useState<QualityAlert | null>(null);
  const [resolutionNote, setResolutionNote] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const path = statusFilter
        ? `/quality/alerts?status=${statusFilter}&page_size=100`
        : `/quality/alerts?page_size=100`;
      const payload = await apiRequest<{ data: QualityAlert[]; total: number }>(path);
      setAlerts(payload.data || []);
    } catch {
      setError("Impossible de charger les alertes.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAck(a: QualityAlert) {
    try {
      await apiRequest(`/quality/alerts/${a.id}/acknowledge`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      load();
      showToast("Alerte prise en charge.", "success");
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    }
  }

  async function handleResolve() {
    if (!resolveTarget || !resolutionNote.trim()) return;
    try {
      await apiRequest(`/quality/alerts/${resolveTarget.id}/resolve`, {
        method: "POST",
        body: JSON.stringify({ resolution_note: resolutionNote }),
      });
      setResolveTarget(null);
      setResolutionNote("");
      load();
      showToast("Alerte résolue.", "success");
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    }
  }

  async function handleClose(a: QualityAlert) {
    if (!confirm("Clôturer cette alerte ?")) return;
    try {
      await apiRequest(`/quality/alerts/${a.id}/close`, { method: "POST" });
      load();
      showToast("Alerte clôturée.", "success");
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    }
  }

  if (loading) return <div className="muted">Chargement…</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Alertes qualité ({alerts.length})</h2>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Toutes</option>
          <option value="OPEN">Ouvertes</option>
          <option value="ACKNOWLEDGED">Prises en charge</option>
          <option value="RESOLVED">Résolues</option>
          <option value="CLOSED">Closes</option>
        </select>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Sévérité</th>
              <th>Titre</th>
              <th>Mesure</th>
              <th>Seuil</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 ? (
              <tr><td colSpan={7} className="muted" style={{ textAlign: "center" }}>Aucune alerte.</td></tr>
            ) : (
              alerts.map((a) => (
                <tr key={a.id}>
                  <td>{new Date(a.created_at).toLocaleString("fr-FR")}</td>
                  <td>
                    <span className={`badge ${SEVERITY_BADGE[a.severity] || "badge-gray"}`}>
                      {SEVERITY_LABEL[a.severity] || a.severity}
                    </span>
                  </td>
                  <td>
                    <strong>{a.title}</strong>
                    {a.message && (
                      <div className="muted" style={{ fontSize: 12 }}>{a.message}</div>
                    )}
                  </td>
                  <td><strong>{a.observed_value}</strong></td>
                  <td>
                    {a.comparator && a.threshold_value
                      ? `${COMPARATOR_LABEL[a.comparator] || a.comparator} ${a.threshold_value}`
                      : "—"}
                  </td>
                  <td>
                    <span className={`badge ${STATUS_BADGE[a.status] || "badge-gray"}`}>
                      {STATUS_LABEL[a.status] || a.status}
                    </span>
                  </td>
                  <td>
                    {a.status === "OPEN" && (
                      <button className="action-button" onClick={() => handleAck(a)} title="Prendre en charge">
                        👁️
                      </button>
                    )}
                    {(a.status === "OPEN" || a.status === "ACKNOWLEDGED") && (
                      <button
                        className="action-button"
                        onClick={() => { setResolveTarget(a); setResolutionNote(""); }}
                        title="Résoudre"
                      >
                        ✅
                      </button>
                    )}
                    {a.status === "RESOLVED" && (
                      <button className="action-button" onClick={() => handleClose(a)} title="Clôturer">
                        🗄️
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {resolveTarget && (
        <div className="modal-overlay" onClick={() => setResolveTarget(null)}>
          <div className="card modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>Résoudre l'alerte</h3>
            <p><strong>{resolveTarget.title}</strong></p>
            <p className="muted">Mesure: {resolveTarget.observed_value} — Seuil: {resolveTarget.threshold_value}</p>
            <label>
              Note de résolution *
              <textarea
                value={resolutionNote}
                onChange={(e) => setResolutionNote(e.target.value)}
                rows={4}
                placeholder="Décrivez l'action corrective mise en place…"
                required
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" onClick={handleResolve} disabled={!resolutionNote.trim()}>
                Marquer résolue
              </button>
              <button className="secondary-button" onClick={() => setResolveTarget(null)}>
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── Thresholds List ─────────────────────────────────────────────────────────

function ThresholdsList({ lookups }: { lookups: LookupData }) {
  const [thresholds, setThresholds] = useState<Threshold[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [indicatorId, setIndicatorId] = useState("");
  const [comparator, setComparator] = useState("GT");
  const [thresholdValue, setThresholdValue] = useState("");
  const [severity, setSeverity] = useState("HIGH");
  const [cooldownHours, setCooldownHours] = useState(24);
  const [alertMessage, setAlertMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<{ data: Threshold[]; total: number }>(
        "/quality/thresholds?page_size=100"
      );
      setThresholds(payload.data || []);
    } catch {
      setError("Impossible de charger les seuils.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!indicatorId || !thresholdValue) return;
    setSubmitting(true);
    try {
      await apiRequest("/quality/thresholds", {
        method: "POST",
        body: JSON.stringify({
          indicator_id: indicatorId,
          comparator,
          threshold_value: thresholdValue,
          severity,
          cooldown_hours: cooldownHours,
          alert_message: alertMessage || undefined,
          channels: ["in_app"],
          notify_roles: ["ADMIN"],
        }),
      });
      setShowForm(false);
      setIndicatorId(""); setThresholdValue(""); setAlertMessage("");
      load();
      showToast("Seuil créé avec succès.", "success");
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(t: Threshold) {
    if (!confirm(`Supprimer ce seuil ?`)) return;
    try {
      await apiRequest(`/quality/thresholds/${t.id}`, { method: "DELETE" });
      load();
      showToast("Seuil supprimé.", "success");
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    }
  }

  async function handleToggle(t: Threshold) {
    try {
      await apiRequest(`/quality/thresholds/${t.id}`, {
        method: "PATCH",
        body: JSON.stringify({ enabled: !t.enabled }),
      });
      load();
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    }
  }

  if (loading) return <div className="muted">Chargement…</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Seuils d'alerte ({thresholds.length})</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "+ Nouveau seuil"}
        </button>
      </div>

      {showForm && (
        <form className="card form-card" onSubmit={handleSubmit}>
          <h3>Nouveau seuil d'alerte</h3>
          <div className="form-grid">
            <label>
              Indicateur *
              <select value={indicatorId} onChange={(e) => setIndicatorId(e.target.value)} required>
                <option value="">— Sélectionner —</option>
                {lookups.indicators?.map((ind: any) => (
                  <option key={ind.id} value={ind.id}>
                    {ind.code} — {ind.name}
                  </option>
                )) || []}
              </select>
            </label>
            <label>
              Comparateur *
              <select value={comparator} onChange={(e) => setComparator(e.target.value)}>
                <option value="GT">&gt; (supérieur à)</option>
                <option value="GE">≥ (supérieur ou égal)</option>
                <option value="LT">&lt; (inférieur à)</option>
                <option value="LE">≤ (inférieur ou égal)</option>
                <option value="EQ">= (égal à)</option>
              </select>
            </label>
            <label>
              Valeur seuil *
              <input value={thresholdValue} onChange={(e) => setThresholdValue(e.target.value)} placeholder="5" required />
            </label>
            <label>
              Sévérité
              <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
                <option value="LOW">Faible</option>
                <option value="MEDIUM">Moyenne</option>
                <option value="HIGH">Haute</option>
                <option value="CRITICAL">Critique</option>
              </select>
            </label>
            <label>
              Cooldown (heures)
              <input
                type="number"
                value={cooldownHours}
                onChange={(e) => setCooldownHours(parseInt(e.target.value, 10) || 24)}
                min="0" max="720"
              />
            </label>
          </div>
          <label>
            Message d'alerte <span className="muted">(optionnel — utilisez {`{{value}}`} et {`{{threshold}}`})</span>
            <textarea
              value={alertMessage}
              onChange={(e) => setAlertMessage(e.target.value)}
              rows={2}
              placeholder="Seuil franchi : {{value}} (cible : {{threshold}})"
            />
          </label>
          <div className="form-actions">
            <button type="submit" className="primary-button" disabled={submitting}>
              {submitting ? "Création…" : "Créer le seuil"}
            </button>
            <button type="button" className="secondary-button" onClick={() => setShowForm(false)}>
              Annuler
            </button>
          </div>
        </form>
      )}

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Indicateur</th>
              <th>Comparateur</th>
              <th>Seuil</th>
              <th>Sévérité</th>
              <th>Cooldown</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {thresholds.length === 0 ? (
              <tr><td colSpan={7} className="muted" style={{ textAlign: "center" }}>Aucun seuil configuré.</td></tr>
            ) : (
              thresholds.map((t) => (
                <tr key={t.id}>
                  <td><code>{t.indicator_id}</code></td>
                  <td>{COMPARATOR_LABEL[t.comparator] || t.comparator}</td>
                  <td><strong>{t.threshold_value}</strong></td>
                  <td>
                    <span className={`badge ${SEVERITY_BADGE[t.severity] || "badge-gray"}`}>
                      {SEVERITY_LABEL[t.severity] || t.severity}
                    </span>
                  </td>
                  <td>{t.cooldown_hours}h</td>
                  <td>
                    <span className={`badge ${t.enabled ? "badge-green" : "badge-gray"}`}>
                      {t.enabled ? "Actif" : "Inactif"}
                    </span>
                  </td>
                  <td>
                    <button className="action-button" onClick={() => handleToggle(t)} title="Activer/Désactiver">
                      {t.enabled ? "🔴" : "🟢"}
                    </button>
                    <button className="action-button" onClick={() => handleDelete(t)} title="Supprimer">
                      🗑️
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
