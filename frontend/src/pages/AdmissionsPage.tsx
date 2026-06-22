import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";
import { usePaginatedList } from "../hooks/usePaginatedList";
import { Pagination } from "../components/Pagination";
import { useT } from "../i18n";
import {
  Activity,
  CalendarCheck,
  BedDouble,
  LogOut,
  Plus,
  Search,
  Eye,
  ClipboardCheck,
  Clock,
  UserCircle,
  Building2,
  Stethoscope,
  AlertTriangle,
  X,
  RefreshCw,
} from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════
   Types & Constants
   ═══════════════════════════════════════════════════════════════════ */

type TabKey = "tableau" | "nouvelle" | "historique";

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: "tableau", label: "Tableau", icon: <Activity size={16} /> },
  { key: "nouvelle", label: "Nouvelle admission", icon: <Plus size={16} /> },
  { key: "historique", label: "Historique", icon: <Clock size={16} /> },
];

const ADMISSION_TYPE_OPTIONS = [
  { value: "CONSULTATION", label: "Consultation" },
  { value: "HOSPITALIZATION", label: "Hospitalisation" },
  { value: "EMERGENCY", label: "Urgence" },
  { value: "DAY_HOSPITAL", label: "Hôpital de jour" },
  { value: "AMBULATORY", label: "Ambulatoire" },
];

const PRIORITY_OPTIONS = [
  { value: "ROUTINE", label: "Routine" },
  { value: "URGENT", label: "Urgent" },
  { value: "EMERGENCY", label: "Extrême urgence" },
];

const STATUS_MAP: Record<string, { label: string; badge: string }> = {
  OPEN: { label: "Active", badge: "badge-green" },
  ACTIVE: { label: "Active", badge: "badge-green" },
  CLOSED: { label: "Sorti", badge: "badge-gray" },
  DISCHARGED: { label: "Sorti", badge: "badge-gray" },
};

const TYPE_LABELS: Record<string, string> = {
  CONSULTATION: "Consultation",
  HOSPITALIZATION: "Hospitalisation",
  EMERGENCY: "Urgence",
  DAY_HOSPITAL: "Hôpital de jour",
  AMBULATORY: "Ambulatoire",
};

/* ═══════════════════════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════════════════════ */

export function AdmissionsPage({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const t = useT();
  const [activeTab, setActiveTab] = useState<TabKey>("tableau");

  return (
    <section>
      <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "4px" }}>
        <h1 style={{ margin: 0 }}>{t("nav.admissions")}</h1>
      </div>
      <p className="muted" style={{ marginBottom: "16px" }}>
        Gestion des admissions, hospitalisations et sorties des patients.
      </p>

      <div
        style={{
          display: "flex",
          gap: "4px",
          background: "var(--border-light)",
          padding: "4px",
          borderRadius: "var(--radius-lg)",
          marginBottom: "20px",
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
              background: activeTab === tab.key ? "var(--card)" : "transparent",
              color: activeTab === tab.key ? "var(--primary)" : "var(--muted)",
              boxShadow: activeTab === tab.key ? "var(--shadow-sm)" : "none",
              transition: "all 0.2s ease",
            }}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      <div>
        {activeTab === "tableau" && (
          <TableauTab lookups={lookups} onCreated={onCreated} />
        )}
        {activeTab === "nouvelle" && (
          <NouvelleAdmissionTab lookups={lookups} onCreated={onCreated} />
        )}
        {activeTab === "historique" && (
          <HistoriqueTab lookups={lookups} />
        )}
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   Tab 1 — Tableau (Dashboard)
   ═══════════════════════════════════════════════════════════════════ */

function TableauTab({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const t = useT();
  // Filtres serveur (appliqués via usePaginatedList.extraParams)
  const [statusFilter, setStatusFilter] = useState("OPEN");
  const [deptFilter, setDeptFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Données KPI (chargées séparément, indépendantes des filtres/pagination)
  const [kpiData, setKpiData] = useState<Row[]>([]);

  const options = buildOptions(lookups);

  // Liste paginée des admissions (recherche server-side + filtres serveur).
  // NOTE: le filtre statut est passé via extraParams.status (et NON via search),
  // ce qui corrige l'ancien bug où params.set("search", statusFilter) filtrait
  // sur admission_type au lieu du statut réel.
  const {
    items: admissions,
    total,
    page,
    totalPages,
    loading,
    error,
    search,
    setSearch,
    setPage,
    reload,
  } = usePaginatedList<Row>("/admissions", {
    pageSize: 20,
    debounceMs: 300,
    extraParams: {
      status: statusFilter || null,
      department_id: deptFilter || null,
      admission_type: typeFilter || null,
      date_from: dateFrom || null,
      date_to: dateTo || null,
    },
  });

  // Charger toutes les admissions pour les KPIs (comptages globaux,
  // indépendants des filtres/pagination de la table)
  async function loadKpis() {
    try {
      const payload = await apiRequest<any>("/admissions?page_size=1000");
      setKpiData(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      /* silent */
    }
  }

  useEffect(() => {
    loadKpis();
  }, []);

  // Réagir aux refresh globaux (création/sortie d'admission ailleurs)
  useEffect(() => {
    const handler = () => {
      reload();
      loadKpis();
    };
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [reload]);

  function handleRefresh() {
    reload();
    loadKpis();
    onCreated();
  }

  function handleResetFilters() {
    setStatusFilter("OPEN");
    setDeptFilter("");
    setTypeFilter("");
    setDateFrom("");
    setDateTo("");
    setSearch("");
    setPage(1);
  }

  /* ── Resolve names ─────────────────────────────── */
  function getPatientName(patientId: string): string {
    const p = lookups.patients.find((x) => x.id === patientId);
    if (!p) return "Inconnu";
    return `${p.first_name || ""} ${p.last_name || ""}`.trim() || p.patient_number || "N/A";
  }

  function getDeptName(deptId: string | null): string {
    if (!deptId) return "—";
    const d = lookups.departments.find((x) => x.id === deptId);
    return d ? `${d.code || ""} - ${d.name || d.id}`.trim() : "—";
  }

  function getFacilityName(facilityId: string): string {
    const f = lookups.facilities.find((x) => x.id === facilityId);
    return f ? f.name || f.id : "—";
  }

  /* ── Compute KPIs ──────────────────────────────── */
  const now = new Date();
  const todayStr = now.toDateString();

  const kpis = useMemo(() => {
    const active = kpiData.filter(
      (a) => a.status === "OPEN" || a.status === "ACTIVE"
    );
    const todayAdmissions = kpiData.filter((a) => {
      if (!a.admitted_at) return false;
      return new Date(a.admitted_at).toDateString() === todayStr;
    });
    const hospitalized = kpiData.filter(
      (a) =>
        (a.status === "OPEN" || a.status === "ACTIVE") &&
        a.admission_type === "HOSPITALIZATION"
    );
    const plannedDischarges = kpiData.filter(
      (a) => a.status === "CLOSED" || a.status === "DISCHARGED"
    );
    return {
      activeCount: active.length,
      todayCount: todayAdmissions.length,
      hospCount: hospitalized.length,
      dischargeCount: plannedDischarges.length,
    };
  }, [kpiData, todayStr]);

  /* ── Apply filters ── (filtrage server-side via usePaginatedList.extraParams) */

  /* ── Color coding helpers ──────────────────────── */
  function getStayIndicator(admission: Row): React.ReactNode {
    if (!admission.admitted_at) return null;
    const admittedDate = new Date(admission.admitted_at);
    const diffHours = (now.getTime() - admittedDate.getTime()) / (1000 * 60 * 60);
    if (diffHours < 24) {
      return (
        <span
          style={{
            display: "inline-block",
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: "#16a34a",
            marginRight: "6px",
            flexShrink: 0,
          }}
          title="Admission récente (< 24h)"
        />
      );
    }
    const diffDays = diffHours / 24;
    if (diffDays > 7) {
      return (
        <span
          style={{
            display: "inline-block",
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: "#f59e0b",
            marginRight: "6px",
            flexShrink: 0,
          }}
          title="Séjour long (> 7 jours)"
        />
      );
    }
    return null;
  }

  async function handleDischarge(admissionId: string) {
    if (!confirm("Confirmer la sortie de ce patient ?")) return;
    try {
      await apiRequest(`/admissions/${admissionId}/close`, { method: "POST" });
      showToast("Sortie enregistrée avec succès.", "success");
      handleRefresh();
    } catch {
      showToast("Erreur lors de l'enregistrement de la sortie.", "error");
    }
  }

  return (
    <>
      {/* ── KPI Cards ──────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "12px",
          marginBottom: "20px",
        }}
      >
        <KpiCard
          icon={<Activity size={20} />}
          label="Admissions actives"
          value={kpis.activeCount}
          color="var(--primary)"
          bgColor="var(--primary-light)"
        />
        <KpiCard
          icon={<CalendarCheck size={20} />}
          label="Prévues aujourd'hui"
          value={kpis.todayCount}
          color="#2563eb"
          bgColor="#eff6ff"
        />
        <KpiCard
          icon={<BedDouble size={20} />}
          label="En hospitalisation"
          value={kpis.hospCount}
          color="#7c3aed"
          bgColor="#f5f3ff"
        />
        <KpiCard
          icon={<LogOut size={20} />}
          label="Sorties prévues"
          value={kpis.dischargeCount}
          color="#b45309"
          bgColor="#fef3c7"
        />
      </div>

      {/* ── Barre de recherche (server-side, debounce 300ms) ── */}
      <div
        style={{
          display: "flex",
          gap: 12,
          alignItems: "center",
          marginBottom: 12,
          flexWrap: "wrap",
        }}
      >
        <input
          type="text"
          placeholder="🔍 Rechercher (patient, numéro, motif)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: 250, padding: "8px 12px" }}
        />
      </div>

      {/* ── Filters ────────────────────────────────────── */}
      <div
        className="card"
        style={{
          marginBottom: "16px",
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
          alignItems: "end",
          padding: "16px",
        }}
      >
        <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
          <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>Statut</span>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            style={{ minWidth: "160px", fontSize: "13px" }}
          >
            <option value="">Tous statuts</option>
            <option value="OPEN">Actives</option>
            <option value="CLOSED">Sortis</option>
          </select>
        </div>
        <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
          <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>Type</span>
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setPage(1);
            }}
            style={{ minWidth: "160px", fontSize: "13px" }}
          >
            <option value="">Tous types</option>
            {ADMISSION_TYPE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
          <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>Service</span>
          <select
            value={deptFilter}
            onChange={(e) => {
              setDeptFilter(e.target.value);
              setPage(1);
            }}
            style={{ minWidth: "180px", fontSize: "13px" }}
          >
            <option value="">Tous les services</option>
            {options.departments.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
          <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>Date début</span>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => {
              setDateFrom(e.target.value);
              setPage(1);
            }}
            style={{ fontSize: "13px" }}
          />
        </div>
        <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
          <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>Date fin</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => {
              setDateTo(e.target.value);
              setPage(1);
            }}
            style={{ fontSize: "13px" }}
          />
        </div>
        <button
          className="btn btn-outline btn-sm"
          onClick={handleResetFilters}
          style={{ height: "38px" }}
        >
          <X size={14} />
          Réinitialiser
        </button>
        <button
          className="btn btn-outline btn-sm"
          onClick={handleRefresh}
          style={{ height: "38px" }}
        >
          <RefreshCw size={14} />
          Actualiser
        </button>
      </div>

      {/* ── Admissions Table ───────────────────────────── */}
      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
          <p className="muted" style={{ marginTop: "12px" }}>
            {t("label.loading")}
          </p>
        </div>
      ) : error ? (
        <div className="card" style={{ padding: "16px", color: "var(--danger)" }}>
          {error}
        </div>
      ) : admissions.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <p className="muted">Aucune admission trouvée.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: "0" }}>
          <div className="table-wrapper" style={{ maxHeight: "520px", overflowY: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Date d'admission</th>
                  <th>Motif / Type</th>
                  <th>Service</th>
                  <th>Statut</th>
                  <th>Établissement</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {admissions.map((adm) => {
                  const statusInfo = STATUS_MAP[adm.status] || {
                    label: adm.status,
                    badge: "badge-gray",
                  };
                  const isActive =
                    adm.status === "OPEN" || adm.status === "ACTIVE";
                  return (
                    <tr key={adm.id}>
                      <td>
                        <div style={{ display: "flex", alignItems: "center" }}>
                          {getStayIndicator(adm)}
                          <span style={{ fontWeight: 600 }}>
                            {getPatientName(adm.patient_id)}
                          </span>
                        </div>
                      </td>
                      <td style={{ whiteSpace: "nowrap", fontSize: "13px" }}>
                        {adm.admitted_at
                          ? new Date(adm.admitted_at).toLocaleString("fr-FR", {
                              day: "2-digit",
                              month: "2-digit",
                              year: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "—"}
                      </td>
                      <td>
                        <span style={{ fontWeight: 500 }}>
                          {TYPE_LABELS[adm.admission_type] ||
                            adm.admission_type ||
                            "—"}
                        </span>
                      </td>
                      <td style={{ fontSize: "13px" }}>
                        {getDeptName(adm.department_id)}
                      </td>
                      <td>
                        <span className={`badge ${statusInfo.badge}`}>
                          {statusInfo.label}
                        </span>
                      </td>
                      <td style={{ fontSize: "13px" }}>
                        {getFacilityName(adm.facility_id)}
                      </td>
                      <td>
                        <div style={{ display: "flex", gap: "6px" }}>
                          <button
                            className="btn btn-outline btn-sm"
                            title="Voir dossier"
                          >
                            <Eye size={13} />
                            Dossier
                          </button>
                          {isActive && (
                            <button
                              className="btn btn-sm"
                              style={{
                                background: "#fef3c7",
                                color: "#92400e",
                                border: "1px solid #fcd34d",
                              }}
                              onClick={() => handleDischarge(adm.id)}
                              title="Programmer sortie"
                            >
                              <ClipboardCheck size={13} />
                              Sortie
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div style={{ padding: "0 16px" }}>
            <Pagination
              page={page}
              totalPages={totalPages}
              total={total}
              onPageChange={setPage}
              loading={loading}
            />
          </div>
        </div>
      )}
    </>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   Tab 2 — Nouvelle Admission
   ═══════════════════════════════════════════════════════════════════ */

function NouvelleAdmissionTab({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const options = buildOptions(lookups);
  const doctors = lookups.staff.filter(
    (s) => s.role === "DOCTOR" || s.role === "PHYSICIAN"
  );

  const [facilityId, setFacilityId] = useState(firstValue(options.facilities));
  const [patientId, setPatientId] = useState("");
  const [patientSearch, setPatientSearch] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [admissionType, setAdmissionType] = useState("CONSULTATION");
  const [motif, setMotif] = useState("");
  const [doctorId, setDoctorId] = useState("");
  const [admissionDate, setAdmissionDate] = useState(
    new Date().toISOString().slice(0, 16)
  );
  const [priority, setPriority] = useState("ROUTINE");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPatientDropdown, setShowPatientDropdown] = useState(false);

  const filteredPatients = useMemo(() => {
    if (!patientSearch.trim()) return lookups.patients.slice(0, 20);
    const q = patientSearch.toLowerCase();
    return lookups.patients
      .filter(
        (p) =>
          (p.first_name || "").toLowerCase().includes(q) ||
          (p.last_name || "").toLowerCase().includes(q) ||
          (p.patient_number || "").toLowerCase().includes(q)
      )
      .slice(0, 20);
  }, [lookups.patients, patientSearch]);

  function selectPatient(p: Row) {
    setPatientId(p.id);
    setPatientSearch(
      `${p.first_name || ""} ${p.last_name || ""}`.trim() ||
        p.patient_number ||
        ""
    );
    setShowPatientDropdown(false);
  }

  function clearPatient() {
    setPatientId("");
    setPatientSearch("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!patientId || !facilityId) {
      showToast("Veuillez sélectionner un patient et un établissement.", "error");
      return;
    }
    setSubmitting(true);
    try {
      await apiRequest("/admissions", {
        method: "POST",
        body: JSON.stringify({
          facility_id: facilityId,
          patient_id: patientId,
          department_id: departmentId || undefined,
          admission_type: admissionType,
          status: "OPEN",
        }),
      });
      showToast("Admission enregistrée avec succès.", "success");
      onCreated();
      // Reset form
      setPatientId("");
      setPatientSearch("");
      setDepartmentId("");
      setAdmissionType("CONSULTATION");
      setMotif("");
      setDoctorId("");
      setAdmissionDate(new Date().toISOString().slice(0, 16));
      setPriority("ROUTINE");
      setNotes("");
    } catch {
      showToast("Erreur lors de l'enregistrement de l'admission.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const priorityColors: Record<string, { bg: string; text: string; border: string }> = {
    ROUTINE: { bg: "#f0fdf4", text: "#047857", border: "#86efac" },
    URGENT: { bg: "#fffbeb", text: "#92400e", border: "#fcd34d" },
    EMERGENCY: { bg: "#fef2f2", text: "#b91c1c", border: "#fca5a5" },
  };

  return (
    <div className="card" style={{ maxWidth: "900px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "20px" }}>
        <div
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "var(--radius-md)",
            background: "var(--primary-light)",
            color: "var(--primary)",
            display: "grid",
            placeItems: "center",
          }}
        >
          <Plus size={18} />
        </div>
        <div>
          <h2 style={{ fontSize: "18px", margin: 0 }}>Nouvelle admission</h2>
          <p className="muted" style={{ fontSize: "13px" }}>
            Enregistrer une nouvelle admission de patient
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* ── Section: Patient ──────────────────────── */}
        <fieldset
          style={{
            border: "1px solid var(--border-light)",
            borderRadius: "var(--radius-lg)",
            padding: "16px",
            marginBottom: "20px",
          }}
        >
          <legend
            style={{
              fontSize: "13px",
              fontWeight: 700,
              color: "var(--primary)",
              padding: "0 8px",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            <UserCircle size={14} style={{ verticalAlign: "middle", marginRight: "4px" }} />
            Patient
          </legend>
          <div style={{ position: "relative" }}>
            <div style={{ position: "relative" }}>
              <Search
                size={16}
                style={{
                  position: "absolute",
                  left: "10px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  color: "var(--muted)",
                }}
              />
              <input
                type="text"
                placeholder="Rechercher un patient (nom, prénom, numéro)..."
                value={patientSearch}
                onChange={(e) => {
                  setPatientSearch(e.target.value);
                  setShowPatientDropdown(true);
                  setPatientId("");
                }}
                onFocus={() => setShowPatientDropdown(true)}
                style={{ paddingLeft: "34px", paddingRight: patientId ? "32px" : "12px" }}
                required={!patientId}
              />
              {patientId && (
                <button
                  type="button"
                  onClick={clearPatient}
                  style={{
                    position: "absolute",
                    right: "8px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    background: "none",
                    border: "none",
                    color: "var(--muted)",
                    cursor: "pointer",
                    padding: "2px",
                  }}
                >
                  <X size={16} />
                </button>
              )}
            </div>
            {showPatientDropdown && !patientId && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  left: 0,
                  right: 0,
                  background: "var(--card)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-md)",
                  maxHeight: "220px",
                  overflowY: "auto",
                  zIndex: 100,
                  boxShadow: "var(--shadow-md)",
                }}
              >
                {filteredPatients.length === 0 ? (
                  <div style={{ padding: "12px", color: "var(--muted)", fontSize: "13px" }}>
                    Aucun patient trouvé
                  </div>
                ) : (
                  filteredPatients.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => selectPatient(p)}
                      style={{
                        display: "block",
                        width: "100%",
                        textAlign: "left",
                        padding: "10px 14px",
                        border: "none",
                        background: "transparent",
                        cursor: "pointer",
                        fontSize: "13px",
                        fontFamily: "inherit",
                        borderBottom: "1px solid var(--border-light)",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.background = "var(--primary-light)")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.background = "transparent")
                      }
                    >
                      <span style={{ fontWeight: 600 }}>
                        {p.first_name || ""} {p.last_name || ""}
                      </span>
                      {p.patient_number && (
                        <span className="muted" style={{ marginLeft: "8px", fontSize: "12px" }}>
                          ({p.patient_number})
                        </span>
                      )}
                    </button>
                  ))
                )}
              </div>
            )}
            {patientId && (
              <div
                style={{
                  marginTop: "8px",
                  padding: "6px 12px",
                  background: "var(--primary-light)",
                  borderRadius: "var(--radius-md)",
                  fontSize: "13px",
                  color: "var(--primary)",
                  fontWeight: 600,
                }}
              >
                ✓ Patient sélectionné : {patientSearch}
              </div>
            )}
          </div>
        </fieldset>

        {/* ── Section: Organisation ─────────────────── */}
        <fieldset
          style={{
            border: "1px solid var(--border-light)",
            borderRadius: "var(--radius-lg)",
            padding: "16px",
            marginBottom: "20px",
          }}
        >
          <legend
            style={{
              fontSize: "13px",
              fontWeight: 700,
              color: "var(--primary)",
              padding: "0 8px",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            <Building2 size={14} style={{ verticalAlign: "middle", marginRight: "4px" }} />
            Organisation
          </legend>
          <div className="form-grid">
            <label className="form-control">
              Établissement *
              <select
                value={facilityId}
                onChange={(e) => setFacilityId(e.target.value)}
                required
              >
                <option value="">-- Choisir --</option>
                {options.facilities.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Service
              <select
                value={departmentId}
                onChange={(e) => setDepartmentId(e.target.value)}
              >
                <option value="">-- Choisir --</option>
                {options.departments.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Médecin traitant
              <select
                value={doctorId}
                onChange={(e) => setDoctorId(e.target.value)}
              >
                <option value="">-- Choisir --</option>
                {doctors.map((d) => (
                  <option key={d.id} value={d.id}>
                    Dr. {d.last_name || ""} {d.first_name || ""}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </fieldset>

        {/* ── Section: Admission ────────────────────── */}
        <fieldset
          style={{
            border: "1px solid var(--border-light)",
            borderRadius: "var(--radius-lg)",
            padding: "16px",
            marginBottom: "20px",
          }}
        >
          <legend
            style={{
              fontSize: "13px",
              fontWeight: 700,
              color: "var(--primary)",
              padding: "0 8px",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            <Stethoscope size={14} style={{ verticalAlign: "middle", marginRight: "4px" }} />
            Détails de l'admission
          </legend>
          <div className="form-grid">
            <label className="form-control">
              Type d'admission *
              <select
                value={admissionType}
                onChange={(e) => setAdmissionType(e.target.value)}
                required
              >
                {ADMISSION_TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Date/heure d'admission
              <input
                type="datetime-local"
                value={admissionDate}
                onChange={(e) => setAdmissionDate(e.target.value)}
              />
            </label>
            <label className="form-control">
              Priorité *
              <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
                {PRIORITY_OPTIONS.map((opt) => {
                  const colors = priorityColors[opt.value];
                  const isSelected = priority === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setPriority(opt.value)}
                      style={{
                        padding: "6px 14px",
                        borderRadius: "var(--radius-md)",
                        border: `2px solid ${isSelected ? colors.text : colors.border}`,
                        background: isSelected ? colors.bg : "white",
                        color: isSelected ? colors.text : "var(--muted)",
                        fontWeight: isSelected ? 700 : 500,
                        fontSize: "13px",
                        fontFamily: "inherit",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                      }}
                    >
                      {opt.value === "EMERGENCY" && <AlertTriangle size={13} />}
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </label>
          </div>
          <label className="form-control" style={{ marginTop: "8px" }}>
            Motif d'admission
            <textarea
              value={motif}
              onChange={(e) => setMotif(e.target.value)}
              placeholder="Décrivez le motif de l'admission..."
              rows={3}
              style={{
                width: "100%",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-sm)",
                padding: "10px 12px",
                font: "inherit",
                resize: "vertical",
                minHeight: "72px",
              }}
            />
          </label>
          <label className="form-control">
            Notes complémentaires
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Notes additionnelles..."
              rows={2}
              style={{
                width: "100%",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-sm)",
                padding: "10px 12px",
                font: "inherit",
                resize: "vertical",
                minHeight: "48px",
              }}
            />
          </label>
        </fieldset>

        {/* ── Actions ───────────────────────────────── */}
        <div className="form-actions">
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Enregistrement..." : "Enregistrer l'admission"}
          </button>
          <button
            className="btn btn-outline"
            type="button"
            onClick={() => {
              setPatientId("");
              setPatientSearch("");
              setDepartmentId("");
              setAdmissionType("CONSULTATION");
              setMotif("");
              setDoctorId("");
              setAdmissionDate(new Date().toISOString().slice(0, 16));
              setPriority("ROUTINE");
              setNotes("");
            }}
          >
            Réinitialiser
          </button>
        </div>
      </form>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   Tab 3 — Historique
   ═══════════════════════════════════════════════════════════════════ */

function HistoriqueTab({ lookups }: { lookups: LookupData }) {
  const t = useT();
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Liste paginée des admissions sorties (status=CLOSED, recherche server-side).
  // Backend supporte status=CLOSED qui couvre les statuts CLOSED/DISCHARGED.
  const {
    items: admissions,
    total,
    page,
    totalPages,
    loading,
    error,
    search,
    setSearch,
    setPage,
    reload,
  } = usePaginatedList<Row>("/admissions", {
    pageSize: 20,
    debounceMs: 300,
    extraParams: {
      status: "CLOSED",
      date_from: dateFrom || null,
      date_to: dateTo || null,
    },
  });

  // Réagir aux refresh globaux (création/sortie d'admission ailleurs)
  useEffect(() => {
    const handler = () => reload();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [reload]);

  function getPatientName(patientId: string): string {
    const p = lookups.patients.find((x) => x.id === patientId);
    if (!p) return "Inconnu";
    return `${p.first_name || ""} ${p.last_name || ""}`.trim() || p.patient_number || "N/A";
  }

  function getDeptName(deptId: string | null): string {
    if (!deptId) return "—";
    const d = lookups.departments.find((x) => x.id === deptId);
    return d ? `${d.code || ""} - ${d.name || d.id}`.trim() : "—";
  }

  function getStayDuration(adm: Row): string {
    if (!adm.admitted_at) return "—";
    const start = new Date(adm.admitted_at);
    const end = adm.closed_at ? new Date(adm.closed_at) : new Date();
    const diffDays = Math.round(
      (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)
    );
    if (diffDays === 0) return "< 1 jour";
    return `${diffDays} jour${diffDays > 1 ? "s" : ""}`;
  }

  return (
    <>
      {/* ── Barre de recherche + filtres date (server-side, debounce 300ms) ── */}
      <div
        style={{
          display: "flex",
          gap: 12,
          alignItems: "center",
          marginBottom: 12,
          flexWrap: "wrap",
        }}
      >
        <input
          type="text"
          placeholder="🔍 Rechercher (patient, numéro)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: 250, padding: "8px 12px" }}
        />
        <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
          <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Date sortie début
          </span>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => {
              setDateFrom(e.target.value);
              setPage(1);
            }}
            style={{ fontSize: "13px" }}
          />
        </div>
        <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
          <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Date sortie fin
          </span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => {
              setDateTo(e.target.value);
              setPage(1);
            }}
            style={{ fontSize: "13px" }}
          />
        </div>
        <button
          className="btn btn-outline btn-sm"
          onClick={() => {
            setDateFrom("");
            setDateTo("");
            setSearch("");
            setPage(1);
          }}
          style={{ height: "38px" }}
        >
          <X size={14} />
          Réinitialiser
        </button>
      </div>

      {/* ── Discharged Table ──────────────────────────── */}
      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
          <p className="muted" style={{ marginTop: "12px" }}>
            {t("label.loading")}
          </p>
        </div>
      ) : error ? (
        <div className="card" style={{ padding: "16px", color: "var(--danger)" }}>
          {error}
        </div>
      ) : admissions.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <p className="muted">Aucun patient sorti trouvé.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: "0" }}>
          <div className="table-wrapper" style={{ maxHeight: "520px", overflowY: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Date d'admission</th>
                  <th>Date de sortie</th>
                  <th>Durée de séjour</th>
                  <th>Type</th>
                  <th>Service</th>
                </tr>
              </thead>
              <tbody>
                {admissions.map((adm) => (
                  <tr key={adm.id}>
                    <td style={{ fontWeight: 600 }}>
                      {getPatientName(adm.patient_id)}
                    </td>
                    <td style={{ whiteSpace: "nowrap", fontSize: "13px" }}>
                      {adm.admitted_at
                        ? new Date(adm.admitted_at).toLocaleDateString("fr-FR")
                        : "—"}
                    </td>
                    <td style={{ whiteSpace: "nowrap", fontSize: "13px" }}>
                      {adm.closed_at
                        ? new Date(adm.closed_at).toLocaleDateString("fr-FR")
                        : "—"}
                    </td>
                    <td>
                      <span
                        className="badge badge-blue"
                        style={{ fontSize: "12px" }}
                      >
                        {getStayDuration(adm)}
                      </span>
                    </td>
                    <td style={{ fontSize: "13px" }}>
                      {TYPE_LABELS[adm.admission_type] ||
                        adm.admission_type ||
                        "—"}
                    </td>
                    <td style={{ fontSize: "13px" }}>
                      {getDeptName(adm.department_id)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ padding: "0 16px" }}>
            <Pagination
              page={page}
              totalPages={totalPages}
              total={total}
              onPageChange={setPage}
              loading={loading}
            />
          </div>
        </div>
      )}
    </>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   KPI Card Component
   ═══════════════════════════════════════════════════════════════════ */

function KpiCard({
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
        padding: "16px 18px",
        background: "var(--card)",
        borderRadius: "var(--radius-lg)",
        boxShadow: "var(--shadow-xs)",
        border: "1px solid var(--border-light)",
      }}
    >
      <div
        style={{
          width: "42px",
          height: "42px",
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
        <div
          style={{
            fontSize: "24px",
            fontWeight: 800,
            color: "var(--text)",
            lineHeight: 1.2,
          }}
        >
          {value}
        </div>
        <div
          style={{
            fontSize: "12px",
            color: "var(--muted)",
            fontWeight: 500,
          }}
        >
          {label}
        </div>
      </div>
    </div>
  );
}
