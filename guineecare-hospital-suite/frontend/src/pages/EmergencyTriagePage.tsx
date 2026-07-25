import { useEffect, useState, useCallback } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import {
  Clock,
  AlertTriangle,
  User,
  Stethoscope,
  Thermometer,
  Heart,
  Activity,
  Droplets,
  Brain,
  ShieldAlert,
  ChevronRight,
  CheckCircle2,
  X,
} from "lucide-react";

const PRIORITY_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; description: string; icon: React.ReactNode }
> = {
  CRITICAL: {
    label: "Urgent",
    color: "#b91c1c",
    bg: "#fee2e2",
    description: "Menace vitale immédiate — réanimation",
    icon: <ShieldAlert size={24} />,
  },
  HIGH: {
    label: "Prioritaire",
    color: "#c2410c",
    bg: "#ffedd5",
    description: "Urgence grave — prise en charge rapide",
    icon: <AlertTriangle size={24} />,
  },
  NORMAL: {
    label: "Standard",
    color: "#1d4ed8",
    bg: "#dbeafe",
    description: "Urgence relative — délai acceptable",
    icon: <Clock size={24} />,
  },
  LOW: {
    label: "Non-urgent",
    color: "#047857",
    bg: "#d1fae5",
    description: "Consultation — sans urgence",
    icon: <CheckCircle2 size={24} />,
  },
};

const CRITICAL_CHECKS = [
  { key: "chest_pain", label: "Douleur thoracique", icon: <Heart size={16} /> },
  { key: "respiratory_distress", label: "Détresse respiratoire", icon: <Activity size={16} /> },
  { key: "consciousness_disorder", label: "Trouble conscience", icon: <Brain size={16} /> },
  { key: "hemorrhage", label: "Hémorragie", icon: <Droplets size={16} /> },
  { key: "anaphylactic_shock", label: "Choc anaphylactique", icon: <ShieldAlert size={16} /> },
];

function getWaitMinutes(arrivedAt: string): number {
  if (!arrivedAt) return 0;
  return Math.floor((Date.now() - new Date(arrivedAt).getTime()) / 60000);
}

function formatWaitTime(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h${m > 0 ? `${m}min` : ""}`;
}

export function EmergencyTriagePage({
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
  const [selectedVisitId, setSelectedVisitId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [now, setNow] = useState(new Date());

  // Triage form state
  const [priorityLevel, setPriorityLevel] = useState<string>("");
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [temperature, setTemperature] = useState("");
  const [bloodPressure, setBloodPressure] = useState("");
  const [heartRate, setHeartRate] = useState("");
  const [o2Saturation, setO2Saturation] = useState("");
  const [painLevel, setPainLevel] = useState(0);
  const [glasgow, setGlasgow] = useState(15);
  const [allergies, setAllergies] = useState(false);
  const [criticalChecks, setCriticalChecks] = useState<Record<string, boolean>>({});

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

  // Clock tick for wait counters
  useEffect(() => {
    const tick = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(tick);
  }, []);

  // Waiting patients sorted by arrival time (oldest first)
  const waitingPatients = visits
    .filter((v) => v.status === "WAITING" || v.status === "ARRIVED")
    .sort((a, b) => {
      const ta = new Date(a.arrived_at).getTime();
      const tb = new Date(b.arrived_at).getTime();
      return ta - tb;
    });

  const selectedVisit = visits.find((v) => v.id === selectedVisitId);

  function selectVisit(visitId: string) {
    const visit = visits.find((v) => v.id === visitId);
    setSelectedVisitId(visitId);
    setPriorityLevel(visit?.priority_level || "");
    setChiefComplaint(visit?.chief_complaint || "");
    setTemperature("");
    setBloodPressure("");
    setHeartRate("");
    setO2Saturation("");
    setPainLevel(0);
    setGlasgow(15);
    setAllergies(false);
    setCriticalChecks({});
  }

  function clearSelection() {
    setSelectedVisitId(null);
    setPriorityLevel("");
    setChiefComplaint("");
    setTemperature("");
    setBloodPressure("");
    setHeartRate("");
    setO2Saturation("");
    setPainLevel(0);
    setGlasgow(15);
    setAllergies(false);
    setCriticalChecks({});
  }

  function toggleCriticalCheck(key: string) {
    setCriticalChecks((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  // Auto-detect critical priority based on critical checks
  function getDetectedPriority(): string | null {
    const anyCritical = Object.values(criticalChecks).some(Boolean);
    if (anyCritical) return "CRITICAL";
    return null;
  }

  async function submitTriage() {
    if (!selectedVisitId) return;
    if (!priorityLevel) {
      showToast("Veuillez sélectionner un niveau de priorité.", "error");
      return;
    }

    setSubmitting(true);
    try {
      // Step 1: Triage
      await apiRequest(`/emergency/visits/${selectedVisitId}/triage`, {
        method: "POST",
        body: JSON.stringify({ priority_level: priorityLevel }),
      });

      // Step 2: Submit care/vitals if any vital sign entered
      const hasVitals =
        temperature || bloodPressure || heartRate || o2Saturation || painLevel > 0 || glasgow < 15;

      if (hasVitals) {
        const vitalSigns = JSON.stringify({
          temperature: temperature || null,
          blood_pressure: bloodPressure || null,
          heart_rate: heartRate || null,
          o2_saturation: o2Saturation || null,
          pain_level: painLevel,
          glasgow: glasgow,
          allergies: allergies,
          critical_flags: Object.entries(criticalChecks)
            .filter(([, v]) => v)
            .map(([k]) => k),
        });

        await apiRequest(`/emergency/visits/${selectedVisitId}/care`, {
          method: "POST",
          body: JSON.stringify({
            vital_signs: vitalSigns,
            treatment_notes: chiefComplaint !== selectedVisit?.chief_complaint ? chiefComplaint : undefined,
          }),
        });
      }

      showToast("Triage enregistré avec succès.", "success");
      clearSelection();
      load();
      onCreated();
    } catch {
      showToast("Erreur lors de l'enregistrement du triage.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const detectedPriority = getDetectedPriority();

  return (
    <div style={{ display: "flex", gap: "16px", minHeight: "70vh" }}>
      {/* ── Left Panel: Waiting Patients ────────────────── */}
      <div
        style={{
          width: "340px",
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
          background: "var(--card)",
          borderRadius: "var(--radius-lg)",
          border: "1px solid var(--border-light)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "16px",
            borderBottom: "1px solid var(--border)",
            fontWeight: 700,
            fontSize: "15px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            color: "var(--text)",
          }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Clock size={18} style={{ color: "#b45309" }} />
            En attente de triage
          </span>
          <span
            style={{
              background: "#fef3c7",
              color: "#b45309",
              padding: "2px 10px",
              borderRadius: "9999px",
              fontSize: "13px",
              fontWeight: 700,
            }}
          >
            {waitingPatients.length}
          </span>
        </div>

        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "8px",
            display: "flex",
            flexDirection: "column",
            gap: "6px",
          }}
        >
          {loading ? (
            <div style={{ textAlign: "center", padding: "24px", color: "var(--muted)" }}>
              <div className="spinner" />
            </div>
          ) : waitingPatients.length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "24px",
                color: "var(--muted)",
                fontSize: "14px",
              }}
            >
              Aucun patient en attente
            </div>
          ) : (
            waitingPatients.map((visit) => {
              const waitMin = getWaitMinutes(visit.arrived_at);
              const isOver = waitMin > 120;
              const isSelected = selectedVisitId === visit.id;
              return (
                <button
                  key={visit.id}
                  onClick={() => selectVisit(visit.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "12px",
                    borderRadius: "var(--radius-md)",
                    border: isSelected
                      ? "2px solid var(--primary)"
                      : "1px solid var(--border-light)",
                    background: isSelected ? "var(--primary-light)" : "var(--card)",
                    cursor: "pointer",
                    textAlign: "left",
                    fontFamily: "inherit",
                    width: "100%",
                    transition: "all 0.15s ease",
                  }}
                >
                  <div
                    style={{
                      width: "36px",
                      height: "36px",
                      borderRadius: "50%",
                      background: isSelected ? "var(--primary)" : "var(--border-light)",
                      color: isSelected ? "white" : "var(--muted)",
                      display: "grid",
                      placeItems: "center",
                      fontSize: "14px",
                      fontWeight: 700,
                      flexShrink: 0,
                    }}
                  >
                    {getPatientName(visit.patient_id)
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .substring(0, 2)
                      .toUpperCase()}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontWeight: 600,
                        fontSize: "14px",
                        color: "var(--text)",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {getPatientName(visit.patient_id)}
                    </div>
                    <div
                      style={{
                        fontSize: "12px",
                        color: "var(--muted)",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {visit.chief_complaint || "Motif non renseigné"}
                    </div>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "flex-end",
                      gap: "2px",
                      flexShrink: 0,
                    }}
                  >
                    <span
                      style={{
                        fontSize: "11px",
                        color: "var(--muted)",
                      }}
                    >
                      {visit.arrived_at
                        ? new Date(visit.arrived_at).toLocaleTimeString("fr-FR", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : ""}
                    </span>
                    <span
                      style={{
                        fontSize: "12px",
                        fontWeight: 700,
                        color: isOver ? "var(--danger)" : "var(--text-secondary)",
                      }}
                    >
                      {formatWaitTime(waitMin)}
                    </span>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* ── Right Panel: Triage Form ────────────────────── */}
      <div
        style={{
          flex: 1,
          background: "var(--card)",
          borderRadius: "var(--radius-lg)",
          border: "1px solid var(--border-light)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {!selectedVisit ? (
          <div
            style={{
              flex: 1,
              display: "grid",
              placeItems: "center",
              color: "var(--muted)",
              fontSize: "15px",
            }}
          >
            <div style={{ textAlign: "center" }}>
              <Stethoscope size={48} style={{ color: "var(--border)", marginBottom: "12px" }} />
              <p>Sélectionnez un patient pour le trier</p>
            </div>
          </div>
        ) : (
          <>
            {/* Selected Patient Header */}
            <div
              style={{
                padding: "16px 20px",
                borderBottom: "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                background: "var(--primary-light)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                }}
              >
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "50%",
                    background: "var(--primary)",
                    color: "white",
                    display: "grid",
                    placeItems: "center",
                    fontSize: "16px",
                    fontWeight: 700,
                  }}
                >
                  {getPatientName(selectedVisit.patient_id)
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .substring(0, 2)
                    .toUpperCase()}
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: "16px", color: "var(--text)" }}>
                    {getPatientName(selectedVisit.patient_id)}
                  </div>
                  <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                    Arrivé à{" "}
                    {selectedVisit.arrived_at
                      ? new Date(selectedVisit.arrived_at).toLocaleTimeString("fr-FR", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "—"}{" "}
                    · Attente:{" "}
                    {formatWaitTime(getWaitMinutes(selectedVisit.arrived_at))}
                  </div>
                </div>
              </div>
              <button
                onClick={clearSelection}
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

            {/* Triage Form Content */}
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "20px",
                display: "flex",
                flexDirection: "column",
                gap: "24px",
              }}
            >
              {/* Critical Assessment Flags */}
              <div>
                <div
                  style={{
                    fontSize: "13px",
                    fontWeight: 700,
                    color: "var(--danger)",
                    marginBottom: "10px",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <ShieldAlert size={16} />
                  Évaluation rapide — Signes d'urgence
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
                    gap: "8px",
                  }}
                >
                  {CRITICAL_CHECKS.map((check) => (
                    <label
                      key={check.key}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        padding: "10px 12px",
                        borderRadius: "var(--radius-md)",
                        border: criticalChecks[check.key]
                          ? "2px solid var(--danger)"
                          : "1px solid var(--border)",
                        background: criticalChecks[check.key]
                          ? "var(--danger-light)"
                          : "var(--card)",
                        cursor: "pointer",
                        fontSize: "14px",
                        fontWeight: criticalChecks[check.key] ? 600 : 400,
                        color: criticalChecks[check.key]
                          ? "var(--danger)"
                          : "var(--text)",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={!!criticalChecks[check.key]}
                        onChange={() => toggleCriticalCheck(check.key)}
                        style={{ display: "none" }}
                      />
                      {check.icon}
                      {check.label}
                    </label>
                  ))}
                </div>
                {detectedPriority && (
                  <div
                    style={{
                      marginTop: "8px",
                      padding: "8px 12px",
                      borderRadius: "var(--radius-md)",
                      background: PRIORITY_CONFIG[detectedPriority].bg,
                      color: PRIORITY_CONFIG[detectedPriority].color,
                      fontSize: "13px",
                      fontWeight: 600,
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <AlertTriangle size={14} />
                    Signe d'urgence détecté — Priorité{" "}
                    {PRIORITY_CONFIG[detectedPriority].label} recommandée
                  </div>
                )}
              </div>

              {/* Priority Level Selection */}
              <div>
                <div
                  style={{
                    fontSize: "13px",
                    fontWeight: 700,
                    color: "var(--text-secondary)",
                    marginBottom: "10px",
                  }}
                >
                  Niveau de priorité
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(4, 1fr)",
                    gap: "10px",
                  }}
                >
                  {Object.entries(PRIORITY_CONFIG).map(([key, cfg]) => (
                    <button
                      key={key}
                      onClick={() => setPriorityLevel(key)}
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: "6px",
                        padding: "16px 10px",
                        borderRadius: "var(--radius-md)",
                        border: priorityLevel === key
                          ? `2px solid ${cfg.color}`
                          : "1px solid var(--border)",
                        background: priorityLevel === key ? cfg.bg : "var(--card)",
                        cursor: "pointer",
                        fontFamily: "inherit",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <span style={{ color: cfg.color }}>{cfg.icon}</span>
                      <span
                        style={{
                          fontSize: "14px",
                          fontWeight: priorityLevel === key ? 700 : 500,
                          color: priorityLevel === key ? cfg.color : "var(--text)",
                        }}
                      >
                        {cfg.label}
                      </span>
                      <span
                        style={{
                          fontSize: "11px",
                          color: "var(--muted)",
                          textAlign: "center",
                          lineHeight: 1.3,
                        }}
                      >
                        {cfg.description}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Chief Complaint */}
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "13px",
                    fontWeight: 700,
                    color: "var(--text-secondary)",
                    marginBottom: "6px",
                  }}
                >
                  Motif de consultation
                </label>
                <textarea
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
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
                    minHeight: "72px",
                    resize: "vertical",
                  }}
                />
              </div>

              {/* Vital Signs Grid */}
              <div>
                <div
                  style={{
                    fontSize: "13px",
                    fontWeight: 700,
                    color: "var(--text-secondary)",
                    marginBottom: "10px",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <Activity size={16} />
                  Constantes vitales
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(3, 1fr)",
                    gap: "12px",
                  }}
                >
                  {/* Temperature */}
                  <VitalInput
                    label="Température"
                    icon={<Thermometer size={16} />}
                    value={temperature}
                    onChange={setTemperature}
                    placeholder="37.0"
                    unit="°C"
                    color="#dc2626"
                  />
                  {/* Blood Pressure */}
                  <VitalInput
                    label="Tension artérielle"
                    icon={<Heart size={16} />}
                    value={bloodPressure}
                    onChange={setBloodPressure}
                    placeholder="120/80"
                    unit="mmHg"
                    color="#7c3aed"
                  />
                  {/* Heart Rate */}
                  <VitalInput
                    label="Fréquence cardiaque"
                    icon={<Activity size={16} />}
                    value={heartRate}
                    onChange={setHeartRate}
                    placeholder="72"
                    unit="bpm"
                    color="#dc2626"
                  />
                  {/* O2 Saturation */}
                  <VitalInput
                    label="Saturation O₂"
                    icon={<Droplets size={16} />}
                    value={o2Saturation}
                    onChange={setO2Saturation}
                    placeholder="98"
                    unit="%"
                    color="#2563eb"
                  />
                  {/* Pain Level */}
                  <div>
                    <label
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                        fontSize: "12px",
                        fontWeight: 600,
                        color: "var(--text-secondary)",
                        marginBottom: "6px",
                      }}
                    >
                      <ShieldAlert size={14} style={{ color: "#dc2626" }} />
                      Douleur (EVA)
                      <span
                        style={{
                          marginLeft: "auto",
                          fontWeight: 700,
                          color:
                            painLevel <= 3
                              ? "#047857"
                              : painLevel <= 6
                              ? "#c2410c"
                              : "#b91c1c",
                          fontSize: "14px",
                        }}
                      >
                        {painLevel}/10
                      </span>
                    </label>
                    <div style={{ display: "flex", gap: "3px" }}>
                      {Array.from({ length: 11 }, (_, i) => (
                        <button
                          key={i}
                          onClick={() => setPainLevel(i)}
                          style={{
                            flex: 1,
                            height: "32px",
                            border: "none",
                            borderRadius:
                              i === 0
                                ? "var(--radius-sm) 0 0 var(--radius-sm)"
                                : i === 10
                                ? "0 var(--radius-sm) var(--radius-sm) 0"
                                : "0",
                            background:
                              painLevel >= i
                                ? i <= 3
                                  ? "#d1fae5"
                                  : i <= 6
                                  ? "#ffedd5"
                                  : "#fee2e2"
                                : "var(--border-light)",
                            cursor: "pointer",
                            fontSize: "10px",
                            fontWeight: painLevel === i ? 700 : 400,
                            color:
                              painLevel >= i
                                ? i <= 3
                                  ? "#047857"
                                  : i <= 6
                                  ? "#c2410c"
                                  : "#b91c1c"
                                : "var(--muted)",
                            padding: 0,
                            fontFamily: "inherit",
                          }}
                        >
                          {i}
                        </button>
                      ))}
                    </div>
                  </div>
                  {/* Glasgow */}
                  <div>
                    <label
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                        fontSize: "12px",
                        fontWeight: 600,
                        color: "var(--text-secondary)",
                        marginBottom: "6px",
                      }}
                    >
                      <Brain size={14} style={{ color: "#7c3aed" }} />
                      Glasgow
                      <span
                        style={{
                          marginLeft: "auto",
                          fontWeight: 700,
                          color: glasgow < 9 ? "#b91c1c" : glasgow < 13 ? "#c2410c" : "#047857",
                          fontSize: "14px",
                        }}
                      >
                        {glasgow}/15
                      </span>
                    </label>
                    <div style={{ display: "flex", gap: "2px" }}>
                      {Array.from({ length: 13 }, (_, i) => i + 3).map((val) => (
                        <button
                          key={val}
                          onClick={() => setGlasgow(val)}
                          style={{
                            flex: 1,
                            height: "32px",
                            border: "none",
                            borderRadius: "0",
                            background:
                              glasgow === val
                                ? val < 9
                                  ? "#fee2e2"
                                  : val < 13
                                  ? "#ffedd5"
                                  : "#d1fae5"
                                : "var(--border-light)",
                            cursor: "pointer",
                            fontSize: "10px",
                            fontWeight: glasgow === val ? 700 : 400,
                            color:
                              glasgow === val
                                ? val < 9
                                  ? "#b91c1c"
                                  : val < 13
                                  ? "#c2410c"
                                  : "#047857"
                                : "var(--muted)",
                            padding: 0,
                            fontFamily: "inherit",
                          }}
                        >
                          {val}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Allergies */}
              <div>
                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    cursor: "pointer",
                    padding: "12px 16px",
                    borderRadius: "var(--radius-md)",
                    border: allergies ? "2px solid #c2410c" : "1px solid var(--border)",
                    background: allergies ? "#ffedd5" : "var(--card)",
                    fontWeight: allergies ? 600 : 400,
                    color: allergies ? "#c2410c" : "var(--text-secondary)",
                    fontSize: "14px",
                    transition: "all 0.15s ease",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={allergies}
                    onChange={(e) => setAllergies(e.target.checked)}
                    style={{ width: "18px", height: "18px" }}
                  />
                  <AlertTriangle size={16} />
                  Patient allergique connu
                </label>
              </div>

              {/* Submit */}
              <div
                style={{
                  display: "flex",
                  gap: "12px",
                  justifyContent: "flex-end",
                  paddingTop: "8px",
                  borderTop: "1px solid var(--border)",
                }}
              >
                <button
                  onClick={clearSelection}
                  style={{
                    padding: "12px 24px",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid var(--border)",
                    background: "var(--card)",
                    color: "var(--text-secondary)",
                    fontSize: "14px",
                    fontWeight: 500,
                    cursor: "pointer",
                    fontFamily: "inherit",
                  }}
                >
                  Annuler
                </button>
                <button
                  onClick={submitTriage}
                  disabled={submitting || !priorityLevel}
                  style={{
                    padding: "12px 32px",
                    borderRadius: "var(--radius-md)",
                    border: "none",
                    background:
                      submitting || !priorityLevel
                        ? "var(--border)"
                        : "var(--primary)",
                    color: "white",
                    fontWeight: 700,
                    fontSize: "14px",
                    cursor:
                      submitting || !priorityLevel ? "not-allowed" : "pointer",
                    fontFamily: "inherit",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <CheckCircle2 size={16} />
                  {submitting
                    ? "Enregistrement..."
                    : "Valider le triage"}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ── Vital Input Component ───────────────────────────────── */
function VitalInput({
  label,
  icon,
  value,
  onChange,
  placeholder,
  unit,
  color,
}: {
  label: string;
  icon: React.ReactNode;
  value: string;
  onChange: (val: string) => void;
  placeholder: string;
  unit: string;
  color: string;
}) {
  return (
    <div>
      <label
        style={{
          display: "flex",
          alignItems: "center",
          gap: "4px",
          fontSize: "12px",
          fontWeight: 600,
          color: "var(--text-secondary)",
          marginBottom: "6px",
        }}
      >
        <span style={{ color }}>{icon}</span>
        {label}
      </label>
      <div style={{ position: "relative" }}>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          style={{
            width: "100%",
            padding: "8px 40px 8px 10px",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            fontSize: "14px",
            fontFamily: "inherit",
            background: "white",
            color: "var(--text)",
          }}
        />
        <span
          style={{
            position: "absolute",
            right: "10px",
            top: "50%",
            transform: "translateY(-50%)",
            fontSize: "12px",
            color: "var(--muted)",
            fontWeight: 500,
          }}
        >
          {unit}
        </span>
      </div>
    </div>
  );
}
