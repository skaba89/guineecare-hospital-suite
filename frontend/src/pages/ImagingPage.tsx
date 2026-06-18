import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";

type TabKey = "orders" | "results";

const TABS: { key: TabKey; label: string }[] = [
  { key: "orders", label: "Examens" },
  { key: "results", label: "Résultats" },
];

const ORDER_STATUS_BADGE: Record<string, string> = {
  PENDING: "badge-yellow",
  IN_PROGRESS: "badge-blue",
  COMPLETED: "badge-green",
  CANCELLED: "badge-gray",
};

const ORDER_STATUS_LABEL: Record<string, string> = {
  PENDING: "En attente",
  IN_PROGRESS: "En cours",
  COMPLETED: "Terminé",
  CANCELLED: "Annulé",
};

const RESULT_STATUS_BADGE: Record<string, string> = {
  DRAFT: "badge-gray",
  VALIDATED: "badge-green",
};

const RESULT_STATUS_LABEL: Record<string, string> = {
  DRAFT: "Brouillon",
  VALIDATED: "Validé",
};

const EXAM_TYPES: { value: string; label: string }[] = [
  { value: "RADIOGRAPHY", label: "Radiographie" },
  { value: "CT_SCAN", label: "Scanner" },
  { value: "MRI", label: "IRM" },
  { value: "ULTRASOUND", label: "Échographie" },
  { value: "MAMMOGRAPHY", label: "Mammographie" },
  { value: "SCINTIGRAPHY", label: "Scintigraphie" },
];

const URGENCY_OPTIONS: { value: string; label: string }[] = [
  { value: "ROUTINE", label: "Routine" },
  { value: "URGENT", label: "Urgent" },
  { value: "EMERGENCY", label: "Urgence" },
];

const EXAM_TYPE_LABEL: Record<string, string> = {
  RADIOGRAPHY: "Radiographie",
  CT_SCAN: "Scanner",
  MRI: "IRM",
  ULTRASOUND: "Échographie",
  MAMMOGRAPHY: "Mammographie",
  SCINTIGRAPHY: "Scintigraphie",
};

const URGENCY_LABEL: Record<string, string> = {
  ROUTINE: "Routine",
  URGENT: "Urgent",
  EMERGENCY: "Urgence",
};

export function ImagingPage({ lookups }: { lookups: LookupData }) {
  const [activeTab, setActiveTab] = useState<TabKey>("orders");

  return (
    <section>
      <h1>Imagerie / Radiologie</h1>
      <p className="muted">Gestion des examens d'imagerie et des résultats.</p>

      <div className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`tab-button ${activeTab === tab.key ? "active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "orders" && <OrdersTab lookups={lookups} />}
      {activeTab === "results" && <ResultsTab lookups={lookups} />}
    </section>
  );
}

/* ─── Orders Tab ──────────────────────────────────────────── */

function OrdersTab({ lookups }: { lookups: LookupData }) {
  const [orders, setOrders] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [examTypeFilter, setExamTypeFilter] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [patientId, setPatientId] = useState("");
  const [examType, setExamType] = useState("");
  const [bodyRegion, setBodyRegion] = useState("");
  const [clinicalInfo, setClinicalInfo] = useState("");
  const [urgency, setUrgency] = useState("ROUTINE");

  const options = buildOptions(lookups);

  function getPatientName(patientId: string): string {
    const patient = lookups.patients.find((p) => p.id === patientId);
    if (!patient) return "Inconnu";
    return `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.patient_number || "N/A";
  }

  const loadOrders = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (examTypeFilter) params.set("exam_type", examTypeFilter);
      const qs = params.toString();
      const payload = await apiRequest<any>(`/imaging/orders${qs ? `?${qs}` : ""}`);
      setOrders(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les examens.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, examTypeFilter]);

  useEffect(() => {
    loadOrders();
    const handler = () => loadOrders();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadOrders]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!patientId || !examType) return;
    setSubmitting(true);
    try {
      await apiRequest("/imaging/orders", {
        method: "POST",
        body: JSON.stringify({
          patient_id: patientId,
          exam_type: examType,
          body_region: bodyRegion.trim() || undefined,
          clinical_info: clinicalInfo.trim() || undefined,
          urgency,
        }),
      });
      setPatientId("");
      setExamType("");
      setBodyRegion("");
      setClinicalInfo("");
      setUrgency("ROUTINE");
      setShowForm(false);
      loadOrders();
      showToast("Examen créé avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création de l'examen.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStart(orderId: string) {
    try {
      await apiRequest(`/imaging/orders/${orderId}/start`, { method: "POST" });
      loadOrders();
      showToast("Examen démarré.", "success");
    } catch {
      showToast("Erreur lors du démarrage.", "error");
    }
  }

  async function handleComplete(orderId: string) {
    try {
      await apiRequest(`/imaging/orders/${orderId}/complete`, { method: "POST" });
      loadOrders();
      showToast("Examen complété.", "success");
    } catch {
      showToast("Erreur lors de la complétion.", "error");
    }
  }

  return (
    <>
      <div className="section-header">
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>Examens d'imagerie</h2>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ minWidth: "140px" }}
            >
              <option value="">Tous les statuts</option>
              <option value="PENDING">En attente</option>
              <option value="IN_PROGRESS">En cours</option>
              <option value="COMPLETED">Terminé</option>
              <option value="CANCELLED">Annulé</option>
            </select>
          </label>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <select
              value={examTypeFilter}
              onChange={(e) => setExamTypeFilter(e.target.value)}
              style={{ minWidth: "140px" }}
            >
              <option value="">Tous les types</option>
              {EXAM_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </label>
        </div>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouvel examen"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouvel examen d'imagerie</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Patient
              <select value={patientId} onChange={(e) => setPatientId(e.target.value)} required>
                <option value="">-- Choisir un patient --</option>
                {options.patients.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Type d'examen
              <select value={examType} onChange={(e) => setExamType(e.target.value)} required>
                <option value="">-- Choisir --</option>
                {EXAM_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Région
              <input
                type="text"
                value={bodyRegion}
                onChange={(e) => setBodyRegion(e.target.value)}
                placeholder="Région du corps"
              />
            </label>
            <label className="form-control">
              Urgence
              <select value={urgency} onChange={(e) => setUrgency(e.target.value)}>
                {URGENCY_OPTIONS.map((u) => (
                  <option key={u.value} value={u.value}>{u.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Informations cliniques
              <textarea
                value={clinicalInfo}
                onChange={(e) => setClinicalInfo(e.target.value)}
                placeholder="Contexte clinique, symptômes..."
                rows={3}
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer l'examen"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : error ? (
        <p style={{ color: "crimson" }}>{error}</p>
      ) : orders.length === 0 ? (
        <div className="card">
          <p className="muted">Aucun examen trouvé.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Patient</th>
                  <th>Type d'examen</th>
                  <th>Région</th>
                  <th>Urgence</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {order.created_at ? new Date(order.created_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td style={{ fontWeight: 600 }}>{getPatientName(order.patient_id)}</td>
                    <td>{EXAM_TYPE_LABEL[order.exam_type] || order.exam_type || "—"}</td>
                    <td>{order.body_region || "—"}</td>
                    <td>
                      <span className={`badge ${order.urgency === "EMERGENCY" ? "badge-red" : order.urgency === "URGENT" ? "badge-yellow" : "badge-gray"}`}>
                        {URGENCY_LABEL[order.urgency] || order.urgency || "—"}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${ORDER_STATUS_BADGE[order.status] || "badge-gray"}`}>
                        {ORDER_STATUS_LABEL[order.status] || order.status}
                      </span>
                    </td>
                    <td>
                      {order.status === "PENDING" && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px" }}
                          onClick={() => handleStart(order.id)}
                        >
                          Démarrer
                        </button>
                      )}
                      {order.status === "IN_PROGRESS" && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px" }}
                          onClick={() => handleComplete(order.id)}
                        >
                          Compléter
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}

/* ─── Results Tab ──────────────────────────────────────────── */

function ResultsTab({ lookups }: { lookups: LookupData }) {
  const [results, setResults] = useState<Row[]>([]);
  const [pendingOrders, setPendingOrders] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [orderId, setOrderId] = useState("");
  const [findings, setFindings] = useState("");
  const [conclusion, setConclusion] = useState("");
  const [recommendation, setRecommendation] = useState("");

  function getPatientName(patientId: string): string {
    const patient = lookups.patients.find((p) => p.id === patientId);
    if (!patient) return "Inconnu";
    return `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.patient_number || "N/A";
  }

  const loadResults = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/imaging/results?page_size=1000");
      setResults(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les résultats.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadPendingOrders = useCallback(async () => {
    try {
      const payload = await apiRequest<any>("/imaging/orders?status=COMPLETED&page_size=1000");
      setPendingOrders(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      // Silently fail
    }
  }, []);

  useEffect(() => {
    loadResults();
    const handler = () => loadResults();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadResults]);

  useEffect(() => {
    if (showForm) {
      loadPendingOrders();
    }
  }, [showForm, loadPendingOrders]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!orderId) return;
    setSubmitting(true);
    try {
      await apiRequest("/imaging/results", {
        method: "POST",
        body: JSON.stringify({
          order_id: orderId,
          findings: findings.trim() || undefined,
          conclusion: conclusion.trim() || undefined,
          recommendation: recommendation.trim() || undefined,
        }),
      });
      setOrderId("");
      setFindings("");
      setConclusion("");
      setRecommendation("");
      setShowForm(false);
      loadResults();
      showToast("Résultat créé avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création du résultat.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleValidate(resultId: string) {
    try {
      await apiRequest(`/imaging/results/${resultId}/validate`, { method: "POST" });
      loadResults();
      showToast("Résultat validé.", "success");
    } catch {
      showToast("Erreur lors de la validation.", "error");
    }
  }

  const orderOptions = pendingOrders.map((o) => ({
    value: o.id,
    label: `${EXAM_TYPE_LABEL[o.exam_type] || o.exam_type} — ${o.body_region || o.patient_id}`,
  }));

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Résultats d'imagerie</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouveau résultat"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouveau résultat d'imagerie</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Examen
              <select value={orderId} onChange={(e) => setOrderId(e.target.value)} required>
                <option value="">-- Choisir un examen complété --</option>
                {orderOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Constatations
              <textarea
                value={findings}
                onChange={(e) => setFindings(e.target.value)}
                placeholder="Constatations radiologiques..."
                rows={3}
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Conclusion
              <textarea
                value={conclusion}
                onChange={(e) => setConclusion(e.target.value)}
                placeholder="Conclusion..."
                rows={2}
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Recommandation
              <textarea
                value={recommendation}
                onChange={(e) => setRecommendation(e.target.value)}
                placeholder="Recommandations..."
                rows={2}
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer le résultat"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : error ? (
        <p style={{ color: "crimson" }}>{error}</p>
      ) : results.length === 0 ? (
        <div className="card">
          <p className="muted">Aucun résultat trouvé.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Patient</th>
                  <th>Examen</th>
                  <th>Constatations</th>
                  <th>Conclusion</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result) => (
                  <tr key={result.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {result.created_at ? new Date(result.created_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td style={{ fontWeight: 600 }}>{getPatientName(result.patient_id)}</td>
                    <td>{result.exam_type || "—"}</td>
                    <td>{result.findings || "—"}</td>
                    <td>{result.conclusion || "—"}</td>
                    <td>
                      <span className={`badge ${RESULT_STATUS_BADGE[result.status] || "badge-gray"}`}>
                        {RESULT_STATUS_LABEL[result.status] || result.status}
                      </span>
                    </td>
                    <td>
                      {result.status === "DRAFT" && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px" }}
                          onClick={() => handleValidate(result.id)}
                        >
                          Valider
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
