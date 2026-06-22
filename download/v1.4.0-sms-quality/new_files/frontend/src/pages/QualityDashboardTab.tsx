import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData } from "../types";
import { showToast } from "../components/Toast";

// ── Types ───────────────────────────────────────────────────────────────────

type Kpi = {
  indicator_id: string;
  indicator_code: string;
  indicator_name: string;
  category: string | null;
  unit: string | null;
  target_value: string | null;
  frequency: string;
  last_value: string | null;
  last_period_start: string | null;
  last_period_end: string | null;
  has_data: boolean;
};

type IncidentsAgg = {
  total: number;
  by_type: { type: string; count: number }[];
  by_severity: { severity: string; count: number }[];
  by_status: { status: string; count: number }[];
  avg_resolution_hours: number | null;
};

type AlertsAgg = {
  open: number;
  acknowledged: number;
  resolved: number;
  recent: any[];
};

type Trend = {
  indicator_code: string;
  indicator_name: string;
  unit: string | null;
  target_value: string | null;
  data_points: { period_start: string; period_end: string; value: string }[];
};

type Dashboard = {
  period_start: string;
  period_end: string;
  facility_id: string | null;
  department_id: string | null;
  kpis: Kpi[];
  incidents: IncidentsAgg;
  alerts: AlertsAgg;
  trends: Trend[];
  thresholds_count: number;
};

const CATEGORY_LABEL: Record<string, string> = {
  SAFETY: "Sécurité",
  EFFICIENCY: "Efficacité",
  PATIENT_EXPERIENCE: "Expérience patient",
  CLINICAL_OUTCOME: "Résultat clinique",
};

const CATEGORY_COLOR: Record<string, string> = {
  SAFETY: "#dc2626",
  EFFICIENCY: "#0ea5e9",
  PATIENT_EXPERIENCE: "#10b981",
  CLINICAL_OUTCOME: "#f59e0b",
};

const INCIDENT_TYPE_LABEL: Record<string, string> = {
  FALL: "Chute",
  MEDICATION_ERROR: "Erreur médicamenteuse",
  NOSOCOMIAL_INFECTION: "Infection nosocomiale",
  EQUIPMENT_FAILURE: "Défaillance équipement",
  OTHER: "Autre",
};

const SEVERITY_LABEL: Record<string, string> = {
  NEAR_MISS: "Presque incident",
  MINOR: "Mineur",
  MODERATE: "Modéré",
  MAJOR: "Majeur",
  CRITICAL: "Critique",
};

const STATUS_LABEL: Record<string, string> = {
  REPORTED: "Signalé",
  UNDER_INVESTIGATION: "En investigation",
  RESOLVED: "Résolu",
  CLOSED: "Clos",
};

// ── Component ───────────────────────────────────────────────────────────────

export function QualityDashboardTab({ lookups }: { lookups: LookupData }) {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [days, setDays] = useState(30);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<Dashboard>(`/quality/dashboard?days=${days}`);
      setDashboard(payload);
    } catch (e: any) {
      setError(e.message || "Impossible de charger le dashboard.");
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSeedDefaults() {
    if (!confirm("Insérer les indicateurs OMS/HAS et seuils par défaut pour votre établissement ?")) return;
    try {
      const result = await apiRequest<{ indicators_created: number; thresholds_created: number }>(
        "/quality/seed-defaults",
        { method: "POST" }
      );
      showToast(
        `${result.indicators_created} indicateur(s) + ${result.thresholds_created} seuil(s) créés.`,
        "success"
      );
      load();
    } catch (e: any) {
      showToast(e.message || "Erreur lors du seed.", "error");
    }
  }

  async function handleCheckThresholds() {
    try {
      const result = await apiRequest<{ raised: number }>(
        "/quality/alerts/check",
        { method: "POST" }
      );
      showToast(`${result.raised} alerte(s) levée(s) par le check.`, "success");
      load();
    } catch (e: any) {
      showToast(e.message || "Erreur lors du check.", "error");
    }
  }

  if (loading) return <div className="muted">Chargement du dashboard…</div>;
  if (error) return <div className="error-message">{error}</div>;
  if (!dashboard) return <div className="muted">Aucune donnée.</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Dashboard qualité — {days} derniers jours</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <select value={days} onChange={(e) => setDays(parseInt(e.target.value, 10))}>
            <option value={7}>7 jours</option>
            <option value={30}>30 jours</option>
            <option value={90}>90 jours</option>
            <option value={365}>1 an</option>
          </select>
          <button className="secondary-button" onClick={handleSeedDefaults} title="Insérer les indicateurs OMS/HAS prédéfinis">
            📚 Seed OMS/HAS
          </button>
          <button className="secondary-button" onClick={handleCheckThresholds} title="Évaluer les seuils sur les mesures récentes">
            🔔 Check seuils
          </button>
        </div>
      </div>

      {/* KPIs summary */}
      <div className="stats-grid">
        <div className="card stat-card">
          <div className="stat-label">Indicateurs suivis</div>
          <div className="stat-value">{dashboard.kpis.length}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Incidents période</div>
          <div className="stat-value">{dashboard.incidents.total}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Alertes ouvertes</div>
          <div className="stat-value stat-error">{dashboard.alerts.open}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Alertes prises en charge</div>
          <div className="stat-value stat-warning">{dashboard.alerts.acknowledged}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Seuils configurés</div>
          <div className="stat-value">{dashboard.thresholds_count}</div>
        </div>
      </div>

      {/* KPIs détaillés */}
      <div className="card">
        <h3>Indicateurs (KPIs)</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Nom</th>
              <th>Catégorie</th>
              <th>Dernière valeur</th>
              <th>Cible</th>
              <th>Unité</th>
              <th>Période</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            {dashboard.kpis.length === 0 ? (
              <tr>
                <td colSpan={8} className="muted" style={{ textAlign: "center", padding: 16 }}>
                  Aucun indicateur. Cliquez sur « Seed OMS/HAS » pour insérer les indicateurs prédéfinis.
                </td>
              </tr>
            ) : (
              dashboard.kpis.map((kpi) => {
                const ratio = _computeRatio(kpi.last_value, kpi.target_value);
                const status = _kpiStatus(ratio, kpi.has_data);
                return (
                  <tr key={kpi.indicator_id}>
                    <td><code>{kpi.indicator_code}</code></td>
                    <td>{kpi.indicator_name}</td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: kpi.category ? CATEGORY_COLOR[kpi.category] : "#64748b",
                          color: "white",
                          fontSize: 10,
                        }}
                      >
                        {kpi.category ? CATEGORY_LABEL[kpi.category] || kpi.category : "—"}
                      </span>
                    </td>
                    <td><strong>{kpi.last_value ?? "—"}</strong></td>
                    <td>{kpi.target_value ?? "—"}</td>
                    <td>{kpi.unit ?? "—"}</td>
                    <td>
                      {kpi.last_period_end
                        ? new Date(kpi.last_period_end).toLocaleDateString("fr-FR")
                        : "—"}
                    </td>
                    <td>
                      <span className={`badge ${status.badge}`}>{status.label}</span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Incidents agrégés */}
      <div className="card">
        <h3>Incidents — agrégats</h3>
        {dashboard.incidents.total === 0 ? (
          <p className="muted">Aucun incident sur la période.</p>
        ) : (
          <>
            <div className="stats-grid" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
              <div>
                <h4>Par type</h4>
                <ul className="legend-list">
                  {dashboard.incidents.by_type.map((it) => (
                    <li key={it.type}>
                      <span className="legend-label">{INCIDENT_TYPE_LABEL[it.type] || it.type}</span>
                      <span className="legend-value">{it.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4>Par sévérité</h4>
                <ul className="legend-list">
                  {dashboard.incidents.by_severity.map((it) => (
                    <li key={it.severity}>
                      <span className="legend-label">{SEVERITY_LABEL[it.severity] || it.severity}</span>
                      <span className="legend-value">{it.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4>Par statut</h4>
                <ul className="legend-list">
                  {dashboard.incidents.by_status.map((it) => (
                    <li key={it.status}>
                      <span className="legend-label">{STATUS_LABEL[it.status] || it.status}</span>
                      <span className="legend-value">{it.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            {dashboard.incidents.avg_resolution_hours !== null && (
              <p className="muted" style={{ marginTop: 12 }}>
                ⏱️ Délai moyen de résolution : <strong>{dashboard.incidents.avg_resolution_hours}h</strong>
              </p>
            )}
          </>
        )}
      </div>

      {/* Tendances */}
      {dashboard.trends.length > 0 && (
        <div className="card">
          <h3>Tendances (5 principaux indicateurs)</h3>
          {dashboard.trends.map((trend) => (
            <div key={trend.indicator_code} style={{ marginBottom: 16 }}>
              <h4 style={{ fontSize: 14, marginBottom: 4 }}>
                {trend.indicator_name} <span className="muted">({trend.indicator_code})</span>
              </h4>
              {trend.data_points.length === 0 ? (
                <p className="muted">Pas de mesure sur la période.</p>
              ) : (
                <TrendChart trend={trend} />
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}

// ── Trend chart (SVG simple, no dependency) ─────────────────────────────────

function TrendChart({ trend }: { trend: Trend }) {
  const W = 600;
  const H = 120;
  const PAD = 30;

  const values = trend.data_points.map((d) => parseFloat(d.value)).filter((v) => !isNaN(v));
  if (values.length < 2) {
    return <p className="muted">Pas assez de mesures pour tracer une tendance.</p>;
  }

  const min = Math.min(...values, parseFloat(trend.target_value || "0") || 0);
  const max = Math.max(...values, parseFloat(trend.target_value || "0") || 0);
  const range = max - min || 1;
  const stepX = (W - 2 * PAD) / Math.max(1, values.length - 1);

  const points = values.map((v, i) => {
    const x = PAD + i * stepX;
    const y = H - PAD - ((v - min) / range) * (H - 2 * PAD);
    return `${x},${y}`;
  });

  const targetY = trend.target_value
    ? H - PAD - ((parseFloat(trend.target_value) - min) / range) * (H - 2 * PAD)
    : null;

  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ maxHeight: 120 }}>
      {/* Target line */}
      {targetY !== null && !isNaN(targetY) && (
        <>
          <line
            x1={PAD} y1={targetY} x2={W - PAD} y2={targetY}
            stroke="#10b981" strokeWidth={1.5} strokeDasharray="4 2"
          />
          <text x={W - PAD} y={targetY - 4} textAnchor="end" fontSize={10} fill="#10b981">
            cible: {trend.target_value}{trend.unit === "%" ? "%" : ""}
          </text>
        </>
      )}
      {/* Trend line */}
      <polyline
        points={points.join(" ")}
        fill="none" stroke="#0f766e" strokeWidth={2}
      />
      {/* Data points */}
      {points.map((p, i) => {
        const [x, y] = p.split(",");
        return <circle key={i} cx={x} cy={y} r={3} fill="#0f766e" />;
      })}
      {/* X-axis labels (first and last only) */}
      <text x={PAD} y={H - 8} fontSize={10} fill="#64748b">
        {trend.data_points[0] ? new Date(trend.data_points[0].period_start).toLocaleDateString("fr-FR") : ""}
      </text>
      <text x={W - PAD} y={H - 8} fontSize={10} fill="#64748b" textAnchor="end">
        {trend.data_points[trend.data_points.length - 1]
          ? new Date(trend.data_points[trend.data_points.length - 1].period_end).toLocaleDateString("fr-FR")
          : ""}
      </text>
    </svg>
  );
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function _toFloat(v: string | null | undefined): number | null {
  if (!v) return null;
  const f = parseFloat(v.replace("%", ""));
  return isNaN(f) ? null : f;
}

function _computeRatio(observed: string | null, target: string | null): number | null {
  const o = _toFloat(observed);
  const t = _toFloat(target);
  if (o === null || t === null || t === 0) return null;
  return o / t;
}

function _kpiStatus(ratio: number | null, hasData: boolean): { badge: string; label: string } {
  if (!hasData) return { badge: "badge-gray", label: "Pas de donnée" };
  if (ratio === null) return { badge: "badge-gray", label: "N/A" };
  if (ratio <= 1.0) return { badge: "badge-green", label: "Atteint" };
  if (ratio <= 1.2) return { badge: "badge-yellow", label: "Léger dépassement" };
  return { badge: "badge-red", label: "Critique" };
}
