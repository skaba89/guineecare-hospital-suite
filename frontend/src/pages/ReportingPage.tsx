import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";

type TabKey = "dashboard" | "reports" | "alerts" | "statistics";

const TABS: { key: TabKey; label: string }[] = [
  { key: "dashboard", label: "Tableau de bord" },
  { key: "reports", label: "Rapports nationaux" },
  { key: "alerts", label: "Alertes épidémiques" },
  { key: "statistics", label: "Statistiques SNIS" },
];

const REPORT_STATUS_BADGE: Record<string, string> = {
  DRAFT: "badge-gray",
  SUBMITTED: "badge-blue",
  VALIDATED: "badge-green",
  REJECTED: "badge-red",
};

const REPORT_STATUS_LABEL: Record<string, string> = {
  DRAFT: "Brouillon",
  SUBMITTED: "Soumis",
  VALIDATED: "Validé",
  REJECTED: "Rejeté",
};

const REPORT_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: "MONTHLY", label: "Mensuel" },
  { value: "QUARTERLY", label: "Trimestriel" },
  { value: "ANNUAL", label: "Annuel" },
  { value: "EPIDEMIC_ALERT", label: "Alerte épidémique" },
];

const REPORT_TYPE_LABEL: Record<string, string> = {
  MONTHLY: "Mensuel",
  QUARTERLY: "Trimestriel",
  ANNUAL: "Annuel",
  EPIDEMIC_ALERT: "Alerte épidémique",
};

const ALERT_LEVEL_BADGE: Record<string, string> = {
  WATCH: "badge-yellow",
  WARNING: "badge-yellow",
  ALERT: "badge-red",
  EMERGENCY: "badge-red",
};

const ALERT_LEVEL_LABEL: Record<string, string> = {
  WATCH: "Veille",
  WARNING: "Alerte",
  ALERT: "Alerte",
  EMERGENCY: "Urgence",
};

const ALERT_LEVEL_OPTIONS: { value: string; label: string }[] = [
  { value: "WATCH", label: "Veille" },
  { value: "WARNING", label: "Alerte" },
  { value: "ALERT", label: "Alerte" },
  { value: "EMERGENCY", label: "Urgence" },
];

const STAT_SOURCE_OPTIONS: { value: string; label: string }[] = [
  { value: "SNIS", label: "SNIS" },
  { value: "DHIS2", label: "DHIS2" },
  { value: "MANUAL", label: "Manuel" },
];

const STAT_SOURCE_LABEL: Record<string, string> = {
  SNIS: "SNIS",
  DHIS2: "DHIS2",
  MANUAL: "Manuel",
};

export function ReportingPage({ lookups }: { lookups: LookupData }) {
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");

  return (
    <section>
      <h1>Reporting National</h1>
      <p className="muted">Rapports nationaux, alertes épidémiques et statistiques SNIS.</p>

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

      {activeTab === "dashboard" && <DashboardTab lookups={lookups} />}
      {activeTab === "reports" && <ReportsTab lookups={lookups} />}
      {activeTab === "alerts" && <AlertsTab lookups={lookups} />}
      {activeTab === "statistics" && <StatisticsTab lookups={lookups} />}
    </section>
  );
}

/* ─── Dashboard Tab ──────────────────────────────────────────── */

function DashboardTab({ lookups }: { lookups: LookupData }) {
  const [dashboard, setDashboard] = useState<Row | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/reporting/dashboard");
      setDashboard(payload.data || null);
    } catch {
      setError("Impossible de charger le tableau de bord.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
    const handler = () => loadDashboard();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadDashboard]);

  if (loading) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "32px" }}>
        <div className="spinner" />
        <p className="muted" style={{ marginTop: "12px" }}>Chargement du tableau de bord...</p>
      </div>
    );
  }

  if (error) {
    return <p style={{ color: "crimson" }}>{error}</p>;
  }

  const cards = [
    { label: "Rapports en brouillon", value: dashboard?.draft_reports ?? 0, color: "#6b7280" },
    { label: "Rapports soumis", value: dashboard?.submitted_reports ?? 0, color: "#2563eb" },
    { label: "Rapports validés", value: dashboard?.validated_reports ?? 0, color: "#047857" },
    { label: "Alertes actives", value: dashboard?.active_alerts ?? 0, color: "#b91c1c" },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "16px" }}>
      {cards.map((card) => (
        <div className="card" key={card.label} style={{ textAlign: "center" }}>
          <div style={{ fontSize: "32px", fontWeight: 700, color: card.color }}>{card.value}</div>
          <div className="muted" style={{ marginTop: "8px", fontSize: "14px" }}>{card.label}</div>
        </div>
      ))}
    </div>
  );
}

/* ─── Reports Tab ──────────────────────────────────────────── */

function ReportsTab({ lookups }: { lookups: LookupData }) {
  const [reports, setReports] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [reportType, setReportType] = useState("MONTHLY");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [totalAdmissions, setTotalAdmissions] = useState("");
  const [totalDischarges, setTotalDischarges] = useState("");
  const [totalDeaths, setTotalDeaths] = useState("");
  const [totalBirths, setTotalBirths] = useState("");
  const [totalSurgeries, setTotalSurgeries] = useState("");
  const [totalEmergencyVisits, setTotalEmergencyVisits] = useState("");
  const [bedOccupancyRate, setBedOccupancyRate] = useState("");
  const [averageStayDays, setAverageStayDays] = useState("");
  const [notes, setNotes] = useState("");

  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  const loadReports = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/reporting/national-reports?page_size=1000");
      setReports(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les rapports.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReports();
    const handler = () => loadReports();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadReports]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!periodStart) return;
    setSubmitting(true);
    try {
      await apiRequest("/reporting/national-reports", {
        method: "POST",
        body: JSON.stringify({
          report_type: reportType,
          period_start: periodStart,
          period_end: periodEnd || undefined,
          facility_id: facilityId || undefined,
          total_admissions: totalAdmissions.trim() || undefined,
          total_discharges: totalDischarges.trim() || undefined,
          total_deaths: totalDeaths.trim() || undefined,
          total_births: totalBirths.trim() || undefined,
          total_surgeries: totalSurgeries.trim() || undefined,
          total_emergency_visits: totalEmergencyVisits.trim() || undefined,
          bed_occupancy_rate: bedOccupancyRate.trim() || undefined,
          average_stay_days: averageStayDays.trim() || undefined,
          notes: notes.trim() || undefined,
        }),
      });
      setReportType("MONTHLY");
      setPeriodStart("");
      setPeriodEnd("");
      setTotalAdmissions("");
      setTotalDischarges("");
      setTotalDeaths("");
      setTotalBirths("");
      setTotalSurgeries("");
      setTotalEmergencyVisits("");
      setBedOccupancyRate("");
      setAverageStayDays("");
      setNotes("");
      setShowForm(false);
      loadReports();
      showToast("Rapport créé avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création du rapport.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmitReport(reportId: string) {
    try {
      await apiRequest(`/reporting/national-reports/${reportId}/submit`, { method: "POST" });
      loadReports();
      showToast("Rapport soumis.", "success");
    } catch {
      showToast("Erreur lors de la soumission.", "error");
    }
  }

  async function handleValidate(reportId: string) {
    try {
      await apiRequest(`/reporting/national-reports/${reportId}/validate`, { method: "POST" });
      loadReports();
      showToast("Rapport validé.", "success");
    } catch {
      showToast("Erreur lors de la validation.", "error");
    }
  }

  async function handleReject(reportId: string) {
    try {
      await apiRequest(`/reporting/national-reports/${reportId}/reject`, { method: "POST" });
      loadReports();
      showToast("Rapport rejeté.", "success");
    } catch {
      showToast("Erreur lors du rejet.", "error");
    }
  }

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Rapports nationaux</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouveau rapport"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouveau rapport national</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Type de rapport
              <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
                {REPORT_TYPE_OPTIONS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Début de période
              <input
                type="date"
                value={periodStart}
                onChange={(e) => setPeriodStart(e.target.value)}
                required
              />
            </label>
            <label className="form-control">
              Fin de période
              <input
                type="date"
                value={periodEnd}
                onChange={(e) => setPeriodEnd(e.target.value)}
              />
            </label>
            <label className="form-control">
              Total admissions
              <input
                type="number"
                value={totalAdmissions}
                onChange={(e) => setTotalAdmissions(e.target.value)}
                placeholder="0"
              />
            </label>
            <label className="form-control">
              Total sorties
              <input
                type="number"
                value={totalDischarges}
                onChange={(e) => setTotalDischarges(e.target.value)}
                placeholder="0"
              />
            </label>
            <label className="form-control">
              Total décès
              <input
                type="number"
                value={totalDeaths}
                onChange={(e) => setTotalDeaths(e.target.value)}
                placeholder="0"
              />
            </label>
            <label className="form-control">
              Total naissances
              <input
                type="number"
                value={totalBirths}
                onChange={(e) => setTotalBirths(e.target.value)}
                placeholder="0"
              />
            </label>
            <label className="form-control">
              Total chirurgies
              <input
                type="number"
                value={totalSurgeries}
                onChange={(e) => setTotalSurgeries(e.target.value)}
                placeholder="0"
              />
            </label>
            <label className="form-control">
              Total urgences
              <input
                type="number"
                value={totalEmergencyVisits}
                onChange={(e) => setTotalEmergencyVisits(e.target.value)}
                placeholder="0"
              />
            </label>
            <label className="form-control">
              Taux d'occupation (%)
              <input
                type="text"
                value={bedOccupancyRate}
                onChange={(e) => setBedOccupancyRate(e.target.value)}
                placeholder="0.00"
              />
            </label>
            <label className="form-control">
              Durée moyenne séjour (j)
              <input
                type="text"
                value={averageStayDays}
                onChange={(e) => setAverageStayDays(e.target.value)}
                placeholder="0.0"
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Notes
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Notes complémentaires..."
                rows={2}
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer le rapport"}
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
      ) : reports.length === 0 ? (
        <div className="card">
          <p className="muted">Aucun rapport trouvé.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Période</th>
                  <th>Type</th>
                  <th>Établissement</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {report.period_start ? new Date(report.period_start).toLocaleDateString("fr-FR") : "—"}
                      {report.period_end ? ` — ${new Date(report.period_end).toLocaleDateString("fr-FR")}` : ""}
                    </td>
                    <td>{REPORT_TYPE_LABEL[report.report_type] || report.report_type || "—"}</td>
                    <td>{report.facility_id || "—"}</td>
                    <td>
                      <span className={`badge ${REPORT_STATUS_BADGE[report.status] || "badge-gray"}`}>
                        {REPORT_STATUS_LABEL[report.status] || report.status}
                      </span>
                    </td>
                    <td>
                      {report.status === "DRAFT" && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px" }}
                          onClick={() => handleSubmitReport(report.id)}
                        >
                          Soumettre
                        </button>
                      )}
                      {report.status === "SUBMITTED" && (
                        <>
                          <button
                            className="secondary-button"
                            style={{ padding: "6px 14px", fontSize: "13px" }}
                            onClick={() => handleValidate(report.id)}
                          >
                            Valider
                          </button>
                          <button
                            className="secondary-button"
                            style={{ padding: "6px 14px", fontSize: "13px", marginLeft: "4px", color: "crimson" }}
                            onClick={() => handleReject(report.id)}
                          >
                            Rejeter
                          </button>
                        </>
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

/* ─── Alerts Tab ──────────────────────────────────────────── */

function AlertsTab({ lookups }: { lookups: LookupData }) {
  const [alerts, setAlerts] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [diseaseName, setDiseaseName] = useState("");
  const [caseCount, setCaseCount] = useState("");
  const [alertLevel, setAlertLevel] = useState("WATCH");
  const [region, setRegion] = useState("");
  const [description, setDescription] = useState("");
  const [measuresTaken, setMeasuresTaken] = useState("");

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/reporting/epidemic-alerts?page_size=1000");
      setAlerts(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les alertes épidémiques.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAlerts();
    const handler = () => loadAlerts();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadAlerts]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!diseaseName) return;
    setSubmitting(true);
    try {
      await apiRequest("/reporting/epidemic-alerts", {
        method: "POST",
        body: JSON.stringify({
          disease_name: diseaseName.trim(),
          case_count: caseCount.trim() || undefined,
          alert_level: alertLevel,
          region: region.trim() || undefined,
          description: description.trim() || undefined,
          measures_taken: measuresTaken.trim() || undefined,
        }),
      });
      setDiseaseName("");
      setCaseCount("");
      setAlertLevel("WATCH");
      setRegion("");
      setDescription("");
      setMeasuresTaken("");
      setShowForm(false);
      loadAlerts();
      showToast("Alerte épidémique créée avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création de l'alerte.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleClose(alertId: string) {
    try {
      await apiRequest(`/reporting/epidemic-alerts/${alertId}/close`, { method: "POST" });
      loadAlerts();
      showToast("Alerte clôturée.", "success");
    } catch {
      showToast("Erreur lors de la clôture.", "error");
    }
  }

  const ALERT_STATUS_LABEL: Record<string, string> = {
    ACTIVE: "Active",
    CLOSED: "Clôturée",
  };

  const ALERT_STATUS_BADGE: Record<string, string> = {
    ACTIVE: "badge-red",
    CLOSED: "badge-green",
  };

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Alertes épidémiques</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouvelle alerte"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouvelle alerte épidémique</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Maladie
              <input
                type="text"
                value={diseaseName}
                onChange={(e) => setDiseaseName(e.target.value)}
                placeholder="Nom de la maladie"
                required
              />
            </label>
            <label className="form-control">
              Nombre de cas
              <input
                type="number"
                value={caseCount}
                onChange={(e) => setCaseCount(e.target.value)}
                placeholder="0"
              />
            </label>
            <label className="form-control">
              Niveau d'alerte
              <select value={alertLevel} onChange={(e) => setAlertLevel(e.target.value)}>
                {ALERT_LEVEL_OPTIONS.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Région
              <input
                type="text"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                placeholder="Région concernée"
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Description
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Description de la situation..."
                rows={2}
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Mesures prises
              <textarea
                value={measuresTaken}
                onChange={(e) => setMeasuresTaken(e.target.value)}
                placeholder="Mesures déjà prises..."
                rows={2}
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer l'alerte"}
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
      ) : alerts.length === 0 ? (
        <div className="card">
          <p className="muted">Aucune alerte épidémique trouvée.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Maladie</th>
                  <th>Cas</th>
                  <th>Niveau</th>
                  <th>Région</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td style={{ fontWeight: 600 }}>{alert.disease_name || "—"}</td>
                    <td>{alert.case_count ?? "—"}</td>
                    <td>
                      <span className={`badge ${ALERT_LEVEL_BADGE[alert.alert_level] || "badge-gray"}`}>
                        {ALERT_LEVEL_LABEL[alert.alert_level] || alert.alert_level || "—"}
                      </span>
                    </td>
                    <td>{alert.region || "—"}</td>
                    <td>
                      <span className={`badge ${ALERT_STATUS_BADGE[alert.status] || "badge-gray"}`}>
                        {ALERT_STATUS_LABEL[alert.status] || alert.status}
                      </span>
                    </td>
                    <td>
                      {alert.status === "ACTIVE" && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px" }}
                          onClick={() => handleClose(alert.id)}
                        >
                          Clôturer
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

/* ─── Statistics Tab ──────────────────────────────────────────── */

function StatisticsTab({ lookups }: { lookups: LookupData }) {
  const [stats, setStats] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [category, setCategory] = useState("");
  const [metricName, setMetricName] = useState("");
  const [metricValue, setMetricValue] = useState("");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [unit, setUnit] = useState("");
  const [source, setSource] = useState("SNIS");

  const loadStats = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/reporting/statistics?page_size=1000");
      setStats(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les statistiques.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
    const handler = () => loadStats();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadStats]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!category || !metricName || !metricValue) return;
    setSubmitting(true);
    try {
      await apiRequest("/reporting/statistics", {
        method: "POST",
        body: JSON.stringify({
          category: category.trim(),
          metric_name: metricName.trim(),
          metric_value: metricValue.trim(),
          period_start: periodStart || undefined,
          period_end: periodEnd || undefined,
          unit: unit.trim() || undefined,
          source,
        }),
      });
      setCategory("");
      setMetricName("");
      setMetricValue("");
      setPeriodStart("");
      setPeriodEnd("");
      setUnit("");
      setSource("SNIS");
      setShowForm(false);
      loadStats();
      showToast("Statistique créée avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création de la statistique.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Statistiques SNIS</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouvelle statistique"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouvelle statistique</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Catégorie
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="Catégorie"
                required
              />
            </label>
            <label className="form-control">
              Métrique
              <input
                type="text"
                value={metricName}
                onChange={(e) => setMetricName(e.target.value)}
                placeholder="Nom de la métrique"
                required
              />
            </label>
            <label className="form-control">
              Valeur
              <input
                type="text"
                value={metricValue}
                onChange={(e) => setMetricValue(e.target.value)}
                placeholder="Valeur"
                required
              />
            </label>
            <label className="form-control">
              Début de période
              <input
                type="date"
                value={periodStart}
                onChange={(e) => setPeriodStart(e.target.value)}
              />
            </label>
            <label className="form-control">
              Fin de période
              <input
                type="date"
                value={periodEnd}
                onChange={(e) => setPeriodEnd(e.target.value)}
              />
            </label>
            <label className="form-control">
              Unité
              <input
                type="text"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                placeholder="Unité"
              />
            </label>
            <label className="form-control">
              Source
              <select value={source} onChange={(e) => setSource(e.target.value)}>
                {STAT_SOURCE_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer la statistique"}
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
      ) : stats.length === 0 ? (
        <div className="card">
          <p className="muted">Aucune statistique trouvée.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Catégorie</th>
                  <th>Métrique</th>
                  <th>Valeur</th>
                  <th>Période</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {stats.map((stat) => (
                  <tr key={stat.id}>
                    <td style={{ fontWeight: 600 }}>{stat.category || "—"}</td>
                    <td>{stat.metric_name || "—"}</td>
                    <td>{stat.metric_value ?? "—"}{stat.unit ? ` ${stat.unit}` : ""}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {stat.period_start ? new Date(stat.period_start).toLocaleDateString("fr-FR") : "—"}
                      {stat.period_end ? ` — ${new Date(stat.period_end).toLocaleDateString("fr-FR")}` : ""}
                    </td>
                    <td>
                      <span className="badge badge-blue">
                        {STAT_SOURCE_LABEL[stat.source] || stat.source || "—"}
                      </span>
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
