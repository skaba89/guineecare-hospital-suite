import { useState, useEffect, useMemo } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { EmergencyQueuePage } from "./EmergencyQueuePage";
import { EmergencyTriagePage } from "./EmergencyTriagePage";
import { EmergencyOrientationPage } from "./EmergencyOrientationPage";
import { useT } from "../i18n";
import {
  Activity,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Stethoscope,
  LayoutDashboard,
  ClipboardList,
  ArrowRightLeft,
} from "lucide-react";

type TabKey = "tableau" | "triage" | "orientation";

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: "tableau", label: "Tableau", icon: <LayoutDashboard size={16} /> },
  { key: "triage", label: "Triage", icon: <ClipboardList size={16} /> },
  { key: "orientation", label: "Orientation", icon: <ArrowRightLeft size={16} /> },
];

export function EmergencyPage({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const t = useT();
  const [activeTab, setActiveTab] = useState<TabKey>("tableau");
  const [visits, setVisits] = useState<Row[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let mounted = true;
    async function fetchVisits() {
      try {
        const payload = await apiRequest<any>("/emergency/queue?page_size=1000");
        const data: Row[] = Array.isArray(payload.data) ? payload.data : [];
        if (mounted) setVisits(data);
      } catch {
        // silently ignore
      }
    }
    fetchVisits();
    const interval = setInterval(fetchVisits, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [refreshKey]);

  const stats = useMemo(() => ({
    total: visits.length,
    waiting: visits.filter(
      (v) => v.status === "WAITING" || v.status === "ARRIVED"
    ).length,
    triaged: visits.filter((v) => v.status === "TRIAGED").length,
    inCare: visits.filter((v) => v.status === "IN_CARE").length,
    oriented: visits.filter(
      (v) => v.status === "ORIENTED" || v.status === "DISCHARGED"
    ).length,
    critical: visits.filter((v) => v.priority_level === "CRITICAL").length,
  }), [visits]);

  function handleRefresh() {
    setRefreshKey((k) => k + 1);
    onCreated();
  }

  function getPatientName(patientId: string): string {
    const patient = lookups.patients.find((p) => p.id === patientId);
    if (!patient) return "Inconnu";
    return `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.patient_number || "N/A";
  }

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* ── Stats Bar ──────────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
          gap: "12px",
        }}
      >
        <StatCard
          icon={<Activity size={20} />}
          label="Total patients"
          value={stats.total}
          color="var(--primary)"
          bgColor="var(--primary-light)"
        />
        <StatCard
          icon={<Clock size={20} />}
          label="En attente"
          value={stats.waiting}
          color="#b45309"
          bgColor="#fef3c7"
        />
        <StatCard
          icon={<ClipboardList size={20} />}
          label="Triés"
          value={stats.triaged}
          color="var(--accent)"
          bgColor="var(--accent-light)"
        />
        <StatCard
          icon={<Stethoscope size={20} />}
          label="En soins"
          value={stats.inCare}
          color="#047857"
          bgColor="#d1fae5"
        />
        <StatCard
          icon={<CheckCircle2 size={20} />}
          label="Orientés/Sortis"
          value={stats.oriented}
          color="var(--muted)"
          bgColor="#f1f5f9"
        />
        <StatCard
          icon={<AlertTriangle size={20} />}
          label="Critiques"
          value={stats.critical}
          color="var(--danger)"
          bgColor="var(--danger-light)"
        />
      </div>

      {/* ── Tab Bar ────────────────────────────────────────── */}
      <div
        style={{
          display: "flex",
          gap: "4px",
          background: "var(--border-light)",
          padding: "4px",
          borderRadius: "var(--radius-lg)",
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 20px",
              borderRadius: "var(--radius-md)",
              border: "none",
              cursor: "pointer",
              fontWeight: activeTab === tab.key ? 700 : 400,
              fontSize: "14px",
              fontFamily: "inherit",
              background:
                activeTab === tab.key ? "var(--card)" : "transparent",
              color: activeTab === tab.key ? "var(--primary)" : "var(--muted)",
              boxShadow:
                activeTab === tab.key ? "var(--shadow-sm)" : "none",
              transition: "all 0.2s ease",
            }}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab Content ────────────────────────────────────── */}
      <div>
        {activeTab === "tableau" && (
          <EmergencyQueuePage
            lookups={lookups}
            onCreated={handleRefresh}
            getPatientName={getPatientName}
          />
        )}
        {activeTab === "triage" && (
          <EmergencyTriagePage
            lookups={lookups}
            onCreated={handleRefresh}
            getPatientName={getPatientName}
          />
        )}
        {activeTab === "orientation" && (
          <EmergencyOrientationPage
            lookups={lookups}
            onCreated={handleRefresh}
            getPatientName={getPatientName}
          />
        )}
      </div>
    </section>
  );
}

/* ── Stat Card Component ────────────────────────────────────── */
function StatCard({
  icon,
  label,
  value,
  color,
  bgColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
  bgColor: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "14px 16px",
        background: "var(--card)",
        borderRadius: "var(--radius-lg)",
        boxShadow: "var(--shadow-xs)",
        border: "1px solid var(--border-light)",
      }}
    >
      <div
        style={{
          width: "40px",
          height: "40px",
          borderRadius: "var(--radius-md)",
          display: "grid",
          placeItems: "center",
          background: bgColor,
          color: color,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div>
        <div style={{ fontSize: "22px", fontWeight: 700, color: "var(--text)", lineHeight: 1.2 }}>
          {value}
        </div>
        <div style={{ fontSize: "12px", color: "var(--muted)", fontWeight: 500 }}>
          {label}
        </div>
      </div>
    </div>
  );
}
