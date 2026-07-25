import { useCallback, useEffect, useMemo, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";

// ── Types ───────────────────────────────────────────────────────────────────

type Shift = {
  id: string;
  code: string;
  name: string;
  shift_type: string; // DAY | NIGHT | FULL_DAY | ON_CALL
  color: string | null;
  start_time: string | null;
  end_time: string | null;
  recurrence: string;
  enabled: boolean;
  required_staff_count: number;
  required_profession: string | null;
};

type Assignment = {
  id: string;
  shift_id: string;
  staff_id: string;
  assignment_date: string;
  start_time: string | null;
  end_time: string | null;
  status: string;
  notes: string | null;
};

type PlanningResponse = {
  facility_id: string | null;
  department_id: string | null;
  start_date: string;
  end_date: string;
  days: string[];
  rows: {
    staff_id: string;
    staff_name: string;
    employee_number: string | null;
    profession: string | null;
    cells: { staff_id: string; date: string; assignments: Assignment[] }[];
  }[];
  summary: { total_assignments: number; by_status: Record<string, number> };
};

type TabKey = "planning" | "shifts" | "assignments" | "on-call" | "swaps";

const TABS: { key: TabKey; label: string }[] = [
  { key: "planning", label: "Planning hebdo" },
  { key: "shifts", label: "Templates de shifts" },
  { key: "assignments", label: "Affectations" },
  { key: "on-call", label: "Astreintes" },
  { key: "swaps", label: "Remplacements" },
];

const SHIFT_TYPE_LABEL: Record<string, string> = {
  DAY: "Jour",
  NIGHT: "Nuit",
  FULL_DAY: "24h",
  ON_CALL: "Astreinte",
};

const SHIFT_TYPE_COLOR: Record<string, string> = {
  DAY: "#f59e0b",
  NIGHT: "#1e40af",
  FULL_DAY: "#7c3aed",
  ON_CALL: "#10b981",
};

const STATUS_LABEL: Record<string, string> = {
  SCHEDULED: "Planifié",
  CONFIRMED: "Confirmé",
  COMPLETED: "Effectué",
  ABSENT: "Absent",
  CANCELLED: "Annulé",
};

const STATUS_BADGE: Record<string, string> = {
  SCHEDULED: "badge-yellow",
  CONFIRMED: "badge-blue",
  COMPLETED: "badge-green",
  ABSENT: "badge-red",
  CANCELLED: "badge-gray",
};

// ── Main ────────────────────────────────────────────────────────────────────

export function PersonnelPlanningPage({ lookups }: { lookups: LookupData }) {
  const [activeTab, setActiveTab] = useState<TabKey>("planning");

  return (
    <section>
      <h1>Personnel — Planning & Gardes</h1>
      <p className="muted">
        Module RH v2 : plannings hebdo/mensuels, gardes, astreintes, congés,
        remplacements. v1.5.0
      </p>

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

      {activeTab === "planning" && <PlanningTab lookups={lookups} />}
      {activeTab === "shifts" && <ShiftsTab lookups={lookups} />}
      {activeTab === "assignments" && <AssignmentsTab lookups={lookups} />}
      {activeTab === "on-call" && <OnCallTab lookups={lookups} />}
      {activeTab === "swaps" && <SwapsTab lookups={lookups} />}
    </section>
  );
}

// ── Planning Tab ────────────────────────────────────────────────────────────

function PlanningTab({ lookups }: { lookups: LookupData }) {
  const today = new Date();
  const monday = new Date(today);
  monday.setDate(today.getDate() - ((today.getDay() + 6) % 7));

  const [startDate, setStartDate] = useState(monday.toISOString().split("T")[0]);
  const [endDate, setEndDate] = useState(() => {
    const d = new Date(monday);
    d.setDate(d.getDate() + 6);
    return d.toISOString().split("T")[0];
  });
  const [departmentId, setDepartmentId] = useState("");
  const [planning, setPlanning] = useState<PlanningResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      let path = `/personnel/planning?start_date=${startDate}&end_date=${endDate}`;
      if (departmentId) path += `&department_id=${departmentId}`;
      const payload = await apiRequest<PlanningResponse>(path);
      setPlanning(payload);
    } catch (e: any) {
      setError(e.message || "Erreur");
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, departmentId]);

  useEffect(() => {
    load();
  }, [load]);

  const staffById = useMemo(() => {
    const m: Record<string, Row> = {};
    (lookups.staff || []).forEach((s: Row) => { m[s.id] = s; });
    return m;
  }, [lookups.staff]);

  function shiftWeeks(offset: number) {
    const start = new Date(startDate);
    start.setDate(start.getDate() + offset * 7);
    const end = new Date(start);
    end.setDate(end.getDate() + 6);
    setStartDate(start.toISOString().split("T")[0]);
    setEndDate(end.toISOString().split("T")[0]);
  }

  if (loading) return <div className="muted">Chargement…</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Planning hebdomadaire</h2>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button className="action-button" onClick={() => shiftWeeks(-1)} title="Semaine précédente">←</button>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          <span>→</span>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          <button className="action-button" onClick={() => shiftWeeks(1)} title="Semaine suivante">→</button>
          <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
            <option value="">Tous services</option>
            {(lookups.departments || []).map((d: Row) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
      </div>

      {planning && (
        <>
          <div className="stats-grid">
            <div className="card stat-card">
              <div className="stat-label">Staff planifiés</div>
              <div className="stat-value">{planning.rows.length}</div>
            </div>
            <div className="card stat-card">
              <div className="stat-label">Affectations période</div>
              <div className="stat-value">{planning.summary.total_assignments}</div>
            </div>
            <div className="card stat-card">
              <div className="stat-label">Confirmées</div>
              <div className="stat-value stat-success">
                {planning.summary.by_status?.CONFIRMED || 0}
              </div>
            </div>
          </div>

          <div className="card" style={{ overflowX: "auto" }}>
            <table className="data-table" style={{ minWidth: 800 }}>
              <thead>
                <tr>
                  <th style={{ position: "sticky", left: 0, background: "#fff" }}>Staff</th>
                  {planning.days.map((d) => {
                    const date = new Date(d);
                    const isWeekend = date.getDay() === 0 || date.getDay() === 6;
                    return (
                      <th
                        key={d}
                        style={{
                          minWidth: 120,
                          background: isWeekend ? "#fef3c7" : undefined,
                        }}
                      >
                        {date.toLocaleDateString("fr-FR", { weekday: "short", day: "2-digit" })}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {planning.rows.length === 0 ? (
                  <tr>
                    <td colSpan={planning.days.length + 1} className="muted" style={{ textAlign: "center" }}>
                      Aucun staff actif sur cette période.
                    </td>
                  </tr>
                ) : (
                  planning.rows.map((row) => (
                    <tr key={row.staff_id}>
                      <td style={{ position: "sticky", left: 0, background: "#fff" }}>
                        <strong>{row.staff_name}</strong>
                        <div className="muted" style={{ fontSize: 11 }}>
                          {row.employee_number} · {row.profession || "—"}
                        </div>
                      </td>
                      {row.cells.map((cell) => (
                        <td key={cell.date} style={{ verticalAlign: "top", padding: 4 }}>
                          {cell.assignments.length === 0 ? (
                            <span className="muted">—</span>
                          ) : (
                            cell.assignments.map((a) => (
                              <AssignmentBadge key={a.id} assignment={a} shifts={lookups.shifts || []} />
                            ))
                          )}
                        </td>
                      ))}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}

function AssignmentBadge({ assignment, shifts }: { assignment: Assignment; shifts: Row[] }) {
  const shift = shifts.find((s) => s.id === assignment.shift_id);
  const color = shift?.color || SHIFT_TYPE_COLOR[shift?.shift_type || ""] || "#64748b";
  return (
    <div
      style={{
        background: color,
        color: "white",
        padding: "2px 6px",
        borderRadius: 4,
        fontSize: 10,
        marginBottom: 2,
        display: "inline-block",
        maxWidth: 110,
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
      }}
      title={`${shift?.name || "Shift"} — ${STATUS_LABEL[assignment.status] || assignment.status}`}
    >
      {(shift?.name || "Shift").slice(0, 15)}
    </div>
  );
}

// ── Shifts Tab ──────────────────────────────────────────────────────────────

function ShiftsTab({ lookups }: { lookups: LookupData }) {
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [shiftType, setShiftType] = useState("DAY");
  const [startTime, setStartTime] = useState("08:00");
  const [endTime, setEndTime] = useState("17:00");
  const [recurrence, setRecurrence] = useState("DAILY");
  const [requiredProfession, setRequiredProfession] = useState("");
  const [departmentId, setDepartmentId] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const payload = await apiRequest<{ data: Shift[]; total: number }>("/personnel/shifts");
      setShifts(payload.data || []);
    } catch {
      setShifts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!code || !name) return;
    setSubmitting(true);
    try {
      await apiRequest("/personnel/shifts", {
        method: "POST",
        body: JSON.stringify({
          code,
          name,
          shift_type: shiftType,
          start_time: startTime || undefined,
          end_time: endTime || undefined,
          recurrence,
          required_profession: requiredProfession || undefined,
          department_id: departmentId || undefined,
        }),
      });
      setShowForm(false);
      setCode(""); setName(""); setRequiredProfession(""); setDepartmentId("");
      load();
      showToast("Shift créé avec succès.", "success");
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleGenerate(shift: Shift) {
    const startDate = prompt("Date de début (YYYY-MM-DD) :", new Date().toISOString().split("T")[0]);
    if (!startDate) return;
    const endDate = prompt("Date de fin (YYYY-MM-DD) :", startDate);
    if (!endDate) return;
    const staffId = prompt("Staff ID (laisser vide pour auto) :", "");
    try {
      const result = await apiRequest<{ generated: number; skipped: number }>(
        `/personnel/shifts/${shift.id}/generate`,
        {
          method: "POST",
          body: JSON.stringify({
            start_date: startDate,
            end_date: endDate,
            staff_id: staffId || null,
          }),
        }
      );
      showToast(`${result.generated} affectation(s) générée(s), ${result.skipped} ignorée(s).`, "success");
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    }
  }

  if (loading) return <div className="muted">Chargement…</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Templates de shifts ({shifts.length})</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "+ Nouveau shift"}
        </button>
      </div>

      {showForm && (
        <form className="card form-card" onSubmit={handleSubmit}>
          <h3>Nouveau template de shift</h3>
          <div className="form-grid">
            <label>
              Code *
              <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="GARDE_MED_NUIT" required />
            </label>
            <label>
              Nom *
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Garde médecine nuit" required />
            </label>
            <label>
              Type
              <select value={shiftType} onChange={(e) => setShiftType(e.target.value)}>
                <option value="DAY">Jour</option>
                <option value="NIGHT">Nuit</option>
                <option value="FULL_DAY">24h</option>
                <option value="ON_CALL">Astreinte</option>
              </select>
            </label>
            <label>
              Début
              <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
            </label>
            <label>
              Fin
              <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
            </label>
            <label>
              Récurrence
              <select value={recurrence} onChange={(e) => setRecurrence(e.target.value)}>
                <option value="DAILY">Tous les jours</option>
                <option value="WEEKDAYS">Lundi-vendredi</option>
                <option value="WEEKEND">Weekend</option>
              </select>
            </label>
            <label>
              Profession requise
              <input value={requiredProfession} onChange={(e) => setRequiredProfession(e.target.value)} placeholder="MEDECIN" />
            </label>
            <label>
              Département
              <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
                <option value="">— Tous —</option>
                {(lookups.departments || []).map((d: Row) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="form-actions">
            <button type="submit" className="primary-button" disabled={submitting}>
              {submitting ? "Création…" : "Créer"}
            </button>
            <button type="button" className="secondary-button" onClick={() => setShowForm(false)}>
              Annuler
            </button>
          </div>
        </form>
      )}

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Nom</th>
              <th>Type</th>
              <th>Horaires</th>
              <th>Récurrence</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {shifts.length === 0 ? (
              <tr><td colSpan={7} className="muted" style={{ textAlign: "center" }}>Aucun shift.</td></tr>
            ) : (
              shifts.map((s) => (
                <tr key={s.id}>
                  <td><code>{s.code}</code></td>
                  <td>{s.name}</td>
                  <td>
                    <span
                      className="badge"
                      style={{ background: s.color || SHIFT_TYPE_COLOR[s.shift_type], color: "white", fontSize: 10 }}
                    >
                      {SHIFT_TYPE_LABEL[s.shift_type] || s.shift_type}
                    </span>
                  </td>
                  <td>{s.start_time?.slice(0, 5)} → {s.end_time?.slice(0, 5)}</td>
                  <td>{s.recurrence}</td>
                  <td>
                    <span className={`badge ${s.enabled ? "badge-green" : "badge-gray"}`}>
                      {s.enabled ? "Actif" : "Inactif"}
                    </span>
                  </td>
                  <td>
                    <button
                      className="action-button"
                      onClick={() => handleGenerate(s)}
                      title="Générer des affectations"
                    >
                      📅
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ── Assignments Tab ─────────────────────────────────────────────────────────

function AssignmentsTab({ lookups }: { lookups: LookupData }) {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const path = statusFilter
        ? `/personnel/assignments?status=${statusFilter}&page_size=100`
        : `/personnel/assignments?page_size=100`;
      const payload = await apiRequest<{ data: Assignment[]; total: number }>(path);
      setAssignments(payload.data || []);
    } catch {
      setAssignments([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const staffById = useMemo(() => {
    const m: Record<string, Row> = {};
    (lookups.staff || []).forEach((s: Row) => { m[s.id] = s; });
    return m;
  }, [lookups.staff]);

  if (loading) return <div className="muted">Chargement…</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Affectations ({assignments.length})</h2>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Toutes</option>
          <option value="SCHEDULED">Planifiées</option>
          <option value="CONFIRMED">Confirmées</option>
          <option value="COMPLETED">Effectuées</option>
          <option value="ABSENT">Absences</option>
        </select>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Staff</th>
              <th>Shift</th>
              <th>Horaires</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            {assignments.length === 0 ? (
              <tr><td colSpan={5} className="muted" style={{ textAlign: "center" }}>Aucune affectation.</td></tr>
            ) : (
              assignments.map((a) => {
                const staff = staffById[a.staff_id];
                const shift = (lookups.shifts || []).find((s: Row) => s.id === a.shift_id);
                return (
                  <tr key={a.id}>
                    <td>{new Date(a.assignment_date).toLocaleDateString("fr-FR")}</td>
                    <td>
                      {staff ? `${staff.first_name} ${staff.last_name}` : a.staff_id}
                      <div className="muted" style={{ fontSize: 11 }}>{staff?.employee_number}</div>
                    </td>
                    <td>{shift?.name || a.shift_id}</td>
                    <td>{a.start_time?.slice(0, 5) || "—"} → {a.end_time?.slice(0, 5) || "—"}</td>
                    <td>
                      <span className={`badge ${STATUS_BADGE[a.status] || "badge-gray"}`}>
                        {STATUS_LABEL[a.status] || a.status}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ── On-Call Duties Tab ──────────────────────────────────────────────────────

function OnCallTab({ lookups }: { lookups: LookupData }) {
  const [duties, setDuties] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form
  const [staffId, setStaffId] = useState("");
  const [startAt, setStartAt] = useState("");
  const [endAt, setEndAt] = useState("");
  const [dutyType, setDutyType] = useState("TELEPHONIC");
  const [reason, setReason] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const payload = await apiRequest<{ data: any[]; total: number }>(
        "/personnel/on-call-duties"
      );
      setDuties(payload.data || []);
    } catch {
      setDuties([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!staffId || !startAt || !endAt) return;
    setSubmitting(true);
    try {
      await apiRequest("/personnel/on-call-duties", {
        method: "POST",
        body: JSON.stringify({
          staff_id: staffId,
          start_at: new Date(startAt).toISOString(),
          end_at: new Date(endAt).toISOString(),
          duty_type: dutyType,
          reason: reason || undefined,
        }),
      });
      setShowForm(false);
      setStaffId(""); setStartAt(""); setEndAt(""); setReason("");
      load();
      showToast("Astreinte créée.", "success");
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const DUTY_TYPE_LABEL: Record<string, string> = {
    TELEPHONIC: "Téléphonique",
    PHYSICAL: "Physique",
    MIXED: "Mixte",
  };

  if (loading) return <div className="muted">Chargement…</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Astreintes ({duties.length})</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "+ Nouvelle astreinte"}
        </button>
      </div>

      {showForm && (
        <form className="card form-card" onSubmit={handleSubmit}>
          <h3>Planifier une astreinte</h3>
          <div className="form-grid">
            <label>
              Staff *
              <select value={staffId} onChange={(e) => setStaffId(e.target.value)} required>
                <option value="">— Sélectionner —</option>
                {(lookups.staff || []).map((s: Row) => (
                  <option key={s.id} value={s.id}>
                    {s.first_name} {s.last_name} ({s.employee_number})
                  </option>
                ))}
              </select>
            </label>
            <label>
              Type
              <select value={dutyType} onChange={(e) => setDutyType(e.target.value)}>
                <option value="TELEPHONIC">Téléphonique</option>
                <option value="PHYSICAL">Physique</option>
                <option value="MIXED">Mixte</option>
              </select>
            </label>
            <label>
              Début *
              <input type="datetime-local" value={startAt} onChange={(e) => setStartAt(e.target.value)} required />
            </label>
            <label>
              Fin *
              <input type="datetime-local" value={endAt} onChange={(e) => setEndAt(e.target.value)} required />
            </label>
          </div>
          <label>
            Raison
            <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Astreinte week-end cardiologie" />
          </label>
          <div className="form-actions">
            <button type="submit" className="primary-button" disabled={submitting}>
              {submitting ? "Création…" : "Planifier"}
            </button>
            <button type="button" className="secondary-button" onClick={() => setShowForm(false)}>
              Annuler
            </button>
          </div>
        </form>
      )}

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Période</th>
              <th>Staff</th>
              <th>Type</th>
              <th>Raison</th>
              <th>Compensation</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            {duties.length === 0 ? (
              <tr><td colSpan={6} className="muted" style={{ textAlign: "center" }}>Aucune astreinte.</td></tr>
            ) : (
              duties.map((d) => {
                const staff = (lookups.staff || []).find((s: Row) => s.id === d.staff_id);
                return (
                  <tr key={d.id}>
                    <td>
                      {new Date(d.start_at).toLocaleString("fr-FR")}
                      <br />
                      <span className="muted">→ {new Date(d.end_at).toLocaleString("fr-FR")}</span>
                    </td>
                    <td>{staff ? `${staff.first_name} ${staff.last_name}` : d.staff_id}</td>
                    <td>{DUTY_TYPE_LABEL[d.duty_type] || d.duty_type}</td>
                    <td>{d.reason || "—"}</td>
                    <td>{d.compensation_days}j</td>
                    <td>
                      <span className={`badge ${d.status === "SCHEDULED" ? "badge-yellow" : d.status === "COMPLETED" ? "badge-green" : "badge-gray"}`}>
                        {d.status}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ── Swaps Tab ───────────────────────────────────────────────────────────────

function SwapsTab({ lookups }: { lookups: LookupData }) {
  const [swaps, setSwaps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const path = statusFilter
        ? `/personnel/swaps?status=${statusFilter}`
        : `/personnel/swaps`;
      const payload = await apiRequest<{ data: any[]; total: number }>(path);
      setSwaps(payload.data || []);
    } catch {
      setSwaps([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAction(swapId: string, action: "accept" | "approve" | "reject" | "cancel") {
    const note = action === "approve" || action === "reject"
      ? prompt("Note du manager :", "") || ""
      : undefined;
    try {
      await apiRequest(`/personnel/swaps/${swapId}/${action}`, {
        method: "POST",
        body: JSON.stringify(action === "approve" || action === "reject" ? { manager_note: note } : {}),
      });
      showToast(`Action "${action}" effectuée.`, "success");
      load();
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    }
  }

  const SWAP_STATUS_BADGE: Record<string, string> = {
    REQUESTED: "badge-yellow",
    ACCEPTED: "badge-blue",
    APPROVED: "badge-green",
    REJECTED: "badge-red",
    CANCELLED: "badge-gray",
    COMPLETED: "badge-gray",
  };

  if (loading) return <div className="muted">Chargement…</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Demandes de remplacement ({swaps.length})</h2>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Toutes</option>
          <option value="REQUESTED">En attente acceptation</option>
          <option value="ACCEPTED">En attente validation</option>
          <option value="APPROVED">Approuvées</option>
          <option value="REJECTED">Refusées</option>
        </select>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date demande</th>
              <th>Staff initial</th>
              <th>Remplaçant</th>
              <th>Raison</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {swaps.length === 0 ? (
              <tr><td colSpan={6} className="muted" style={{ textAlign: "center" }}>Aucune demande.</td></tr>
            ) : (
              swaps.map((s) => {
                const requester = (lookups.staff || []).find((st: Row) => st.id === s.requester_id);
                const replacement = (lookups.staff || []).find((st: Row) => st.id === s.replacement_id);
                return (
                  <tr key={s.id}>
                    <td>{new Date(s.created_at).toLocaleString("fr-FR")}</td>
                    <td>{requester ? `${requester.first_name} ${requester.last_name}` : s.requester_id}</td>
                    <td>{replacement ? `${replacement.first_name} ${replacement.last_name}` : s.replacement_id}</td>
                    <td>{s.reason || "—"}</td>
                    <td>
                      <span className={`badge ${SWAP_STATUS_BADGE[s.status] || "badge-gray"}`}>
                        {s.status}
                      </span>
                    </td>
                    <td>
                      {s.status === "REQUESTED" && (
                        <>
                          <button className="action-button" onClick={() => handleAction(s.id, "accept")} title="Accepter">✅</button>
                          <button className="action-button" onClick={() => handleAction(s.id, "cancel")} title="Annuler">❌</button>
                        </>
                      )}
                      {s.status === "ACCEPTED" && (
                        <>
                          <button className="action-button" onClick={() => handleAction(s.id, "approve")} title="Approuver">👍</button>
                          <button className="action-button" onClick={() => handleAction(s.id, "reject")} title="Refuser">👎</button>
                        </>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
