import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData } from "../types";
import { useT } from "../i18n";
import { useNavigate } from "react-router-dom";
import { Building2, Users, ClipboardList, BedDouble, AlertTriangle, FlaskConical, Receipt, TrendingUp, Activity, FileText, RefreshCw } from "lucide-react";

type NationalData = {
  filters: Record<string, unknown>;
  facilities_count: number;
  indicators: {
    total_patients: number;
    total_admissions: number;
    active_admissions: number;
    total_consultations: number;
    total_emergencies: number;
    avg_emergency_wait_min: number;
    active_stays: number;
    total_beds: number;
    occupied_beds: number;
    available_beds: number;
    bed_occupancy_rate: number;
    total_pregnancies: number;
    total_deliveries: number;
    total_products: number;
    total_stock_value_gnf: number;
    low_stock_count: number;
    total_lab_orders: number;
    validated_lab_orders: number;
    pending_lab_orders: number;
    total_invoices: number;
    paid_invoices: number;
    unpaid_invoices: number;
    total_revenue_gnf: number;
    total_outstanding_gnf: number;
  };
  by_region: Array<{ region: string; facilities_count: number; patients_count: number }>;
  by_facility_type: Array<{ category: string; count: number }>;
  generated_at: string;
};

function _fmtGNF(value: number): string {
  return new Intl.NumberFormat("fr-FR").format(value) + " GNF";
}

function _fmtNum(value: number): string {
  return new Intl.NumberFormat("fr-FR").format(value);
}

export function NationalPilotagePage(_: { lookups: LookupData }) {
  const t = useT();
  const navigate = useNavigate();
  const [data, setData] = useState<NationalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [region, setRegion] = useState("");
  const [period, setPeriod] = useState("");

  const load = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (region) params.set("region", region);
      if (period) params.set("period", period);
      const sep = params.toString() ? "?" : "";
      const result = await apiRequest<NationalData>(`/reporting/national${sep}${params.toString()}`);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [region, period]);

  useEffect(() => {
    load();
  }, [load]);

  const kpis = data?.indicators;
  const bedRate = kpis?.bed_occupancy_rate ?? 0;

  const kpiCards = [
    { label: "Établissements", value: _fmtNum(data?.facilities_count ?? 0), icon: Building2, color: "#2563eb", bg: "#eff6ff", onClick: () => navigate("/facilities") },
    { label: "Patients", value: _fmtNum(kpis?.total_patients ?? 0), icon: Users, color: "#0f6b3e", bg: "#e8f5ee", onClick: () => navigate("/patients") },
    { label: "Admissions", value: _fmtNum(kpis?.total_admissions ?? 0), icon: ClipboardList, color: "#7c3aed", bg: "#f5f3ff", onClick: () => navigate("/admissions") },
    { label: "Urgences", value: _fmtNum(kpis?.total_emergencies ?? 0), icon: AlertTriangle, color: "#dc2626", bg: "#fef2f2", onClick: () => navigate("/emergency") },
    { label: "Hospitalisés", value: _fmtNum(kpis?.active_stays ?? 0), icon: BedDouble, color: "#0f6b3e", bg: "#e8f5ee", onClick: () => navigate("/hospitalization") },
    { label: "Occupation lits", value: `${bedRate}%`, icon: Activity, color: bedRate > 85 ? "#dc2626" : "#0f6b3e", bg: bedRate > 85 ? "#fef2f2" : "#e8f5ee" },
    { label: "Examens labo", value: _fmtNum(kpis?.total_lab_orders ?? 0), icon: FlaskConical, color: "#d97706", bg: "#fffbeb", onClick: () => navigate("/lab") },
    { label: "Recettes", value: _fmtGNF(kpis?.total_revenue_gnf ?? 0), icon: Receipt, color: "#0f6b3e", bg: "#e8f5ee", onClick: () => navigate("/billing") },
    { label: "Créances", value: _fmtGNF(kpis?.total_outstanding_gnf ?? 0), icon: TrendingUp, color: "#dc2626", bg: "#fef2f2" },
    { label: "Ruptures stock", value: _fmtNum(kpis?.low_stock_count ?? 0), icon: AlertTriangle, color: kpis?.low_stock_count ? "#dc2626" : "#0f6b3e", bg: kpis?.low_stock_count ? "#fef2f2" : "#e8f5ee", onClick: () => navigate("/pharmacy") },
    { label: "Accouchements", value: _fmtNum(kpis?.total_deliveries ?? 0), icon: Users, color: "#7c3aed", bg: "#f5f3ff", onClick: () => navigate("/maternity") },
    { label: "Factures impayées", value: _fmtNum(kpis?.unpaid_invoices ?? 0), icon: FileText, color: "#d97706", bg: "#fffbeb" },
  ];

  return (
    <section>
      {/* Hero */}
      <div className="card" style={{ background: "linear-gradient(135deg, #0b2e58 0%, #1a4a7a 100%)", color: "white", padding: "32px", marginBottom: "24px" }}>
        <p style={{ textTransform: "uppercase", fontSize: "12px", letterSpacing: "2px", color: "#f2c94c", fontWeight: 700, marginBottom: "8px" }}>
          Pilotage national
        </p>
        <h1 style={{ margin: "0 0 12px", fontSize: "28px", color: "white" }}>
          Vue ministérielle de la plateforme GuinéeCare
        </h1>
        <p style={{ color: "rgba(255,255,255,0.8)", margin: 0, lineHeight: 1.6 }}>
          Indicateurs sanitaires agrégés en temps réel — {data?.facilities_count ?? 0} établissement(s) suivi(s).
          Données anonymisées, conformes à la confidentialité médicale.
        </p>
      </div>

      {/* Filtres */}
      <div style={{ display: "flex", gap: "12px", marginBottom: "20px", flexWrap: "wrap", alignItems: "end" }}>
        <label className="toolbar-control" style={{ minWidth: 200 }}>
          <span>Région</span>
          <select value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="">Toutes les régions</option>
            <option value="Conakry">Conakry</option>
            <option value="Boké">Boké</option>
            <option value="Kindia">Kindia</option>
            <option value="Labé">Labé</option>
            <option value="Mamou">Mamou</option>
            <option value="Faranah">Faranah</option>
            <option value="Kankan">Kankan</option>
            <option value="Nzérékoré">Nzérékoré</option>
          </select>
        </label>
        <label className="toolbar-control" style={{ minWidth: 150 }}>
          <span>Période</span>
          <select value={period} onChange={(e) => setPeriod(e.target.value)}>
            <option value="">Toutes périodes</option>
            <option value="2026">2026</option>
            <option value="202601">Jan 2026</option>
            <option value="202602">Fév 2026</option>
            <option value="202603">Mar 2026</option>
            <option value="202604">Avr 2026</option>
            <option value="202605">Mai 2026</option>
            <option value="202606">Juin 2026</option>
            <option value="202607">Juil 2026</option>
          </select>
        </label>
        <button className="btn btn-outline btn-sm" onClick={load} disabled={loading} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
          <RefreshCw size={14} className={loading ? "spin" : ""} />
          Actualiser
        </button>
        {data && (
          <span className="muted" style={{ fontSize: 12, marginLeft: "auto" }}>
            Généré le {new Date(data.generated_at).toLocaleString("fr-FR")}
          </span>
        )}
      </div>

      {/* Loading */}
      {loading && !data && (
        <div className="card" style={{ textAlign: "center", padding: "48px" }}>
          <div className="spinner" />
          <p className="muted" style={{ marginTop: "16px" }}>Chargement des indicateurs nationaux…</p>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="error-state">
          <p className="error-state-title">Erreur de chargement</p>
          <p className="error-state-description">{error}</p>
          <div className="error-state-action">
            <button className="btn btn-primary btn-sm" onClick={load}>Réessayer</button>
          </div>
        </div>
      )}

      {/* KPI Grid */}
      {data && !loading && (
        <>
          <div className="kpi-grid">
            {kpiCards.map((kpi) => {
              const Icon = kpi.icon;
              return (
                <div
                  key={kpi.label}
                  className={`kpi-card ${kpi.onClick ? "kpi-card-clickable" : ""}`}
                  onClick={kpi.onClick}
                  role={kpi.onClick ? "button" : undefined}
                  tabIndex={kpi.onClick ? 0 : undefined}
                >
                  <div className="kpi-card-icon" style={{ backgroundColor: kpi.bg, color: kpi.color }}>
                    <Icon size={22} color={kpi.color} />
                  </div>
                  <div className="kpi-card-content">
                    <div className="kpi-card-value" style={{ color: kpi.color, fontSize: kpi.value.length > 10 ? "16px" : "22px" }}>
                      {kpi.value}
                    </div>
                    <div className="kpi-card-title">{kpi.label}</div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Répartition par région */}
          {data.by_region.length > 0 && (
            <div className="card" style={{ marginTop: "20px" }}>
              <div className="chart-header">
                <h3 className="chart-title">
                  <Building2 size={16} />
                  Répartition par région sanitaire
                </h3>
              </div>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Région</th>
                      <th>Établissements</th>
                      <th>Patients</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.by_region.map((r) => (
                      <tr key={r.region}>
                        <td style={{ fontWeight: 600 }}>{r.region}</td>
                        <td>{_fmtNum(r.facilities_count)}</td>
                        <td>{_fmtNum(r.patients_count)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Répartition par type d'établissement */}
          {data.by_facility_type.length > 0 && (
            <div className="card" style={{ marginTop: "20px" }}>
              <div className="chart-header">
                <h3 className="chart-title">
                  <Building2 size={16} />
                  Répartition par type d'établissement
                </h3>
              </div>
              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", padding: "16px" }}>
                {data.by_facility_type.map((f) => (
                  <div key={f.category} style={{
                    padding: "12px 20px",
                    borderRadius: "8px",
                    background: "var(--primary-50)",
                    border: "1px solid var(--primary-100)",
                    textAlign: "center",
                  }}>
                    <div style={{ fontSize: "24px", fontWeight: 700, color: "var(--primary)" }}>{f.count}</div>
                    <div style={{ fontSize: "12px", color: "var(--muted)", textTransform: "uppercase" }}>{f.category}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Export Excel */}
          <div style={{ marginTop: "20px", display: "flex", gap: "12px" }}>
            <a
              href={`/api/v1/reporting/export/xlsx${region ? `?region=${region}` : ""}${period ? `${region ? "&" : "?"}period=${period}` : ""}`}
              className="btn btn-outline"
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              <FileText size={16} />
              Exporter Excel
            </a>
          </div>

          {/* Timeline déploiement national */}
          <div className="card" style={{ marginTop: "20px" }}>
            <h2>Déploiement national progressif</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "20px", marginTop: "12px" }}>
              {[
                { step: "1", title: "Démonstration", desc: "Validation institutionnelle et choix du périmètre pilote." },
                { step: "2", title: "Pilote hospitalier", desc: "Déploiement dans un établissement de référence pendant 3 à 6 mois." },
                { step: "3", title: "Extension régionale", desc: "Déploiement multi-établissements et consolidation des indicateurs." },
                { step: "4", title: "Plateforme nationale", desc: "Reporting national, interopérabilité et gouvernance centralisée." },
              ].map((item) => (
                <div key={item.step} style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
                  <div style={{
                    width: "36px", height: "36px", borderRadius: "50%",
                    background: "var(--primary)", color: "white",
                    display: "grid", placeItems: "center", fontWeight: 800, fontSize: "16px", flexShrink: 0,
                  }}>
                    {item.step}
                  </div>
                  <div>
                    <strong>{item.title}</strong>
                    <p className="muted" style={{ margin: "4px 0 0", fontSize: "14px" }}>{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
