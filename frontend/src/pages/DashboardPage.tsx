import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { buildOptions, firstValue } from "../utils/options";

type DashboardStats = {
  patients: number;
  admissions: number;
  emergencyVisits: number;
  activeStays: number;
  availableBeds: number;
  totalBeds: number;
  pendingLabOrders: number;
  surgeryScheduled: number;
  pendingImaging: number;
  activeAlerts: number;
  draftReports: number;
  openIncidents: number;
};

export function DashboardPage({ lookups }: { lookups: LookupData }) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [recentPatients, setRecentPatients] = useState<Row[]>([]);
  const [recentAdmissions, setRecentAdmissions] = useState<Row[]>([]);

  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  const loadStats = useCallback(async () => {
    if (!facilityId) return;
    setLoading(true);
    try {
      // Fetch all stats in parallel
      const [patients, admissions, emergency, stays, beds, labOrders, imagingOrders, reporting] =
        await Promise.all([
          apiRequest<{ data?: Row[] }>("/patients"),
          apiRequest<{ data?: Row[] }>("/admissions"),
          apiRequest<{ data?: Row[] }>("/emergency/queue"),
          apiRequest<{ data?: Row[] }>("/hospitalization/stays?status=ACTIVE"),
          apiRequest<{ data?: Row[] }>(`/hospitalization/bed-board?facility_id=${facilityId}`),
          apiRequest<{ data?: Row[] }>("/laboratory/orders"),
          apiRequest<{ data?: Row[] }>("/imaging/orders?status=PENDING"),
          apiRequest<{ data?: Record<string, unknown> }>("/reporting/dashboard"),
        ]);

      const allBeds = Array.isArray(beds.data) ? beds.data : [];
      const availableBeds = allBeds.filter((b: Row) => b.bed_status === "AVAILABLE").length;
      const labPending = Array.isArray(labOrders.data)
        ? labOrders.data.filter((o: Row) => o.status === "PENDING" || o.status === "IN_PROGRESS").length
        : 0;
      const imagingPending = Array.isArray(imagingOrders.data) ? imagingOrders.data.length : 0;

      const reportingData = reporting.data || {};
      const activeAlerts = Number(reportingData.active_alerts || 0);
      const draftReports = Number(reportingData.draft_reports || 0);

      setStats({
        patients: Array.isArray(patients.data) ? patients.data.length : 0,
        admissions: Array.isArray(admissions.data) ? admissions.data.length : 0,
        emergencyVisits: Array.isArray(emergency.data) ? emergency.data.length : 0,
        activeStays: Array.isArray(stays.data) ? stays.data.length : 0,
        availableBeds,
        totalBeds: allBeds.length,
        pendingLabOrders: labPending,
        surgeryScheduled: 0,
        pendingImaging: imagingPending,
        activeAlerts,
        draftReports,
        openIncidents: 0,
      });

      // Recent patients
      const patientsList = Array.isArray(patients.data) ? patients.data : [];
      setRecentPatients(patientsList.slice(0, 5));

      // Recent admissions
      const admissionsList = Array.isArray(admissions.data) ? admissions.data : [];
      setRecentAdmissions(admissionsList.slice(0, 5));
    } catch {
      // Silently fail — dashboard should remain usable
    } finally {
      setLoading(false);
    }
  }, [facilityId]);

  useEffect(() => {
    loadStats();
    const handler = () => loadStats();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadStats]);

  if (loading && !stats) {
    return (
      <section>
        <h1>Dashboard hôpital</h1>
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
          <p className="muted" style={{ marginTop: "12px" }}>Chargement des statistiques...</p>
        </div>
      </section>
    );
  }

  const bedOccupancy = stats && stats.totalBeds > 0
    ? Math.round(((stats.totalBeds - stats.availableBeds) / stats.totalBeds) * 100)
    : 0;

  return (
    <section>
      <h1>Dashboard hôpital</h1>
      <p className="muted">Vue d'ensemble de l'activité hospitalière en temps réel.</p>

      {/* KPI Cards */}
      <div className="grid">
        <KpiCard
          title="Patients enregistrés"
          value={stats?.patients ?? 0}
          icon="👤"
          color="#2563eb"
        />
        <KpiCard
          title="Admissions actives"
          value={stats?.admissions ?? 0}
          icon="📋"
          color="#7c3aed"
        />
        <KpiCard
          title="Urgences en cours"
          value={stats?.emergencyVisits ?? 0}
          icon="🚨"
          color="#dc2626"
        />
        <KpiCard
          title="Hospitalisés"
          value={stats?.activeStays ?? 0}
          icon="🏥"
          color="#059669"
        />
        <KpiCard
          title="Lits disponibles"
          value={`${stats?.availableBeds ?? 0} / ${stats?.totalBeds ?? 0}`}
          icon="🛏️"
          color={bedOccupancy > 85 ? "#dc2626" : "#059669"}
          subtitle={stats && stats.totalBeds > 0 ? `Taux d'occupation : ${bedOccupancy}%` : undefined}
        />
        <KpiCard
          title="Examens en attente"
          value={(stats?.pendingLabOrders ?? 0) + (stats?.pendingImaging ?? 0)}
          icon="🔬"
          color="#d97706"
        />
      </div>

      {/* Secondary KPIs */}
      <div className="grid" style={{ marginTop: "18px" }}>
        <KpiCard
          title="Alertes épidémiques"
          value={stats?.activeAlerts ?? 0}
          icon="⚠️"
          color={stats && stats.activeAlerts > 0 ? "#dc2626" : "#059669"}
        />
        <KpiCard
          title="Rapports en brouillon"
          value={stats?.draftReports ?? 0}
          icon="📊"
          color="#6366f1"
        />
      </div>

      {/* Recent Activity */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "18px", marginTop: "18px" }}>
        {/* Recent Patients */}
        <div className="card">
          <h3 style={{ marginBottom: "12px" }}>Patients récents</h3>
          {recentPatients.length === 0 ? (
            <p className="muted">Aucun patient enregistré.</p>
          ) : (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Nom</th>
                    <th>Sexe</th>
                    <th>Date de naissance</th>
                  </tr>
                </thead>
                <tbody>
                  {recentPatients.map((p) => (
                    <tr key={p.id}>
                      <td style={{ fontWeight: 600 }}>{p.first_name} {p.last_name}</td>
                      <td>{p.gender === "M" ? "Masculin" : p.gender === "F" ? "Féminin" : p.gender || "—"}</td>
                      <td>{p.date_of_birth ? new Date(p.date_of_birth).toLocaleDateString("fr-FR") : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Admissions */}
        <div className="card">
          <h3 style={{ marginBottom: "12px" }}>Admissions récentes</h3>
          {recentAdmissions.length === 0 ? (
            <p className="muted">Aucune admission enregistrée.</p>
          ) : (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Patient</th>
                    <th>Motif</th>
                  </tr>
                </thead>
                <tbody>
                  {recentAdmissions.map((a) => (
                    <tr key={a.id}>
                      <td style={{ whiteSpace: "nowrap" }}>
                        {a.admitted_at ? new Date(a.admitted_at).toLocaleDateString("fr-FR") : "—"}
                      </td>
                      <td style={{ fontWeight: 600 }}>{a.patient_id || "—"}</td>
                      <td>{a.reason || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function KpiCard({
  title,
  value,
  icon,
  color,
  subtitle,
}: {
  title: string;
  value: number | string;
  icon: string;
  color: string;
  subtitle?: string;
}) {
  return (
    <div className="card" style={{ position: "relative", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "4px",
          height: "100%",
          background: color,
          borderRadius: "4px 0 0 4px",
        }}
      />
      <div style={{ paddingLeft: "12px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div className="muted" style={{ fontSize: "13px", fontWeight: 600, textTransform: "uppercase" }}>
            {title}
          </div>
          <span style={{ fontSize: "24px" }}>{icon}</span>
        </div>
        <div className="kpi" style={{ margin: "4px 0", color }}>{value}</div>
        {subtitle && (
          <div className="muted" style={{ fontSize: "12px" }}>{subtitle}</div>
        )}
      </div>
    </div>
  );
}
