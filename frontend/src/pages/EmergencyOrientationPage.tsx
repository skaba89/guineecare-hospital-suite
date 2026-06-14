import { useEffect, useState, useCallback } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  ArrowRightLeft,
  Clock,
  AlertTriangle,
  Building2,
  BedDouble,
  LogOut,
  X,
  CheckCircle2,
  Stethoscope,
  FileText,
  Home,
  Ambulance,
  Building,
  User,
} from "lucide-react";

const PRIORITY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  LOW: { label: "Basse", color: "#047857", bg: "#d1fae5" },
  NORMAL: { label: "Normale", color: "#1d4ed8", bg: "#dbeafe" },
  HIGH: { label: "Haute", color: "#c2410c", bg: "#ffedd5" },
  CRITICAL: { label: "Critique", color: "#b91c1c", bg: "#fee2e2" },
};

const DESTINATION_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  HOSPITALIZATION: {
    label: "Hospitalisation",
    icon: <BedDouble size={20} />,
    color: "#7c3aed",
  },
  CONSULTATION: {
    label: "Consultation",
    icon: <Stethoscope size={20} />,
    color: "#2563eb",
  },
  DISCHARGE: {
    label: "Sortie",
    icon: <Home size={20} />,
    color: "#047857",
  },
  TRANSFER: {
    label: "Transfert",
    icon: <Ambulance size={20} />,
    color: "#c2410c",
  },
};

const PIE_COLORS = ["#7c3aed", "#2563eb", "#047857", "#c2410c"];

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

export function EmergencyOrientationPage({
  lookups,
  onCreated,
  getPatientName,
}: {
  lookups: LookupData;
  onCreated: () => void;
  getPatientName: (id: string) => string;
}) {
  const [visits, setVisits] = useState<Row[]>([]);
  const [beds, setBeds] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [orientingVisitId, setOrientingVisitId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Orientation form state
  const [destination, setDestination] = useState("HOSPITALIZATION");
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [selectedBed, setSelectedBed] = useState("");
  const [selectedFacility, setSelectedFacility] = useState("");
  const [dischargeSummary, setDischargeSummary] = useState("");
  const [orientationNotes, setOrientationNotes] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/emergency/queue");
      const allVisits = Array.isArray(payload.data) ? payload.data : [];
      setVisits(allVisits);

      // Load beds for hospitalization orientation
      try {
        const bedsPayload = await apiRequest<any>("/hospitalization/beds");
        const allBeds = Array.isArray(bedsPayload.data) ? bedsPayload.data : [];
        setBeds(allBeds.filter((b: Row) => b.bed_status === "AVAILABLE"));
      } catch {
        setBeds([]);
      }
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

  // Patients needing orientation
  const orientablePatients = visits.filter(
    (v) => v.status === "TRIAGED" || v.status === "IN_CARE"
  );

  // Stats
  const waitingOrientation = orientablePatients.length;
  const waitTimes = orientablePatients.map((v) => getWaitMinutes(v.arrived_at));
  const avgWaitTime =
    waitTimes.length > 0
      ? Math.round(waitTimes.reduce((a, b) => a + b, 0) / waitTimes.length)
      : 0;

  // Destination breakdown for pie chart
  const destinationBreakdown = [
    { name: "Hospitalisation", value: orientablePatients.filter((v) => v.priority_level === "CRITICAL" || v.priority_level === "HIGH").length },
    { name: "Consultation", value: orientablePatients.filter((v) => v.priority_level === "NORMAL").length },
    { name: "Sortie", value: orientablePatients.filter((v) => v.priority_level === "LOW").length },
    { name: "Transfert", value: 0 },
  ].filter((d) => d.value > 0);

  function openOrientation(visitId: string) {
    setOrientingVisitId(visitId);
    setDestination("HOSPITALIZATION");
    setSelectedDepartment("");
    setSelectedBed("");
    setSelectedFacility("");
    setDischargeSummary("");
    setOrientationNotes("");
  }

  function closeOrientation() {
    setOrientingVisitId(null);
  }

  async function submitOrientation() {
    if (!orientingVisitId) return;
    setSubmitting(true);
    try {
      const visit = visits.find((v) => v.id === orientingVisitId);

      if (visit?.status === "IN_CARE") {
        // Discharge from care first, then orient
        await apiRequest(`/emergency/visits/${orientingVisitId}/discharge`, {
          method: "POST",
          body: JSON.stringify({
            discharge_summary: dischargeSummary || "Sortie des urgences",
            discharge_destination:
              destination === "HOSPITALIZATION"
                ? "HOSPITALIZATION"
                : destination === "TRANSFER"
                ? "TRANSFER"
                : "HOME",
            orientation: destination,
          }),
        });
      } else {
        // For TRIAGED patients - orient them
        await apiRequest(`/emergency/visits/${orientingVisitId}/orientation`, {
          method: "POST",
          body: JSON.stringify({
            orientation: destination,
          }),
        });

        // If there's a discharge summary for TRIAGED → discharge
        if (destination === "DISCHARGE" && dischargeSummary) {
          try {
            await apiRequest(`/emergency/visits/${orientingVisitId}/discharge`, {
              method: "POST",
              body: JSON.stringify({
                discharge_summary: dischargeSummary,
                discharge_destination: "HOME",
              }),
            });
          } catch {
            // Visit may not be in IN_CARE status for discharge
          }
        }
      }

      showToast("Orientation enregistrée avec succès.", "success");
      closeOrientation();
      load();
      onCreated();
    } catch (err: any) {
      showToast(err?.message || "Erreur lors de l'orientation.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function quickDischarge(visitId: string) {
    try {
      const visit = visits.find((v) => v.id === visitId);
      if (visit?.status === "IN_CARE") {
        await apiRequest(`/emergency/visits/${visitId}/discharge`, {
          method: "POST",
          body: JSON.stringify({
            discharge_summary: "Sortie sur conseil médical",
            discharge_destination: "HOME",
          }),
        });
      } else {
        await apiRequest(`/emergency/visits/${visitId}/orientation`, {
          method: "POST",
          body: JSON.stringify({ orientation: "DISCHARGE" }),
        });
      }
      showToast("Sortie enregistrée.", "success");
      load();
      onCreated();
    } catch {
      showToast("Erreur lors de la sortie.", "error");
    }
  }

  // Available beds filtered by department
  const filteredBeds = selectedDepartment
    ? beds.filter((b) => {
        const room = lookups.departments.find((d) => d.id === selectedDepartment);
        return room ? true : true; // Show all available beds, the API doesn't directly link rooms to departments in this lookup
      })
    : beds;

  const orientingVisit = visits.find((v) => v.id === orientingVisitId);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* ── Summary Stats ──────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: "12px",
        }}
      >
        {/* Waiting Orientation */}
        <div
          style={{
            padding: "20px",
            background: "var(--card)",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--border-light)",
            boxShadow: "var(--shadow-xs)",
            display: "flex",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "var(--radius-md)",
              background: "#dbeafe",
              color: "#1d4ed8",
              display: "grid",
              placeItems: "center",
              flexShrink: 0,
            }}
          >
            <ArrowRightLeft size={24} />
          </div>
          <div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "var(--text)", lineHeight: 1.1 }}>
              {waitingOrientation}
            </div>
            <div style={{ fontSize: "13px", color: "var(--muted)", fontWeight: 500 }}>
              En attente d'orientation
            </div>
          </div>
        </div>

        {/* Average Wait Time */}
        <div
          style={{
            padding: "20px",
            background: "var(--card)",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--border-light)",
            boxShadow: "var(--shadow-xs)",
            display: "flex",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "var(--radius-md)",
              background: avgWaitTime > 120 ? "#fee2e2" : "#fef3c7",
              color: avgWaitTime > 120 ? "#b91c1c" : "#b45309",
              display: "grid",
              placeItems: "center",
              flexShrink: 0,
            }}
          >
            <Clock size={24} />
          </div>
          <div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "var(--text)", lineHeight: 1.1 }}>
              {formatWaitTime(avgWaitTime)}
            </div>
            <div style={{ fontSize: "13px", color: "var(--muted)", fontWeight: 500 }}>
              Temps d'attente moyen
            </div>
          </div>
        </div>

        {/* Destination Breakdown Chart */}
        <div
          style={{
            padding: "16px",
            background: "var(--card)",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--border-light)",
            boxShadow: "var(--shadow-xs)",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          {destinationBreakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={80}>
              <PieChart>
                <Pie
                  data={destinationBreakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={20}
                  outerRadius={35}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {destinationBreakdown.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={PIE_COLORS[index % PIE_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any, name: any) => [`${value} patients`, name]}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div
              style={{
                width: "100%",
                textAlign: "center",
                color: "var(--muted)",
                fontSize: "13px",
                padding: "12px",
              }}
            >
              Aucune donnée
            </div>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: "4px", minWidth: 0 }}>
            {destinationBreakdown.map((d, i) => (
              <div
                key={d.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  fontSize: "11px",
                  color: "var(--text-secondary)",
                }}
              >
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "2px",
                    background: PIE_COLORS[i % PIE_COLORS.length],
                    flexShrink: 0,
                  }}
                />
                {d.name}: {d.value}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Patient Table ────────────────────────────────── */}
      <div
        style={{
          background: "var(--card)",
          borderRadius: "var(--radius-lg)",
          border: "1px solid var(--border-light)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ fontWeight: 700, fontSize: "15px", color: "var(--text)" }}>
            Patients à orienter
          </div>
          <span
            style={{
              fontSize: "13px",
              color: "var(--muted)",
              background: "var(--border-light)",
              padding: "4px 10px",
              borderRadius: "9999px",
            }}
          >
            {orientablePatients.length} patient{orientablePatients.length !== 1 ? "s" : ""}
          </span>
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: "32px", color: "var(--muted)" }}>
            <div className="spinner" />
            <p style={{ marginTop: "12px" }}>Chargement...</p>
          </div>
        ) : error ? (
          <div style={{ padding: "24px", color: "var(--danger)", textAlign: "center" }}>
            {error}
          </div>
        ) : orientablePatients.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: "48px 24px",
              color: "var(--muted)",
            }}
          >
            <CheckCircle2
              size={40}
              style={{ color: "var(--border)", marginBottom: "12px" }}
            />
            <p>Aucun patient en attente d'orientation.</p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "14px",
              }}
            >
              <thead>
                <tr
                  style={{
                    borderBottom: "2px solid var(--border)",
                  }}
                >
                  <th
                    style={{
                      padding: "12px 16px",
                      textAlign: "left",
                      fontSize: "12px",
                      fontWeight: 700,
                      color: "var(--muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                    }}
                  >
                    Patient
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      textAlign: "left",
                      fontSize: "12px",
                      fontWeight: 700,
                      color: "var(--muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                    }}
                  >
                    Priorité
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      textAlign: "left",
                      fontSize: "12px",
                      fontWeight: 700,
                      color: "var(--muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                    }}
                  >
                    Attente
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      textAlign: "left",
                      fontSize: "12px",
                      fontWeight: 700,
                      color: "var(--muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                    }}
                  >
                    Motif
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      textAlign: "left",
                      fontSize: "12px",
                      fontWeight: 700,
                      color: "var(--muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                    }}
                  >
                    Statut
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      textAlign: "right",
                      fontSize: "12px",
                      fontWeight: 700,
                      color: "var(--muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                    }}
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {orientablePatients
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
                  .map((visit) => {
                    const priority =
                      PRIORITY_CONFIG[visit.priority_level] || PRIORITY_CONFIG.NORMAL;
                    const waitMin = getWaitMinutes(visit.arrived_at);
                    const isOver = waitMin > 120;

                    return (
                      <tr
                        key={visit.id}
                        style={{
                          borderBottom: "1px solid var(--border-light)",
                          transition: "background 0.15s ease",
                        }}
                        onMouseEnter={(e) => {
                          (e.currentTarget as HTMLTableRowElement).style.background =
                            "var(--border-light)";
                        }}
                        onMouseLeave={(e) => {
                          (e.currentTarget as HTMLTableRowElement).style.background =
                            "transparent";
                        }}
                      >
                        <td style={{ padding: "12px 16px" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                            <div
                              style={{
                                width: "32px",
                                height: "32px",
                                borderRadius: "50%",
                                background: priority.bg,
                                color: priority.color,
                                display: "grid",
                                placeItems: "center",
                                fontSize: "12px",
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
                            <div>
                              <div style={{ fontWeight: 600, color: "var(--text)" }}>
                                {getPatientName(visit.patient_id)}
                              </div>
                              <div style={{ fontSize: "12px", color: "var(--muted)" }}>
                                Arrivé{" "}
                                {visit.arrived_at
                                  ? new Date(visit.arrived_at).toLocaleTimeString(
                                      "fr-FR",
                                      { hour: "2-digit", minute: "2-digit" }
                                    )
                                  : "—"}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td style={{ padding: "12px 16px" }}>
                          <span
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              padding: "4px 10px",
                              borderRadius: "9999px",
                              fontSize: "12px",
                              fontWeight: 700,
                              color: priority.color,
                              background: priority.bg,
                            }}
                          >
                            {visit.priority_level === "CRITICAL" && (
                              <AlertTriangle size={12} />
                            )}
                            {priority.label}
                          </span>
                        </td>
                        <td style={{ padding: "12px 16px" }}>
                          <span
                            style={{
                              fontWeight: 700,
                              color: isOver ? "var(--danger)" : "var(--text)",
                              fontSize: "14px",
                            }}
                          >
                            {formatWaitTime(waitMin)}
                          </span>
                        </td>
                        <td style={{ padding: "12px 16px", maxWidth: "200px" }}>
                          <span
                            style={{
                              fontSize: "13px",
                              color: "var(--text-secondary)",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                              display: "block",
                            }}
                          >
                            {visit.chief_complaint || "—"}
                          </span>
                        </td>
                        <td style={{ padding: "12px 16px" }}>
                          <span
                            style={{
                              fontSize: "13px",
                              fontWeight: 600,
                              color:
                                visit.status === "IN_CARE"
                                  ? "#047857"
                                  : "#1d4ed8",
                            }}
                          >
                            {visit.status === "IN_CARE" ? "En soins" : "Trié"}
                          </span>
                        </td>
                        <td
                          style={{
                            padding: "12px 16px",
                            textAlign: "right",
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              gap: "8px",
                              justifyContent: "flex-end",
                            }}
                          >
                            <button
                              onClick={() => openOrientation(visit.id)}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "4px",
                                padding: "8px 14px",
                                borderRadius: "var(--radius-md)",
                                border: "1px solid var(--primary)",
                                background: "var(--primary-light)",
                                color: "var(--primary)",
                                fontWeight: 600,
                                fontSize: "13px",
                                cursor: "pointer",
                                fontFamily: "inherit",
                                transition: "all 0.15s ease",
                              }}
                            >
                              <ArrowRightLeft size={14} />
                              Orienter
                            </button>
                            <button
                              onClick={() => quickDischarge(visit.id)}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "4px",
                                padding: "8px 14px",
                                borderRadius: "var(--radius-md)",
                                border: "1px solid var(--border)",
                                background: "var(--card)",
                                color: "var(--muted)",
                                fontWeight: 500,
                                fontSize: "13px",
                                cursor: "pointer",
                                fontFamily: "inherit",
                                transition: "all 0.15s ease",
                              }}
                            >
                              <LogOut size={14} />
                              Sortie
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Orientation Modal ─────────────────────────────── */}
      {orientingVisitId && orientingVisit && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            display: "grid",
            placeItems: "center",
            zIndex: 1000,
          }}
          onClick={closeOrientation}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "560px",
              margin: "24px",
              background: "var(--card)",
              borderRadius: "var(--radius-lg)",
              boxShadow: "var(--shadow-lg)",
              overflow: "hidden",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: "20px 24px",
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
                  gap: "10px",
                  fontWeight: 700,
                  fontSize: "16px",
                  color: "var(--primary)",
                }}
              >
                <ArrowRightLeft size={20} />
                Orientation du patient
              </div>
              <button
                onClick={closeOrientation}
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

            {/* Patient Info */}
            <div
              style={{
                padding: "16px 24px",
                borderBottom: "1px solid var(--border-light)",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                background: "var(--bg)",
              }}
            >
              <div
                style={{
                  width: "40px",
                  height: "40px",
                  borderRadius: "50%",
                  background: PRIORITY_CONFIG[orientingVisit.priority_level]?.bg || "#dbeafe",
                  color: PRIORITY_CONFIG[orientingVisit.priority_level]?.color || "#1d4ed8",
                  display: "grid",
                  placeItems: "center",
                  fontSize: "16px",
                  fontWeight: 700,
                }}
              >
                {getPatientName(orientingVisit.patient_id)
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .substring(0, 2)
                  .toUpperCase()}
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: "15px", color: "var(--text)" }}>
                  {getPatientName(orientingVisit.patient_id)}
                </div>
                <div style={{ fontSize: "13px", color: "var(--muted)" }}>
                  {orientingVisit.chief_complaint || "Pas de motif renseigné"} · Attente:{" "}
                  {formatWaitTime(getWaitMinutes(orientingVisit.arrived_at))}
                </div>
              </div>
              <span
                style={{
                  marginLeft: "auto",
                  padding: "4px 10px",
                  borderRadius: "9999px",
                  fontSize: "12px",
                  fontWeight: 700,
                  color:
                    PRIORITY_CONFIG[orientingVisit.priority_level]?.color || "#1d4ed8",
                  background:
                    PRIORITY_CONFIG[orientingVisit.priority_level]?.bg || "#dbeafe",
                }}
              >
                {PRIORITY_CONFIG[orientingVisit.priority_level]?.label || "Normale"}
              </span>
            </div>

            {/* Modal Body */}
            <div
              style={{
                padding: "24px",
                display: "flex",
                flexDirection: "column",
                gap: "20px",
              }}
            >
              {/* Destination Selection */}
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "13px",
                    fontWeight: 700,
                    color: "var(--text-secondary)",
                    marginBottom: "10px",
                  }}
                >
                  Destination
                </label>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(2, 1fr)",
                    gap: "10px",
                  }}
                >
                  {Object.entries(DESTINATION_CONFIG).map(([key, cfg]) => (
                    <button
                      key={key}
                      onClick={() => setDestination(key)}
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: "6px",
                        padding: "16px 12px",
                        borderRadius: "var(--radius-md)",
                        border:
                          destination === key
                            ? `2px solid ${cfg.color}`
                            : "1px solid var(--border)",
                        background:
                          destination === key
                            ? `${cfg.color}15`
                            : "var(--card)",
                        cursor: "pointer",
                        fontFamily: "inherit",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <span style={{ color: cfg.color }}>{cfg.icon}</span>
                      <span
                        style={{
                          fontSize: "14px",
                          fontWeight: destination === key ? 700 : 500,
                          color:
                            destination === key ? cfg.color : "var(--text)",
                        }}
                      >
                        {cfg.label}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Conditional Fields based on Destination */}
              {destination === "HOSPITALIZATION" && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px",
                    padding: "16px",
                    background: "#f5f3ff",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid #e9d5ff",
                  }}
                >
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#7c3aed", display: "flex", alignItems: "center", gap: "6px" }}>
                    <BedDouble size={16} />
                    Détails d'hospitalisation
                  </div>
                  {/* Department Selector */}
                  <div>
                    <label
                      style={{
                        display: "block",
                        fontSize: "12px",
                        fontWeight: 600,
                        color: "var(--text-secondary)",
                        marginBottom: "6px",
                      }}
                    >
                      Service d'accueil
                    </label>
                    <select
                      value={selectedDepartment}
                      onChange={(e) => setSelectedDepartment(e.target.value)}
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
                      <option value="">— Sélectionner un service —</option>
                      {lookups.departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name || d.code || d.id}
                        </option>
                      ))}
                    </select>
                  </div>
                  {/* Bed Selector */}
                  <div>
                    <label
                      style={{
                        display: "block",
                        fontSize: "12px",
                        fontWeight: 600,
                        color: "var(--text-secondary)",
                        marginBottom: "6px",
                      }}
                    >
                      Lit
                    </label>
                    <select
                      value={selectedBed}
                      onChange={(e) => setSelectedBed(e.target.value)}
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
                      <option value="">— Sélectionner un lit —</option>
                      {filteredBeds.map((b) => (
                        <option key={b.id} value={b.id}>
                          Lit {b.bed_number || b.id}
                          {b.room_id ? ` — Chambre ${b.room_id}` : ""}
                        </option>
                      ))}
                    </select>
                    {filteredBeds.length === 0 && (
                      <span style={{ fontSize: "12px", color: "var(--muted)", marginTop: "4px", display: "block" }}>
                        Aucun lit disponible
                      </span>
                    )}
                  </div>
                </div>
              )}

              {destination === "TRANSFER" && (
                <div
                  style={{
                    padding: "16px",
                    background: "#fff7ed",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid #fed7aa",
                  }}
                >
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#c2410c", marginBottom: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
                    <Building2 size={16} />
                    Établissement de transfert
                  </div>
                  <select
                    value={selectedFacility}
                    onChange={(e) => setSelectedFacility(e.target.value)}
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
                    <option value="">— Sélectionner un établissement —</option>
                    {lookups.facilities.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.name || f.code || f.id}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Discharge Summary */}
              <div>
                <label
                  style={{
                    display: "flex",
                    fontSize: "13px",
                    fontWeight: 700,
                    color: "var(--text-secondary)",
                    marginBottom: "6px",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <FileText size={14} />
                  Compte rendu de sortie
                </label>
                <textarea
                  value={dischargeSummary}
                  onChange={(e) => setDischargeSummary(e.target.value)}
                  placeholder="Résumé de la prise en charge aux urgences..."
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

              {/* Notes */}
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
                  Notes complémentaires
                </label>
                <textarea
                  value={orientationNotes}
                  onChange={(e) => setOrientationNotes(e.target.value)}
                  placeholder="Notes additionnelles..."
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)",
                    fontSize: "14px",
                    fontFamily: "inherit",
                    background: "white",
                    color: "var(--text)",
                    minHeight: "56px",
                    resize: "vertical",
                  }}
                />
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
                  onClick={closeOrientation}
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
                  onClick={submitOrientation}
                  disabled={submitting}
                  style={{
                    padding: "12px 32px",
                    borderRadius: "var(--radius-md)",
                    border: "none",
                    background: submitting ? "var(--border)" : "var(--primary)",
                    color: "white",
                    fontWeight: 700,
                    fontSize: "14px",
                    cursor: submitting ? "not-allowed" : "pointer",
                    fontFamily: "inherit",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <CheckCircle2 size={16} />
                  {submitting ? "Enregistrement..." : "Confirmer l'orientation"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
