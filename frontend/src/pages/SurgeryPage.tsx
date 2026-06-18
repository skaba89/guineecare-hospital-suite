import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";

type TabKey = "rooms" | "schedules" | "reports";

const TABS: { key: TabKey; label: string }[] = [
  { key: "rooms", label: "Salles" },
  { key: "schedules", label: "Programmation" },
  { key: "reports", label: "Comptes rendus" },
];

const ROOM_STATUS_CONFIG: Record<string, { label: string; cssClass: string; color: string }> = {
  AVAILABLE: { label: "Disponible", cssClass: "available", color: "#047857" },
  OCCUPIED: { label: "Occupée", cssClass: "occupied", color: "#b91c1c" },
  MAINTENANCE: { label: "Maintenance", cssClass: "out_of_service", color: "#6b7280" },
  CLEANING: { label: "Nettoyage", cssClass: "reserved", color: "#92400e" },
};

const SCHEDULE_STATUS_BADGE: Record<string, string> = {
  PLANNED: "badge-yellow",
  IN_PROGRESS: "badge-blue",
  COMPLETED: "badge-green",
  CANCELLED: "badge-gray",
};

const SCHEDULE_STATUS_LABEL: Record<string, string> = {
  PLANNED: "Planifié",
  IN_PROGRESS: "En cours",
  COMPLETED: "Terminé",
  CANCELLED: "Annulé",
};

const REPORT_STATUS_BADGE: Record<string, string> = {
  DRAFT: "badge-gray",
  VALIDATED: "badge-green",
};

const REPORT_STATUS_LABEL: Record<string, string> = {
  DRAFT: "Brouillon",
  VALIDATED: "Validé",
};

const LATERALITY_OPTIONS: { value: string; label: string }[] = [
  { value: "LEFT", label: "Gauche" },
  { value: "RIGHT", label: "Droite" },
  { value: "BILATERAL", label: "Bilatéral" },
  { value: "NOT_APPLICABLE", label: "Non applicable" },
];

const SURGICAL_URGENCY_OPTIONS: { value: string; label: string }[] = [
  { value: "PLANNED", label: "Planifié" },
  { value: "URGENT", label: "Urgent" },
  { value: "EMERGENCY", label: "Urgence" },
];

const ANESTHESIA_OPTIONS: { value: string; label: string }[] = [
  { value: "GENERAL", label: "Générale" },
  { value: "REGIONAL", label: "Régionale" },
  { value: "LOCAL", label: "Locale" },
];

export function SurgeryPage({ lookups }: { lookups: LookupData }) {
  const [activeTab, setActiveTab] = useState<TabKey>("rooms");

  return (
    <section>
      <h1>Bloc Opératoire</h1>
      <p className="muted">Gestion des salles, programmations et comptes rendus chirurgicaux.</p>

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

      {activeTab === "rooms" && <RoomsTab lookups={lookups} />}
      {activeTab === "schedules" && <SchedulesTab lookups={lookups} />}
      {activeTab === "reports" && <ReportsTab lookups={lookups} />}
    </section>
  );
}

/* ─── Rooms Tab ──────────────────────────────────────────── */

function RoomsTab({ lookups }: { lookups: LookupData }) {
  const [rooms, setRooms] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [roomType, setRoomType] = useState("");

  const loadRooms = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/surgery/rooms?page_size=1000");
      setRooms(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les salles.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRooms();
    const handler = () => loadRooms();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadRooms]);

  // Count by status
  const statusCounts = rooms.reduce<Record<string, number>>((acc, room) => {
    acc[room.status] = (acc[room.status] || 0) + 1;
    return acc;
  }, {});

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!code || !name) return;
    setSubmitting(true);
    try {
      await apiRequest("/surgery/rooms", {
        method: "POST",
        body: JSON.stringify({
          code: code.trim(),
          name: name.trim(),
          type: roomType.trim() || undefined,
        }),
      });
      setCode("");
      setName("");
      setRoomType("");
      setShowForm(false);
      loadRooms();
      showToast("Salle créée avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création de la salle.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "32px" }}>
        <div className="spinner" />
        <p className="muted" style={{ marginTop: "12px" }}>Chargement des salles...</p>
      </div>
    );
  }

  if (error) {
    return <p style={{ color: "crimson" }}>{error}</p>;
  }

  return (
    <>
      {/* Status summary */}
      <div className="card" style={{ marginBottom: "18px" }}>
        <div style={{ display: "flex", gap: "24px", flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontWeight: 700, fontSize: "18px" }}>{rooms.length} salle(s)</span>
          {Object.entries(ROOM_STATUS_CONFIG).map(([status, config]) => (
            <span key={status} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "4px",
                  background: config.color,
                  display: "inline-block",
                }}
              />
              <span style={{ fontSize: "14px", color: "var(--muted)" }}>
                {config.label}: <strong style={{ color: "var(--text)" }}>{statusCounts[status] || 0}</strong>
              </span>
            </span>
          ))}
          <button className="primary-button" style={{ marginLeft: "auto" }} onClick={() => setShowForm(!showForm)}>
            {showForm ? "Annuler" : "Nouvelle salle"}
          </button>
        </div>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouvelle salle opératoire</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Code
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Code de la salle"
                required
              />
            </label>
            <label className="form-control">
              Nom
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Nom de la salle"
                required
              />
            </label>
            <label className="form-control">
              Type
              <input
                type="text"
                value={roomType}
                onChange={(e) => setRoomType(e.target.value)}
                placeholder="Type de salle"
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer la salle"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Room grid */}
      <div className="bed-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "16px" }}>
        {rooms.map((room) => {
          const config = ROOM_STATUS_CONFIG[room.status] || ROOM_STATUS_CONFIG.AVAILABLE;
          return (
            <div key={room.id} className={`bed-card ${config.cssClass}`}>
              <div className="bed-number" style={{ fontSize: "16px", fontWeight: 700 }}>{room.code}</div>
              <div className="bed-room">{room.name}</div>
              {room.type && <div className="bed-patient" style={{ fontSize: "12px" }}>{room.type}</div>}
              <div style={{ fontSize: "12px", marginTop: "6px", color: config.color, fontWeight: 600 }}>
                {config.label}
              </div>
            </div>
          );
        })}
      </div>

      {rooms.length === 0 && (
        <div className="card">
          <p className="muted">Aucune salle opératoire configurée.</p>
        </div>
      )}
    </>
  );
}

/* ─── Schedules Tab ──────────────────────────────────────────── */

function SchedulesTab({ lookups }: { lookups: LookupData }) {
  const [schedules, setSchedules] = useState<Row[]>([]);
  const [rooms, setRooms] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [patientId, setPatientId] = useState("");
  const [procedureName, setProcedureName] = useState("");
  const [procedureCode, setProcedureCode] = useState("");
  const [laterality, setLaterality] = useState("NOT_APPLICABLE");
  const [urgency, setUrgency] = useState("PLANNED");
  const [operatingRoomId, setOperatingRoomId] = useState("");
  const [surgeonId, setSurgeonId] = useState("");

  const options = buildOptions(lookups);

  function getPatientName(patientId: string): string {
    const patient = lookups.patients.find((p) => p.id === patientId);
    if (!patient) return "Inconnu";
    return `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.patient_number || "N/A";
  }

  const loadSchedules = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/surgery/schedules?page_size=1000");
      setSchedules(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les programmations.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadRooms = useCallback(async () => {
    try {
      const payload = await apiRequest<any>("/surgery/rooms?page_size=1000");
      setRooms(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      // Silently fail
    }
  }, []);

  useEffect(() => {
    loadSchedules();
    const handler = () => loadSchedules();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadSchedules]);

  useEffect(() => {
    if (showForm) {
      loadRooms();
    }
  }, [showForm, loadRooms]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!patientId || !procedureName) return;
    setSubmitting(true);
    try {
      await apiRequest("/surgery/schedules", {
        method: "POST",
        body: JSON.stringify({
          patient_id: patientId,
          procedure_name: procedureName.trim(),
          procedure_code: procedureCode.trim() || undefined,
          laterality,
          urgency,
          operating_room_id: operatingRoomId || undefined,
          surgeon_id: surgeonId || undefined,
        }),
      });
      setPatientId("");
      setProcedureName("");
      setProcedureCode("");
      setLaterality("NOT_APPLICABLE");
      setUrgency("PLANNED");
      setOperatingRoomId("");
      setSurgeonId("");
      setShowForm(false);
      loadSchedules();
      showToast("Programmation créée avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création de la programmation.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStart(scheduleId: string) {
    try {
      await apiRequest(`/surgery/schedules/${scheduleId}/start`, { method: "POST" });
      loadSchedules();
      showToast("Intervention démarrée.", "success");
    } catch {
      showToast("Erreur lors du démarrage.", "error");
    }
  }

  async function handleComplete(scheduleId: string) {
    try {
      await apiRequest(`/surgery/schedules/${scheduleId}/complete`, { method: "POST" });
      loadSchedules();
      showToast("Intervention terminée.", "success");
    } catch {
      showToast("Erreur lors de la complétion.", "error");
    }
  }

  async function handleCancel(scheduleId: string) {
    if (!confirm("Confirmer l'annulation de cette intervention ?")) return;
    try {
      await apiRequest(`/surgery/schedules/${scheduleId}/cancel`, { method: "POST" });
      loadSchedules();
      showToast("Intervention annulée.", "success");
    } catch {
      showToast("Erreur lors de l'annulation.", "error");
    }
  }

  const roomOptions = rooms.map((r) => ({
    value: r.id,
    label: `${r.code} — ${r.name}`,
  }));

  const URGENCY_LABEL: Record<string, string> = {
    PLANNED: "Planifié",
    URGENT: "Urgent",
    EMERGENCY: "Urgence",
  };

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Programmation chirurgicale</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouvelle programmation"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouvelle programmation</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Patient
              <select value={patientId} onChange={(e) => setPatientId(e.target.value)} required>
                <option value="">-- Choisir un patient --</option>
                {options.patients.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Intervention
              <input
                type="text"
                value={procedureName}
                onChange={(e) => setProcedureName(e.target.value)}
                placeholder="Nom de l'intervention"
                required
              />
            </label>
            <label className="form-control">
              Code intervention
              <input
                type="text"
                value={procedureCode}
                onChange={(e) => setProcedureCode(e.target.value)}
                placeholder="Code (optionnel)"
              />
            </label>
            <label className="form-control">
              Latéralité
              <select value={laterality} onChange={(e) => setLaterality(e.target.value)}>
                {LATERALITY_OPTIONS.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Urgence
              <select value={urgency} onChange={(e) => setUrgency(e.target.value)}>
                {SURGICAL_URGENCY_OPTIONS.map((u) => (
                  <option key={u.value} value={u.value}>{u.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Salle
              <select value={operatingRoomId} onChange={(e) => setOperatingRoomId(e.target.value)}>
                <option value="">-- Choisir une salle --</option>
                {roomOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Chirurgien
              <select value={surgeonId} onChange={(e) => setSurgeonId(e.target.value)}>
                <option value="">-- Choisir un chirurgien --</option>
                {options.staff.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Programmer"}
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
      ) : schedules.length === 0 ? (
        <div className="card">
          <p className="muted">Aucune programmation trouvée.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date prévue</th>
                  <th>Patient</th>
                  <th>Intervention</th>
                  <th>Chirurgien</th>
                  <th>Salle</th>
                  <th>Urgence</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {schedules.map((schedule) => (
                  <tr key={schedule.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {schedule.scheduled_date ? new Date(schedule.scheduled_date).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td style={{ fontWeight: 600 }}>{getPatientName(schedule.patient_id)}</td>
                    <td>{schedule.procedure_name || "—"}</td>
                    <td>{schedule.surgeon_id || "—"}</td>
                    <td>{schedule.operating_room_id || "—"}</td>
                    <td>
                      <span className={`badge ${schedule.urgency === "EMERGENCY" ? "badge-red" : schedule.urgency === "URGENT" ? "badge-yellow" : "badge-gray"}`}>
                        {URGENCY_LABEL[schedule.urgency] || schedule.urgency || "—"}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${SCHEDULE_STATUS_BADGE[schedule.status] || "badge-gray"}`}>
                        {SCHEDULE_STATUS_LABEL[schedule.status] || schedule.status}
                      </span>
                    </td>
                    <td>
                      {schedule.status === "PLANNED" && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px" }}
                          onClick={() => handleStart(schedule.id)}
                        >
                          Démarrer
                        </button>
                      )}
                      {schedule.status === "IN_PROGRESS" && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px" }}
                          onClick={() => handleComplete(schedule.id)}
                        >
                          Terminer
                        </button>
                      )}
                      {(schedule.status === "PLANNED" || schedule.status === "IN_PROGRESS") && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px", marginLeft: "4px", color: "crimson" }}
                          onClick={() => handleCancel(schedule.id)}
                        >
                          Annuler
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

/* ─── Reports Tab ──────────────────────────────────────────── */

function ReportsTab({ lookups }: { lookups: LookupData }) {
  const [reports, setReports] = useState<Row[]>([]);
  const [completedSchedules, setCompletedSchedules] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [scheduleId, setScheduleId] = useState("");
  const [operativeFindings, setOperativeFindings] = useState("");
  const [procedurePerformed, setProcedurePerformed] = useState("");
  const [complications, setComplications] = useState("");
  const [specimens, setSpecimens] = useState("");
  const [bloodLoss, setBloodLoss] = useState("");
  const [anesthesiaType, setAnesthesiaType] = useState("GENERAL");

  function getPatientName(patientId: string): string {
    const patient = lookups.patients.find((p) => p.id === patientId);
    if (!patient) return "Inconnu";
    return `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.patient_number || "N/A";
  }

  const loadReports = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/surgery/reports?page_size=1000");
      setReports(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les comptes rendus.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadCompletedSchedules = useCallback(async () => {
    try {
      const payload = await apiRequest<any>("/surgery/schedules?status=COMPLETED&page_size=1000");
      setCompletedSchedules(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      // Silently fail
    }
  }, []);

  useEffect(() => {
    loadReports();
    const handler = () => loadReports();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadReports]);

  useEffect(() => {
    if (showForm) {
      loadCompletedSchedules();
    }
  }, [showForm, loadCompletedSchedules]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!scheduleId) return;
    setSubmitting(true);
    try {
      await apiRequest("/surgery/reports", {
        method: "POST",
        body: JSON.stringify({
          schedule_id: scheduleId,
          operative_findings: operativeFindings.trim() || undefined,
          procedure_performed: procedurePerformed.trim() || undefined,
          complications: complications.trim() || undefined,
          specimens: specimens.trim() || undefined,
          blood_loss: bloodLoss.trim() || undefined,
          anesthesia_type: anesthesiaType,
        }),
      });
      setScheduleId("");
      setOperativeFindings("");
      setProcedurePerformed("");
      setComplications("");
      setSpecimens("");
      setBloodLoss("");
      setAnesthesiaType("GENERAL");
      setShowForm(false);
      loadReports();
      showToast("Compte rendu créé avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création du compte rendu.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleValidate(reportId: string) {
    try {
      await apiRequest(`/surgery/reports/${reportId}/validate`, { method: "POST" });
      loadReports();
      showToast("Compte rendu validé.", "success");
    } catch {
      showToast("Erreur lors de la validation.", "error");
    }
  }

  const scheduleOptions = completedSchedules.map((s) => ({
    value: s.id,
    label: `${s.procedure_name || "Intervention"} — ${getPatientName(s.patient_id)}`,
  }));

  const ANESTHESIA_LABEL: Record<string, string> = {
    GENERAL: "Générale",
    REGIONAL: "Régionale",
    LOCAL: "Locale",
  };

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Comptes rendus opératoires</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouveau compte rendu"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouveau compte rendu opératoire</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Intervention
              <select value={scheduleId} onChange={(e) => setScheduleId(e.target.value)} required>
                <option value="">-- Choisir une intervention terminée --</option>
                {scheduleOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Type d'anesthésie
              <select value={anesthesiaType} onChange={(e) => setAnesthesiaType(e.target.value)}>
                {ANESTHESIA_OPTIONS.map((a) => (
                  <option key={a.value} value={a.value}>{a.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Perte sanguine (ml)
              <input
                type="text"
                value={bloodLoss}
                onChange={(e) => setBloodLoss(e.target.value)}
                placeholder="Volume en ml"
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Constatations per-opératoires
              <textarea
                value={operativeFindings}
                onChange={(e) => setOperativeFindings(e.target.value)}
                placeholder="Constatations..."
                rows={3}
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Gestes réalisés
              <textarea
                value={procedurePerformed}
                onChange={(e) => setProcedurePerformed(e.target.value)}
                placeholder="Description des gestes..."
                rows={2}
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Complications
              <textarea
                value={complications}
                onChange={(e) => setComplications(e.target.value)}
                placeholder="Complications éventuelles..."
                rows={2}
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Pièces opératoires
              <textarea
                value={specimens}
                onChange={(e) => setSpecimens(e.target.value)}
                placeholder="Pièces envoyées..."
                rows={2}
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer le compte rendu"}
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
          <p className="muted">Aucun compte rendu trouvé.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Patient</th>
                  <th>Intervention</th>
                  <th>Constatations</th>
                  <th>Complications</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {report.created_at ? new Date(report.created_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td style={{ fontWeight: 600 }}>{getPatientName(report.patient_id)}</td>
                    <td>{report.procedure_performed || report.procedure_name || "—"}</td>
                    <td>{report.operative_findings || "—"}</td>
                    <td>{report.complications || "—"}</td>
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
                          onClick={() => handleValidate(report.id)}
                        >
                          Valider
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
