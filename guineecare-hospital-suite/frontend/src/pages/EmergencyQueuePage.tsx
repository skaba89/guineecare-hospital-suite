import { useEffect, useState, useCallback } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import {
  Clock,
  AlertTriangle,
  User,
  Stethoscope,
  LogOut,
  Plus,
  RefreshCw,
  Filter,
  ChevronRight,
  X,
  Ambulance,
  Heart,
} from "lucide-react";

const PRIORITY_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; pulse: boolean }
> = {
  LOW: { label: "Basse", color: "#047857", bg: "#d1fae5", pulse: false },
  NORMAL: { label: "Normale", color: "#1d4ed8", bg: "#dbeafe", pulse: false },
  HIGH: { label: "Haute", color: "#c2410c", bg: "#ffedd5", pulse: false },
  CRITICAL: {
    label: "Critique",
    color: "#b91c1c",
    bg: "#fee2e2",
    pulse: true,
  },
};

const ARRIVAL_MODES = [
  { value: "WALK_IN", label: "Marche" },
  { value: "AMBULANCE", label: "Ambulance" },
  { value: "POLICE", label: "Police" },
  { value: "TRANSFER", label: "Transfert" },
];

function getWaitMinutes(arrivedAt: string): number {
  if (!arrivedAt) return 0;
  const arrived = new Date(arrivedAt);
  const now = new Date();
  return Math.floor((now.getTime() - arrived.getTime()) / 60000);
}

function formatWaitTime(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h${m > 0 ? `${m}min` : ""}`;
}

function getPatientAge(patient: Row | undefined): string {
  if (!patient || !patient.date_of_birth) return "—";
  const birth = new Date(patient.date_of_birth);
  const now = new Date();
  const age = now.getFullYear() - birth.getFullYear();
  return `${age} ans`;
}

function getPatientGender(patient: Row | undefined): string {
  if (!patient) return "";
  return patient.gender === "M" ? "♂" : patient.gender === "F" ? "♀" : "";
}

export function EmergencyQueuePage({
  lookups,
  onCreated,
  getPatientName,
}: {
  lookups: LookupData;
  onCreated: () => void;
  getPatientName: (id: string) => string;
}) {
  const [visits, setVisits] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [showNewPatientModal, setShowNewPatientModal] = useState(false);
  const [recentlyCompleted, setRecentlyCompleted] = useState<Row[]>([]);
  const [now, setNow] = useState(new Date());

  // New patient form state
  const [newPatientId, setNewPatientId] = useState("");
  const [newComplaint, setNewComplaint] = useState("");
  const [newArrivalMode, setNewArrivalMode] = useState("WALK_IN");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/emergency/queue?page_size=1000");
      const allVisits = Array.isArray(payload.data) ? payload.data : [];
      setVisits(allVisits);
    } catch {
      setError("Impossible de charger les données.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const handler = () => load();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [load]);

  // Auto-refresh timer
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      load();
      setNow(new Date());
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, load]);

  // Clock tick for wait time counters
  useEffect(() => {
    const tick = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(tick);
  }, []);

  // Filter visits
  const filteredVisits = visits.filter((v) => {
    if (priorityFilter === "ALL") return true;
    return v.priority_level === priorityFilter;
  });

  const waiting = filteredVisits.filter(
    (v) => v.status === "WAITING" || v.status === "ARRIVED"
  );
  const triaged = filteredVisits.filter((v) => v.status === "TRIAGED");
  const inCare = filteredVisits.filter((v) => v.status === "IN_CARE");
  const completed = [...recentlyCompleted].filter(
    (v) =>
      v.status === "ORIENTED" ||
      v.status === "DISCHARGED"
  );

  const totalPatients = visits.length;

  async function handleTriage(visitId: string) {
    try {
      await apiRequest(`/emergency/visits/${visitId}/triage`, {
        method: "POST",
        body: JSON.stringify({ priority_level: "NORMAL" }),
      });
      showToast("Patient trié avec succès.", "success");
      load();
      onCreated();
    } catch {
      showToast("Erreur lors du triage.", "error");
    }
  }

  async function handleTakeCharge(visitId: string) {
    try {
      await apiRequest(`/emergency/visits/${visitId}/care`, {
        method: "POST",
        body: JSON.stringify({
          attending_doctor_id: null,
          treatment_notes: "",
        }),
      });
      showToast("Patient pris en charge.", "success");
      load();
      onCreated();
    } catch {
      showToast("Erreur lors de la prise en charge.", "error");
    }
  }

  async function handleOrient(visitId: string) {
    try {
      await apiRequest(`/emergency/visits/${visitId}/orientation`, {
        method: "POST",
        body: JSON.stringify({ orientation: "CONSULTATION" }),
      });
      // Move to recently completed
      const visit = visits.find((v) => v.id === visitId);
      if (visit) {
        setRecentlyCompleted((prev) => [
          { ...visit, status: "ORIENTED" },
          ...prev.slice(0, 19),
        ]);
      }
      showToast("Patient orienté.", "success");
      load();
      onCreated();
    } catch {
      showToast("Erreur lors de l'orientation.", "error");
    }
  }

  async function handleDischarge(visitId: string) {
    try {
      await apiRequest(`/emergency/visits/${visitId}/discharge`, {
        method: "POST",
        body: JSON.stringify({
          discharge_summary: "Sortie des urgences",
          discharge_destination: "HOME",
        }),
      });
      const visit = visits.find((v) => v.id === visitId);
      if (visit) {
        setRecentlyCompleted((prev) => [
          { ...visit, status: "DISCHARGED" },
          ...prev.slice(0, 19),
        ]);
      }
      showToast("Patient sorti des urgences.", "success");
      load();
      onCreated();
    } catch {
      showToast("Erreur lors de la sortie.", "error");
    }
  }

  async function handleNewPatient() {
    if (!newPatientId || !newComplaint.trim()) {
      showToast("Veuillez remplir tous les champs obligatoires.", "error");
      return;
    }
    setSubmitting(true);
    try {
      const facilityId =
        lookups.facilities.length > 0 ? lookups.facilities[0].id : "";
      await apiRequest("/emergency/visits", {
        method: "POST",
        body: JSON.stringify({
          facility_id: facilityId,
          patient_id: newPatientId,
          chief_complaint: newComplaint.trim(),
          priority_level: "NORMAL",
        }),
      });
      showToast("Nouveau patient enregistré aux urgences.", "success");
      setShowNewPatientModal(false);
      setNewPatientId("");
      setNewComplaint("");
      setNewArrivalMode("WALK_IN");
      load();
      onCreated();
    } catch {
      showToast("Erreur lors de l'enregistrement.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  function getPatientData(patientId: string): Row | undefined {
    return lookups.patients.find((p) => p.id === patientId);
  }

  const patientOptions = lookups.patients.map((p) => ({
    id: p.id,
    label: `${p.first_name || ""} ${p.last_name || ""}`.trim() || p.patient_number || p.id,
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      {/* ── Top Bar ──────────────────────────────────────── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "12px",
          flexWrap: "wrap",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            flexWrap: "wrap",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 14px",
              background: "var(--card)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border)",
              fontSize: "14px",
              fontWeight: 600,
            }}
          >
            <User size={16} style={{ color: "var(--muted)" }} />
            {totalPatients} patient{totalPatients !== 1 ? "s" : ""}
          </div>

          {/* Priority Filter */}
          <div style={{ position: "relative" }}>
            <button
              onClick={() => setShowFilterDropdown(!showFilterDropdown)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 14px",
                background: "var(--card)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border)",
                fontSize: "14px",
                cursor: "pointer",
                fontFamily: "inherit",
                color: "var(--text)",
              }}
            >
              <Filter size={16} style={{ color: "var(--muted)" }} />
              {priorityFilter === "ALL"
                ? "Toutes priorités"
                : PRIORITY_CONFIG[priorityFilter]?.label || priorityFilter}
            </button>
            {showFilterDropdown && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  left: 0,
                  marginTop: "4px",
                  background: "var(--card)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border)",
                  boxShadow: "var(--shadow-md)",
                  zIndex: 100,
                  minWidth: "180px",
                  overflow: "hidden",
                }}
              >
                <button
                  onClick={() => {
                    setPriorityFilter("ALL");
                    setShowFilterDropdown(false);
                  }}
                  style={{
                    display: "block",
                    width: "100%",
                    padding: "10px 14px",
                    border: "none",
                    background: priorityFilter === "ALL" ? "var(--primary-light)" : "transparent",
                    cursor: "pointer",
                    textAlign: "left",
                    fontSize: "14px",
                    fontFamily: "inherit",
                    color: "var(--text)",
                  }}
                >
                  Toutes priorités
                </button>
                {Object.entries(PRIORITY_CONFIG).map(([key, cfg]) => (
                  <button
                    key={key}
                    onClick={() => {
                      setPriorityFilter(key);
                      setShowFilterDropdown(false);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      width: "100%",
                      padding: "10px 14px",
                      border: "none",
                      background:
                        priorityFilter === key ? cfg.bg : "transparent",
                      cursor: "pointer",
                      textAlign: "left",
                      fontSize: "14px",
                      fontFamily: "inherit",
                      color: "var(--text)",
                    }}
                  >
                    <span
                      style={{
                        width: "10px",
                        height: "10px",
                        borderRadius: "50%",
                        background: cfg.color,
                        flexShrink: 0,
                      }}
                    />
                    {cfg.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Auto Refresh Toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 14px",
              background: autoRefresh ? "var(--primary-light)" : "var(--card)",
              borderRadius: "var(--radius-md)",
              border: `1px solid ${autoRefresh ? "var(--primary)" : "var(--border)"}`,
              fontSize: "14px",
              cursor: "pointer",
              fontFamily: "inherit",
              color: autoRefresh ? "var(--primary)" : "var(--muted)",
              fontWeight: autoRefresh ? 600 : 400,
            }}
          >
            <RefreshCw
              size={16}
              style={{
                animation: autoRefresh
                  ? "spin 2s linear infinite"
                  : "none",
              }}
            />
            Auto
          </button>
        </div>

        <button
          onClick={() => setShowNewPatientModal(true)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "10px 18px",
            background: "var(--primary)",
            color: "white",
            borderRadius: "var(--radius-md)",
            border: "none",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            fontFamily: "inherit",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <Plus size={16} />
          Nouveau patient
        </button>
      </div>

      {/* ── Kanban Board ─────────────────────────────────── */}
      {loading && visits.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "48px",
            color: "var(--muted)",
          }}
        >
          <div className="spinner" />
          <p style={{ marginTop: "12px" }}>Chargement du tableau...</p>
        </div>
      ) : error ? (
        <div
          style={{
            padding: "24px",
            color: "var(--danger)",
            textAlign: "center",
          }}
        >
          {error}
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "12px",
            minHeight: "60vh",
          }}
        >
          {/* Column 1 - En attente */}
          <KanbanColumn
            title="En attente"
            count={waiting.length}
            headerColor="#b45309"
            headerBg="#fef3c7"
            icon={<Clock size={18} />}
          >
            {waiting.length === 0 ? (
              <EmptyColumn text="Aucun patient en attente" />
            ) : (
              waiting
                .sort((a, b) => {
                  const wa = getWaitMinutes(a.arrived_at);
                  const wb = getWaitMinutes(b.arrived_at);
                  return wb - wa;
                })
                .map((visit) => (
                  <PatientCard
                    key={visit.id}
                    visit={visit}
                    patientName={getPatientName(visit.patient_id)}
                    patientData={getPatientData(visit.patient_id)}
                    now={now}
                    actionLabel="Trier"
                    actionIcon={<ClipboardIcon />}
                    actionColor="#b45309"
                    actionBg="#fef3c7"
                    onAction={() => handleTriage(visit.id)}
                    showPriority={false}
                  />
                ))
            )}
          </KanbanColumn>

          {/* Column 2 - Triés */}
          <KanbanColumn
            title="Triés"
            count={triaged.length}
            headerColor="#1d4ed8"
            headerBg="#dbeafe"
            icon={<AlertTriangle size={18} />}
          >
            {triaged.length === 0 ? (
              <EmptyColumn text="Aucun patient trié" />
            ) : (
              triaged
                .sort((a, b) => {
                  const priorityOrder: Record<string, number> = {
                    CRITICAL: 0,
                    HIGH: 1,
                    NORMAL: 2,
                    LOW: 3,
                  };
                  return (
                    (priorityOrder[a.priority_level] ?? 2) -
                    (priorityOrder[b.priority_level] ?? 2)
                  );
                })
                .map((visit) => (
                  <PatientCard
                    key={visit.id}
                    visit={visit}
                    patientName={getPatientName(visit.patient_id)}
                    patientData={getPatientData(visit.patient_id)}
                    now={now}
                    actionLabel="Prendre en charge"
                    actionIcon={<Stethoscope size={14} />}
                    actionColor="#1d4ed8"
                    actionBg="#dbeafe"
                    onAction={() => handleTakeCharge(visit.id)}
                    showPriority={true}
                  />
                ))
            )}
          </KanbanColumn>

          {/* Column 3 - En soins */}
          <KanbanColumn
            title="En soins"
            count={inCare.length}
            headerColor="#047857"
            headerBg="#d1fae5"
            icon={<Heart size={18} />}
          >
            {inCare.length === 0 ? (
              <EmptyColumn text="Aucun patient en soins" />
            ) : (
              inCare.map((visit) => (
                <PatientCard
                  key={visit.id}
                  visit={visit}
                  patientName={getPatientName(visit.patient_id)}
                  patientData={getPatientData(visit.patient_id)}
                  now={now}
                  actionLabel="Orienter"
                  actionIcon={<ChevronRight size={14} />}
                  actionColor="#047857"
                  actionBg="#d1fae5"
                  onAction={() => handleOrient(visit.id)}
                  showPriority={true}
                  showCareInfo={true}
                  doctorName={
                    visit.attending_doctor_id
                      ? lookups.staff.find(
                          (s) => s.id === visit.attending_doctor_id
                        )?.first_name ||
                        lookups.staff.find(
                          (s) => s.id === visit.attending_doctor_id
                        )?.last_name ||
                        "Médecin"
                      : undefined
                  }
                  treatmentNotes={visit.treatment_notes}
                />
              ))
            )}
          </KanbanColumn>

          {/* Column 4 - Orientés / Sortis */}
          <KanbanColumn
            title="Orientés / Sortis"
            count={completed.length}
            headerColor="#64748b"
            headerBg="#f1f5f9"
            icon={<LogOut size={18} />}
          >
            {completed.length === 0 ? (
              <EmptyColumn text="Aucune sortie récente" />
            ) : (
              completed.map((visit) => (
                <PatientCard
                  key={visit.id}
                  visit={visit}
                  patientName={getPatientName(visit.patient_id)}
                  patientData={getPatientData(visit.patient_id)}
                  now={now}
                  actionLabel=""
                  actionIcon={null}
                  actionColor=""
                  actionBg=""
                  onAction={() => {}}
                  showPriority={true}
                  showDischargeInfo={true}
                  orientation={visit.orientation}
                  dischargeDestination={visit.discharge_destination}
                />
              ))
            )}
          </KanbanColumn>
        </div>
      )}

      {/* ── New Patient Modal ─────────────────────────────── */}
      {showNewPatientModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            display: "grid",
            placeItems: "center",
            zIndex: 1000,
          }}
          onClick={() => setShowNewPatientModal(false)}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "520px",
              margin: "24px",
              background: "var(--card)",
              borderRadius: "var(--radius-lg)",
              boxShadow: "var(--shadow-lg)",
              overflow: "hidden",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "20px 24px",
                borderBottom: "1px solid var(--border)",
                background: "var(--primary-light)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  fontWeight: 700,
                  fontSize: "16px",
                  color: "var(--primary)",
                }}
              >
                <Ambulance size={20} />
                Nouveau passage urgence
              </div>
              <button
                onClick={() => setShowNewPatientModal(false)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--muted)",
                  padding: "4px",
                }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Patient Selection */}
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    marginBottom: "6px",
                  }}
                >
                  Patient *
                </label>
                <select
                  value={newPatientId}
                  onChange={(e) => setNewPatientId(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)",
                    fontSize: "14px",
                    fontFamily: "inherit",
                    background: "white",
                    color: "var(--text)",
                  }}
                >
                  <option value="">— Sélectionner un patient —</option>
                  {patientOptions.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Chief Complaint */}
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    marginBottom: "6px",
                  }}
                >
                  Motif de consultation *
                </label>
                <textarea
                  value={newComplaint}
                  onChange={(e) => setNewComplaint(e.target.value)}
                  placeholder="Décrivez le motif d'urgence..."
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)",
                    fontSize: "14px",
                    fontFamily: "inherit",
                    background: "white",
                    color: "var(--text)",
                    minHeight: "80px",
                    resize: "vertical",
                  }}
                />
              </div>

              {/* Arrival Mode */}
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    marginBottom: "6px",
                  }}
                >
                  Mode d'arrivée
                </label>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "8px",
                  }}
                >
                  {ARRIVAL_MODES.map((mode) => (
                    <button
                      key={mode.value}
                      onClick={() => setNewArrivalMode(mode.value)}
                      style={{
                        padding: "10px 12px",
                        borderRadius: "var(--radius-md)",
                        border:
                          newArrivalMode === mode.value
                            ? "2px solid var(--primary)"
                            : "1px solid var(--border)",
                        background:
                          newArrivalMode === mode.value
                            ? "var(--primary-light)"
                            : "white",
                        color:
                          newArrivalMode === mode.value
                            ? "var(--primary)"
                            : "var(--text-secondary)",
                        fontWeight:
                          newArrivalMode === mode.value ? 600 : 400,
                        cursor: "pointer",
                        fontFamily: "inherit",
                        fontSize: "14px",
                      }}
                    >
                      {mode.value === "AMBULANCE" && (
                        <Ambulance
                          size={14}
                          style={{ marginRight: "6px", verticalAlign: "middle" }}
                        />
                      )}
                      {mode.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit */}
              <div
                style={{
                  display: "flex",
                  gap: "12px",
                  justifyContent: "flex-end",
                  paddingTop: "8px",
                }}
              >
                <button
                  onClick={() => setShowNewPatientModal(false)}
                  style={{
                    padding: "10px 20px",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid var(--border)",
                    background: "var(--card)",
                    fontSize: "14px",
                    cursor: "pointer",
                    fontFamily: "inherit",
                    color: "var(--text-secondary)",
                  }}
                >
                  Annuler
                </button>
                <button
                  onClick={handleNewPatient}
                  disabled={submitting || !newPatientId || !newComplaint.trim()}
                  style={{
                    padding: "10px 24px",
                    borderRadius: "var(--radius-md)",
                    border: "none",
                    background:
                      submitting || !newPatientId || !newComplaint.trim()
                        ? "var(--border)"
                        : "var(--primary)",
                    color: "white",
                    fontWeight: 600,
                    fontSize: "14px",
                    cursor:
                      submitting || !newPatientId || !newComplaint.trim()
                        ? "not-allowed"
                        : "pointer",
                    fontFamily: "inherit",
                  }}
                >
                  {submitting ? "Enregistrement..." : "Enregistrer"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Keyframe for spinner */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse-badge {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
    </div>
  );
}

/* ── Kanban Column ───────────────────────────────────────── */
function KanbanColumn({
  title,
  count,
  headerColor,
  headerBg,
  icon,
  children,
}: {
  title: string;
  count: number;
  headerColor: string;
  headerBg: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        background: "var(--bg)",
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--border-light)",
        overflow: "hidden",
        minHeight: "50vh",
      }}
    >
      {/* Column Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 16px",
          background: headerBg,
          borderBottom: `2px solid ${headerColor}`,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontWeight: 700,
            fontSize: "14px",
            color: headerColor,
          }}
        >
          {icon}
          {title}
        </div>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            minWidth: "24px",
            height: "24px",
            borderRadius: "12px",
            background: headerColor,
            color: "white",
            fontSize: "12px",
            fontWeight: 700,
            padding: "0 6px",
          }}
        >
          {count}
        </span>
      </div>

      {/* Column Body */}
      <div
        style={{
          flex: 1,
          padding: "10px",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          overflowY: "auto",
          maxHeight: "calc(100vh - 320px)",
        }}
      >
        {children}
      </div>
    </div>
  );
}

/* ── Patient Card ────────────────────────────────────────── */
function PatientCard({
  visit,
  patientName,
  patientData,
  now,
  actionLabel,
  actionIcon,
  actionColor,
  actionBg,
  onAction,
  showPriority,
  showCareInfo,
  doctorName,
  treatmentNotes,
  showDischargeInfo,
  orientation,
  dischargeDestination,
}: {
  visit: Row;
  patientName: string;
  patientData: Row | undefined;
  now: Date;
  actionLabel: string;
  actionIcon: React.ReactNode;
  actionColor: string;
  actionBg: string;
  onAction: () => void;
  showPriority: boolean;
  showCareInfo?: boolean;
  doctorName?: string;
  treatmentNotes?: string;
  showDischargeInfo?: boolean;
  orientation?: string;
  dischargeDestination?: string;
}) {
  const waitMinutes = getWaitMinutes(visit.arrived_at);
  const isOverWait = waitMinutes > 120;
  const priority = PRIORITY_CONFIG[visit.priority_level] || PRIORITY_CONFIG.NORMAL;

  return (
    <div
      style={{
        background: "var(--card)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--border-light)",
        boxShadow: "var(--shadow-xs)",
        padding: "12px",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        transition: "box-shadow 0.2s ease",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.boxShadow = "var(--shadow-md)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.boxShadow = "var(--shadow-xs)";
      }}
    >
      {/* Top row: Arrival time + Wait counter */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span style={{ fontSize: "12px", color: "var(--muted)" }}>
          {visit.arrived_at
            ? new Date(visit.arrived_at).toLocaleTimeString("fr-FR", {
                hour: "2-digit",
                minute: "2-digit",
              })
            : "—"}
        </span>
        <span
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "12px",
            fontWeight: 700,
            color: isOverWait ? "var(--danger)" : "var(--text-secondary)",
            background: isOverWait ? "var(--danger-light)" : "transparent",
            padding: isOverWait ? "2px 6px" : "0",
            borderRadius: "var(--radius-sm)",
          }}
        >
          <Clock size={12} />
          {formatWaitTime(waitMinutes)}
        </span>
      </div>

      {/* Patient name */}
      <div
        style={{
          fontWeight: 600,
          fontSize: "14px",
          color: "var(--text)",
          lineHeight: 1.3,
        }}
      >
        {patientName}
      </div>

      {/* Age / Gender */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span style={{ fontSize: "12px", color: "var(--muted)" }}>
          {getPatientAge(patientData)}
        </span>
        {getPatientGender(patientData) && (
          <span
            style={{
              fontSize: "12px",
              fontWeight: 600,
              color:
                getPatientGender(patientData) === "♀"
                  ? "#db2777"
                  : "#2563eb",
            }}
          >
            {getPatientGender(patientData)}
          </span>
        )}
      </div>

      {/* Chief Complaint */}
      {visit.chief_complaint && (
        <div
          style={{
            fontSize: "13px",
            color: "var(--text-secondary)",
            lineHeight: 1.4,
            padding: "6px 8px",
            background: "var(--border-light)",
            borderRadius: "var(--radius-sm)",
            borderLeft: "3px solid var(--primary)",
          }}
        >
          {visit.chief_complaint}
        </div>
      )}

      {/* Priority Badge (for triaged/in-care columns) */}
      {showPriority && visit.priority_level && (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            padding: "3px 10px",
            borderRadius: "9999px",
            fontSize: "12px",
            fontWeight: 700,
            color: priority.color,
            background: priority.bg,
            width: "fit-content",
            animation: priority.pulse ? "pulse-badge 1.5s ease-in-out infinite" : "none",
          }}
        >
          {priority.pulse && <AlertTriangle size={12} />}
          {priority.label}
        </span>
      )}

      {/* Care Info */}
      {showCareInfo && doctorName && (
        <div
          style={{
            fontSize: "12px",
            color: "var(--text-secondary)",
            display: "flex",
            alignItems: "center",
            gap: "4px",
          }}
        >
          <Stethoscope size={12} />
          Dr. {doctorName}
        </div>
      )}
      {showCareInfo && treatmentNotes && (
        <div
          style={{
            fontSize: "12px",
            color: "var(--muted)",
            fontStyle: "italic",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {treatmentNotes}
        </div>
      )}

      {/* Discharge/Orientation Info */}
      {showDischargeInfo && (
        <>
          {orientation && (
            <div
              style={{
                fontSize: "12px",
                color: "var(--text-secondary)",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <ArrowRightSmall />
              {orientation === "HOSPITALIZATION"
                ? "Hospitalisation"
                : orientation === "CONSULTATION"
                ? "Consultation"
                : orientation === "TRANSFERT"
                ? "Transfert"
                : orientation}
            </div>
          )}
          {dischargeDestination && (
            <div
              style={{
                fontSize: "12px",
                color: "var(--muted)",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <LogOut size={12} />
              {dischargeDestination === "HOME"
                ? "Domicile"
                : dischargeDestination === "HOSPITALIZATION"
                ? "Hospitalisation"
                : dischargeDestination === "TRANSFER"
                ? "Transfert"
                : dischargeDestination}
            </div>
          )}
        </>
      )}

      {/* Action Button */}
      {actionLabel && (
        <button
          onClick={onAction}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px",
            padding: "8px 12px",
            borderRadius: "var(--radius-md)",
            border: "none",
            background: actionBg,
            color: actionColor,
            fontWeight: 600,
            fontSize: "13px",
            cursor: "pointer",
            fontFamily: "inherit",
            transition: "all 0.15s ease",
            width: "100%",
          }}
        >
          {actionIcon}
          {actionLabel}
        </button>
      )}
    </div>
  );
}

/* ── Empty Column ────────────────────────────────────────── */
function EmptyColumn({ text }: { text: string }) {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "24px 12px",
        color: "var(--muted)",
        fontSize: "13px",
        fontStyle: "italic",
      }}
    >
      {text}
    </div>
  );
}

/* ── Small helpers ───────────────────────────────────────── */
function ClipboardIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
    </svg>
  );
}

function ArrowRightSmall() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  );
}
