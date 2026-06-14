import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";

type TabKey = "resume" | "observations" | "constantes" | "diagnostics" | "historique" | "examens";

const TABS: { key: TabKey; label: string }[] = [
  { key: "resume", label: "Résumé" },
  { key: "observations", label: "Observations" },
  { key: "constantes", label: "Constantes" },
  { key: "diagnostics", label: "Diagnostics" },
  { key: "historique", label: "Historique" },
  { key: "examens", label: "Examens" },
];

const GENDER_LABELS: Record<string, string> = {
  M: "Masculin",
  F: "Féminin",
  O: "Autre",
};

const NOTE_TYPE_OPTIONS = [
  { value: "OBSERVATION", label: "Observation" },
  { value: "CONSULTATION", label: "Consultation" },
  { value: "PRESCRIPTION", label: "Prescription" },
  { value: "NOTE", label: "Note" },
];

const MEASUREMENT_TYPE_OPTIONS = [
  { value: "TEMPERATURE", label: "Température" },
  { value: "BLOOD_PRESSURE", label: "Tension artérielle" },
  { value: "HEART_RATE", label: "Fréquence cardiaque" },
  { value: "WEIGHT", label: "Poids" },
  { value: "HEIGHT", label: "Taille" },
  { value: "OXYGEN_SAT", label: "Saturation O₂" },
  { value: "PAIN_LEVEL", label: "Douleur" },
  { value: "GLASGOW", label: "Glasgow" },
];

const DIAGNOSIS_TYPE_OPTIONS = [
  { value: "PRINCIPAL", label: "Principal" },
  { value: "SECONDARY", label: "Secondaire" },
  { value: "COMPLICATION", label: "Complication" },
];

const DIAGNOSIS_STATUS_OPTIONS = [
  { value: "ACTIVE", label: "Actif" },
  { value: "RESOLVED", label: "Résolu" },
  { value: "CHRONIC", label: "Chronique" },
];

const MEASUREMENT_UNITS: Record<string, string> = {
  TEMPERATURE: "°C",
  BLOOD_PRESSURE: "mmHg",
  HEART_RATE: "bpm",
  WEIGHT: "kg",
  HEIGHT: "cm",
  OXYGEN_SAT: "%",
  PAIN_LEVEL: "/10",
  GLASGOW: "/15",
};

const ADMISSION_STATUS_LABELS: Record<string, string> = {
  ACTIVE: "En cours",
  CLOSED: "Clôturée",
  CANCELLED: "Annulée",
};

const STAY_STATUS_LABELS: Record<string, string> = {
  ACTIVE: "En cours",
  DISCHARGED: "Sorti",
  TRANSFERRED: "Transféré",
};

const EXAM_TYPE_LABELS: Record<string, string> = {
  RADIOGRAPHY: "Radiographie",
  CT_SCAN: "Scanner",
  MRI: "IRM",
  ULTRASOUND: "Échographie",
  MAMMOGRAPHY: "Mammographie",
  SCINTIGRAPHY: "Scintigraphie",
};

const LAB_STATUS_LABELS: Record<string, string> = {
  PENDING: "En attente",
  IN_PROGRESS: "En cours",
  COMPLETED: "Terminé",
  CANCELLED: "Annulé",
};

export function PatientDetailPage({ lookups }: { lookups: LookupData }) {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<TabKey>("resume");
  const [patient, setPatient] = useState<Row | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPatient = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>(`/patients/${id}`);
      setPatient(payload.data || null);
    } catch {
      setError("Impossible de charger les données du patient.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadPatient();
  }, [loadPatient]);

  if (loading) {
    return (
      <section>
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
          <p className="muted" style={{ marginTop: "12px" }}>Chargement du dossier patient...</p>
        </div>
      </section>
    );
  }

  if (error || !patient) {
    return (
      <section>
        <h1>Dossier patient</h1>
        <p style={{ color: "crimson" }}>{error || "Patient introuvable."}</p>
      </section>
    );
  }

  return (
    <section>
      <h1>
        {patient.first_name} {patient.last_name}
        <span className="muted" style={{ fontSize: "16px", fontWeight: 400, marginLeft: "12px" }}>
          {patient.patient_number}
        </span>
      </h1>
      <p className="muted">Dossier Patient Intégré (DPI)</p>

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

      {activeTab === "resume" && <ResumeTab patient={patient} />}
      {activeTab === "observations" && <ObservationsTab patientId={id!} lookups={lookups} />}
      {activeTab === "constantes" && <ConstantesTab patientId={id!} lookups={lookups} />}
      {activeTab === "diagnostics" && <DiagnosticsTab patientId={id!} lookups={lookups} />}
      {activeTab === "historique" && <HistoriqueTab patientId={id!} />}
      {activeTab === "examens" && <ExamensTab patientId={id!} lookups={lookups} />}
    </section>
  );
}

/* ─── Résumé Tab ─────────────────────────────────────────────── */

function ResumeTab({ patient }: { patient: Row }) {
  return (
    <div className="card">
      <h2>Informations du patient</h2>
      <div className="info-grid" style={{ marginTop: "16px" }}>
        <InfoItem label="Nom complet" value={`${patient.first_name || ""} ${patient.last_name || ""}`} />
        <InfoItem label="Date de naissance" value={patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString("fr-FR") : "—"} />
        <InfoItem label="Sexe" value={GENDER_LABELS[patient.gender] || patient.gender || "—"} />
        <InfoItem label="Téléphone" value={patient.phone || "—"} />
        <InfoItem label="Adresse" value={patient.address || "—"} />
        <InfoItem label="Numéro national" value={patient.national_id || "—"} />
        <InfoItem label="Numéro assurance" value={patient.insurance_number || "—"} />
        <InfoItem label="Contact urgence" value={patient.emergency_contact_name || "—"} />
        <InfoItem label="Tel. urgence" value={patient.emergency_contact_phone || "—"} />
        <InfoItem label="Statut" value={
          <span className={`badge ${patient.status === "ACTIVE" ? "badge-green" : "badge-gray"}`}>
            {patient.status === "ACTIVE" ? "Actif" : patient.status}
          </span>
        } />
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="info-item">
      <span className="label">{label}</span>
      <span className="value">{value}</span>
    </div>
  );
}

/* ─── Observations Tab ───────────────────────────────────────── */

function ObservationsTab({ patientId, lookups }: { patientId: string; lookups: LookupData }) {
  const [notes, setNotes] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [noteType, setNoteType] = useState("OBSERVATION");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const options = buildOptions(lookups);

  async function loadNotes() {
    setLoading(true);
    try {
      const payload = await apiRequest<any>(`/clinical/patients/${patientId}/notes`);
      setNotes(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      showToast("Erreur lors du chargement des observations.", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadNotes();
  }, [patientId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    setSubmitting(true);
    try {
      await apiRequest(`/clinical/patients/${patientId}/notes`, {
        method: "POST",
        body: JSON.stringify({
          facility_id: firstValue(options.facilities),
          note_type: noteType,
          content: content.trim(),
        }),
      });
      setContent("");
      setNoteType("OBSERVATION");
      setShowForm(false);
      loadNotes();
      showToast("Observation enregistrée.", "success");
    } catch {
      showToast("Erreur lors de l'enregistrement.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="section-header">
        <h2>Observations cliniques</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouvelle observation"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouvelle observation</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Type
              <select value={noteType} onChange={(e) => setNoteType(e.target.value)}>
                {NOTE_TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Contenu
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={4}
                style={{
                  width: "100%",
                  border: "1px solid var(--border)",
                  borderRadius: "10px",
                  padding: "12px",
                  font: "inherit",
                  resize: "vertical",
                }}
                placeholder="Saisissez l'observation clinique..."
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Enregistrement..." : "Enregistrer"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : notes.length === 0 ? (
        <div className="card">
          <p className="muted">Aucune observation enregistrée.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Contenu</th>
                </tr>
              </thead>
              <tbody>
                {notes.map((note) => (
                  <tr key={note.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {note.created_at ? new Date(note.created_at).toLocaleString("fr-FR") : "—"}
                    </td>
                    <td>
                      <span className="badge badge-blue">{note.note_type || "—"}</span>
                    </td>
                    <td style={{ maxWidth: "400px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {note.content || "—"}
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

/* ─── Constantes Tab ─────────────────────────────────────────── */

function ConstantesTab({ patientId, lookups }: { patientId: string; lookups: LookupData }) {
  const [measurements, setMeasurements] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [measurementType, setMeasurementType] = useState("TEMPERATURE");
  const [value, setValue] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const options = buildOptions(lookups);

  async function loadMeasurements() {
    setLoading(true);
    try {
      const payload = await apiRequest<any>(`/clinical/patients/${patientId}/measurements`);
      setMeasurements(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      showToast("Erreur lors du chargement des constantes.", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMeasurements();
  }, [patientId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!value.trim()) return;
    setSubmitting(true);
    try {
      await apiRequest(`/clinical/patients/${patientId}/measurements`, {
        method: "POST",
        body: JSON.stringify({
          facility_id: firstValue(options.facilities),
          measurement_type: measurementType,
          value: value.trim(),
          unit: MEASUREMENT_UNITS[measurementType] || "",
        }),
      });
      setValue("");
      setMeasurementType("TEMPERATURE");
      setShowForm(false);
      loadMeasurements();
      showToast("Constante enregistrée.", "success");
    } catch {
      showToast("Erreur lors de l'enregistrement.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  function getMeasurementLabel(type: string) {
    const found = MEASUREMENT_TYPE_OPTIONS.find((o) => o.value === type);
    return found ? found.label : type;
  }

  return (
    <>
      <div className="section-header">
        <h2>Constantes vitales</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouvelle constante"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouvelle constante</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Type de mesure
              <select value={measurementType} onChange={(e) => setMeasurementType(e.target.value)}>
                {MEASUREMENT_TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Valeur {MEASUREMENT_UNITS[measurementType] ? `(${MEASUREMENT_UNITS[measurementType]})` : ""}
              <input
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="Ex: 37.2"
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Enregistrement..." : "Enregistrer"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : measurements.length === 0 ? (
        <div className="card">
          <p className="muted">Aucune constante enregistrée.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Valeur</th>
                  <th>Unité</th>
                </tr>
              </thead>
              <tbody>
                {measurements.map((m) => (
                  <tr key={m.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {m.recorded_at ? new Date(m.recorded_at).toLocaleString("fr-FR") : "—"}
                    </td>
                    <td>{getMeasurementLabel(m.measurement_type)}</td>
                    <td style={{ fontWeight: 700 }}>{m.value || "—"}</td>
                    <td>{m.unit || "—"}</td>
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

/* ─── Diagnostics Tab ────────────────────────────────────────── */

function DiagnosticsTab({ patientId, lookups }: { patientId: string; lookups: LookupData }) {
  const [diagnoses, setDiagnoses] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [diagnosisLabel, setDiagnosisLabel] = useState("");
  const [diagnosisCode, setDiagnosisCode] = useState("");
  const [diagnosisType, setDiagnosisType] = useState("PRINCIPAL");
  const [diagnosisStatus, setDiagnosisStatus] = useState("ACTIVE");
  const [submitting, setSubmitting] = useState(false);

  const options = buildOptions(lookups);

  async function loadDiagnoses() {
    setLoading(true);
    try {
      const payload = await apiRequest<any>(`/clinical/patients/${patientId}/diagnoses`);
      setDiagnoses(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      showToast("Erreur lors du chargement des diagnostics.", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDiagnoses();
  }, [patientId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!diagnosisLabel.trim()) return;
    setSubmitting(true);
    try {
      await apiRequest(`/clinical/patients/${patientId}/diagnoses`, {
        method: "POST",
        body: JSON.stringify({
          facility_id: firstValue(options.facilities),
          diagnosis_code: diagnosisCode.trim() || undefined,
          diagnosis_label: diagnosisLabel.trim(),
          diagnosis_type: diagnosisType,
          status: diagnosisStatus,
        }),
      });
      setDiagnosisLabel("");
      setDiagnosisCode("");
      setDiagnosisType("PRINCIPAL");
      setDiagnosisStatus("ACTIVE");
      setShowForm(false);
      loadDiagnoses();
      showToast("Diagnostic enregistré.", "success");
    } catch {
      showToast("Erreur lors de l'enregistrement.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  function getDiagnosisTypeLabel(type: string) {
    const found = DIAGNOSIS_TYPE_OPTIONS.find((o) => o.value === type);
    return found ? found.label : type;
  }

  function getDiagnosisStatusLabel(status: string) {
    const found = DIAGNOSIS_STATUS_OPTIONS.find((o) => o.value === status);
    return found ? found.label : status;
  }

  const statusBadge: Record<string, string> = {
    ACTIVE: "badge-red",
    RESOLVED: "badge-green",
    CHRONIC: "badge-yellow",
  };

  return (
    <>
      <div className="section-header">
        <h2>Diagnostics</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouveau diagnostic"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouveau diagnostic</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Libellé
              <input
                type="text"
                value={diagnosisLabel}
                onChange={(e) => setDiagnosisLabel(e.target.value)}
                placeholder="Ex: Paludisme simple"
              />
            </label>
            <label className="form-control">
              Code CIM-10
              <input
                type="text"
                value={diagnosisCode}
                onChange={(e) => setDiagnosisCode(e.target.value)}
                placeholder="Ex: B50.0"
              />
            </label>
            <label className="form-control">
              Type
              <select value={diagnosisType} onChange={(e) => setDiagnosisType(e.target.value)}>
                {DIAGNOSIS_TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Statut
              <select value={diagnosisStatus} onChange={(e) => setDiagnosisStatus(e.target.value)}>
                {DIAGNOSIS_STATUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Enregistrement..." : "Enregistrer"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : diagnoses.length === 0 ? (
        <div className="card">
          <p className="muted">Aucun diagnostic enregistré.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Libellé</th>
                  <th>Code CIM-10</th>
                  <th>Type</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {diagnoses.map((d) => (
                  <tr key={d.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {d.created_at ? new Date(d.created_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td style={{ fontWeight: 600 }}>{d.diagnosis_label || "—"}</td>
                    <td><code>{d.diagnosis_code || "—"}</code></td>
                    <td>{getDiagnosisTypeLabel(d.diagnosis_type)}</td>
                    <td>
                      <span className={`badge ${statusBadge[d.status] || "badge-gray"}`}>
                        {getDiagnosisStatusLabel(d.status)}
                      </span>
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

/* ─── Historique Tab ─────────────────────────────────────────── */

function HistoriqueTab({ patientId }: { patientId: string }) {
  const [admissions, setAdmissions] = useState<Row[]>([]);
  const [stays, setStays] = useState<Row[]>([]);
  const [emergencyVisits, setEmergencyVisits] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadHistory() {
      setLoading(true);
      try {
        const [admissionsRes, staysRes, emergencyRes] = await Promise.all([
          apiRequest<any>(`/admissions?patient_id=${patientId}`),
          apiRequest<any>(`/hospitalization/stays?patient_id=${patientId}`),
          apiRequest<any>(`/emergency/queue`),
        ]);
        setAdmissions(Array.isArray(admissionsRes.data) ? admissionsRes.data : []);
        setStays(Array.isArray(staysRes.data) ? staysRes.data : []);
        // Filter emergency visits for this patient
        const allEmergency = Array.isArray(emergencyRes.data) ? emergencyRes.data : [];
        setEmergencyVisits(allEmergency.filter((v: Row) => v.patient_id === patientId));
      } catch {
        // Silently fail
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, [patientId]);

  if (loading) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "32px" }}>
        <div className="spinner" />
        <p className="muted" style={{ marginTop: "12px" }}>Chargement de l'historique...</p>
      </div>
    );
  }

  return (
    <>
      {/* Admissions */}
      <div className="card">
        <h3>Admissions ({admissions.length})</h3>
        {admissions.length === 0 ? (
          <p className="muted">Aucune admission enregistrée.</p>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Motif</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {admissions.map((a) => (
                  <tr key={a.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {a.admitted_at ? new Date(a.admitted_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td>{a.reason || "—"}</td>
                    <td>
                      <span className={`badge ${a.status === "ACTIVE" ? "badge-blue" : "badge-gray"}`}>
                        {ADMISSION_STATUS_LABELS[a.status] || a.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Hospitalisation */}
      <div className="card">
        <h3>Hospitalisations ({stays.length})</h3>
        {stays.length === 0 ? (
          <p className="muted">Aucune hospitalisation enregistrée.</p>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date d'entrée</th>
                  <th>Motif</th>
                  <th>Statut</th>
                  <th>Date de sortie</th>
                </tr>
              </thead>
              <tbody>
                {stays.map((s) => (
                  <tr key={s.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {s.admitted_at ? new Date(s.admitted_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td>{s.reason || "—"}</td>
                    <td>
                      <span className={`badge ${s.status === "ACTIVE" ? "badge-blue" : s.status === "DISCHARGED" ? "badge-green" : "badge-gray"}`}>
                        {STAY_STATUS_LABELS[s.status] || s.status}
                      </span>
                    </td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {s.discharged_at ? new Date(s.discharged_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Urgences */}
      <div className="card">
        <h3>Passages aux urgences ({emergencyVisits.length})</h3>
        {emergencyVisits.length === 0 ? (
          <p className="muted">Aucun passage aux urgences enregistré.</p>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date d'arrivée</th>
                  <th>Motif</th>
                  <th>Priorité</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {emergencyVisits.map((v) => (
                  <tr key={v.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {v.arrived_at ? new Date(v.arrived_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td>{v.chief_complaint || "—"}</td>
                    <td>
                      <span className={`badge ${v.priority_level === "URGENT" || v.priority_level === "EMERGENCY" ? "badge-red" : v.priority_level === "NORMAL" ? "badge-yellow" : "badge-green"}`}>
                        {v.priority_level || "—"}
                      </span>
                    </td>
                    <td>
                      <span className="badge badge-blue">{v.status || "—"}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

/* ─── Examens Tab (Imagerie + Laboratoire) ───────────────────── */

function ExamensTab({ patientId, lookups }: { patientId: string; lookups: LookupData }) {
  const [imagingOrders, setImagingOrders] = useState<Row[]>([]);
  const [labOrders, setLabOrders] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadExams() {
      setLoading(true);
      try {
        const [imagingRes, labRes] = await Promise.all([
          apiRequest<any>(`/imaging/orders?patient_id=${patientId}`),
          apiRequest<any>(`/laboratory/orders`),
        ]);
        setImagingOrders(Array.isArray(imagingRes.data) ? imagingRes.data : []);
        const allLab = Array.isArray(labRes.data) ? labRes.data : [];
        setLabOrders(allLab.filter((o: Row) => o.patient_id === patientId));
      } catch {
        // Silently fail
      } finally {
        setLoading(false);
      }
    }
    loadExams();
  }, [patientId]);

  if (loading) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "32px" }}>
        <div className="spinner" />
        <p className="muted" style={{ marginTop: "12px" }}>Chargement des examens...</p>
      </div>
    );
  }

  const imagingStatusBadge: Record<string, string> = {
    PENDING: "badge-yellow",
    IN_PROGRESS: "badge-blue",
    COMPLETED: "badge-green",
    CANCELLED: "badge-gray",
  };

  return (
    <>
      {/* Imagerie */}
      <div className="card">
        <h3>Examens d'imagerie ({imagingOrders.length})</h3>
        {imagingOrders.length === 0 ? (
          <p className="muted">Aucun examen d'imagerie enregistré.</p>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Région</th>
                  <th>Urgence</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {imagingOrders.map((o) => (
                  <tr key={o.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {o.ordered_at ? new Date(o.ordered_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td>{EXAM_TYPE_LABELS[o.exam_type] || o.exam_type || "—"}</td>
                    <td>{o.body_region || "—"}</td>
                    <td>
                      <span className={`badge ${o.urgency === "EMERGENCY" ? "badge-red" : o.urgency === "URGENT" ? "badge-yellow" : "badge-green"}`}>
                        {o.urgency || "—"}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${imagingStatusBadge[o.status] || "badge-gray"}`}>
                        {LAB_STATUS_LABELS[o.status] || o.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Laboratoire */}
      <div className="card">
        <h3>Examens de laboratoire ({labOrders.length})</h3>
        {labOrders.length === 0 ? (
          <p className="muted">Aucun examen de laboratoire enregistré.</p>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Examen</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {labOrders.map((o) => (
                  <tr key={o.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {o.ordered_at ? new Date(o.ordered_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td style={{ fontWeight: 600 }}>{o.test_id || "—"}</td>
                    <td>
                      <span className={`badge ${imagingStatusBadge[o.status] || "badge-gray"}`}>
                        {LAB_STATUS_LABELS[o.status] || o.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
