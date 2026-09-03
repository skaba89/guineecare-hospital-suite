import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";
import { ICD11Search } from "../components/ICD11Search";
import {
  BodyMap,
  BodyRegionId,
  getRegionLabel,
  parseRegions,
  serializeRegions,
} from "../components/BodyMap";

type TabKey = "resume" | "observations" | "constantes" | "diagnostics" | "historique" | "examens" | "bodymap";

const TABS: { key: TabKey; label: string }[] = [
  { key: "resume", label: "Résumé" },
  { key: "observations", label: "Observations" },
  { key: "constantes", label: "Constantes" },
  { key: "diagnostics", label: "Diagnostics" },
  { key: "bodymap", label: "Carte corporelle" },
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
      {activeTab === "bodymap" && <BodyMapTab patientId={id!} lookups={lookups} />}
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
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Diagnostic (recherche ICD-11)
              <ICD11Search
                value={{ code: diagnosisCode, label: diagnosisLabel }}
                onChange={(code, label) => {
                  setDiagnosisCode(code);
                  setDiagnosisLabel(label);
                }}
                placeholder="Tapez paludisme, hypertension, 1F03…"
                required
              />
              <small style={{ color: "var(--muted)", fontSize: "11px", marginTop: "4px" }}>
                🔍 Recherche dans le catalogue ICD-11 (classification OMS) —
                si le code n'apparaît pas, vous pouvez saisir un libellé libre.
              </small>
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
          apiRequest<any>(`/admissions?patient_id=${patientId}&page_size=1000`),
          apiRequest<any>(`/hospitalization/stays?patient_id=${patientId}&page_size=1000`),
          apiRequest<any>(`/emergency/queue?page_size=1000`),
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
          apiRequest<any>(`/imaging/orders?patient_id=${patientId}&page_size=1000`),
          apiRequest<any>(`/laboratory/orders?page_size=1000`),
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

/* ─── Carte corporelle Tab ────────────────────────────────────── */

const EXAM_TYPE_OPTIONS_BODYMAP = [
  { value: "DOULEUR", label: "Douleur" },
  { value: "LESION", label: "Lésion / Plaie" },
  { value: "EXAMEN", label: "Examen clinique" },
  { value: "INJECTION", label: "Site d'injection / ponction" },
  { value: "AUTRE", label: "Autre" },
];

interface BodyExamRecord {
  id: string;
  created_at: string;
  exam_type: string;
  regions: BodyRegionId[];
  note: string;
  author?: string;
}

/**
 * BodyMapTab — Onglet « Carte corporelle » du dossier patient.
 *
 * Permet au clinicien de :
 *  1. Cliquer sur les régions anatomiques du corps (vue face/dos)
 *  2. Préciser le type d'examen (douleur, lésion, etc.)
 *  3. Ajouter une note descriptive
 *  4. Enregistrer — sauvegardé comme observation clinique (note_type=OBSERVATION)
 *     avec un marqueur `[BODYMAP]` dans le contenu pour pouvoir le récupérer
 *     et l'afficher dans l'historique ci-dessous.
 *
 * Format de stockage (champ content de l'observation) :
 *   [BODYMAP|exam_type=DOULEUR|regions=head,chest,abdomen|note=Texte libre]
 */
function BodyMapTab({ patientId, lookups }: { patientId: string; lookups: LookupData }) {
  const [selected, setSelected] = useState<BodyRegionId[]>([]);
  const [examType, setExamType] = useState("DOULEUR");
  const [note, setNote] = useState("");
  const [history, setHistory] = useState<BodyExamRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [viewingRecord, setViewingRecord] = useState<BodyExamRecord | null>(null);

  const options = buildOptions(lookups);

  async function loadHistory() {
    setLoading(true);
    try {
      const payload = await apiRequest<any>(`/clinical/patients/${patientId}/notes`);
      const allNotes: Row[] = Array.isArray(payload.data) ? payload.data : [];
      // Filtrer les observations qui contiennent le marqueur BODYMAP
      const parsed: BodyExamRecord[] = allNotes
        .map((n): BodyExamRecord | null => {
          const content: string = (n.content as string) || "";
          const match = content.match(/^\[BODYMAP\|exam_type=([^|]*)\|regions=([^|]*)\|note=(.*)\]$/s);
          if (!match) return null;
          return {
            id: n.id as string,
            created_at: n.created_at as string,
            exam_type: match[1] || "AUTRE",
            regions: parseRegions(match[2] || ""),
            note: match[3] || "",
            author: n.author_name as string | undefined,
          };
        })
        .filter((r): r is BodyExamRecord => r !== null)
        .sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""));
      setHistory(parsed);
    } catch {
      showToast("Erreur lors du chargement de l'historique.", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, [patientId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (selected.length === 0) {
      showToast("Veuillez sélectionner au moins une région sur la carte.", "warning");
      return;
    }
    setSubmitting(true);
    try {
      const content = `[BODYMAP|exam_type=${examType}|regions=${serializeRegions(selected)}|note=${note.trim()}]`;
      await apiRequest(`/clinical/patients/${patientId}/notes`, {
        method: "POST",
        body: JSON.stringify({
          facility_id: firstValue(options.facilities),
          note_type: "OBSERVATION",
          content,
        }),
      });
      // Reset
      setSelected([]);
      setNote("");
      setExamType("DOULEUR");
      showToast("Examen corporel enregistré.", "success");
      loadHistory();
    } catch {
      showToast("Erreur lors de l'enregistrement.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  function resetForm() {
    setSelected([]);
    setNote("");
    setExamType("DOULEUR");
  }

  const examTypeLabel = (t: string) =>
    EXAM_TYPE_OPTIONS_BODYMAP.find((o) => o.value === t)?.label || t;

  return (
    <>
      <div className="section-header">
        <h2>Carte corporelle interactive</h2>
        <span className="muted" style={{ fontSize: "13px" }}>
          Cliquez sur les régions du corps pour les sélectionner
        </span>
      </div>

      <div className="card">
        <div className="body-map-exam-grid">
          {/* ─── Colonne gauche : carte interactive + formulaire ─── */}
          <form className="body-map-exam-form" onSubmit={handleSubmit}>
            <BodyMap
              selected={selected}
              onChange={setSelected}
              height={420}
            />
            <label>
              Type d'examen
              <select
                value={examType}
                onChange={(e) => setExamType(e.target.value)}
              >
                {EXAM_TYPE_OPTIONS_BODYMAP.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label>
              Note clinique (optionnel)
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={3}
                placeholder="Ex : douleur aiguë, palpation, aspect de la lésion, irradiation..."
              />
            </label>
            <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
              <button
                type="submit"
                className="primary-button"
                disabled={submitting || selected.length === 0}
              >
                {submitting ? "Enregistrement..." : "Enregistrer l'examen"}
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={resetForm}
                disabled={submitting}
              >
                Réinitialiser
              </button>
            </div>
          </form>

          {/* ─── Colonne droite : historique des examens corporels ─── */}
          <div>
            <h3 style={{ marginTop: 0, marginBottom: 12, fontSize: 15 }}>
              Historique des examens corporels ({history.length})
            </h3>
            {loading ? (
              <div className="body-map-empty-state">Chargement...</div>
            ) : history.length === 0 ? (
              <div className="body-map-empty-state">
                Aucun examen corporel enregistré pour ce patient.
                <br />
                Utilisez la carte ci-contre pour enregistrer le premier.
              </div>
            ) : (
              <div className="body-map-exam-history">
                {history.map((rec) => (
                  <div
                    key={rec.id}
                    className="body-map-exam-history-item"
                    onClick={() => setViewingRecord(viewingRecord?.id === rec.id ? null : rec)}
                    style={{ cursor: "pointer" }}
                  >
                    <div className="meta">
                      <span>
                        {rec.created_at
                          ? new Date(rec.created_at).toLocaleString("fr-FR", {
                              day: "2-digit", month: "2-digit", year: "numeric",
                              hour: "2-digit", minute: "2-digit",
                            })
                          : "—"}
                      </span>
                      <span className="badge badge-blue">{examTypeLabel(rec.exam_type)}</span>
                    </div>
                    <div className="regions">
                      {rec.regions.map((r) => (
                        <span key={r} className="mini-chip">{getRegionLabel(r)}</span>
                      ))}
                    </div>
                    {rec.note && <div className="note">« {rec.note} »</div>}
                    {rec.author && (
                      <div style={{ marginTop: 4, fontSize: 11, color: "var(--muted)" }}>
                        Par : {rec.author}
                      </div>
                    )}
                    {viewingRecord?.id === rec.id && (
                      <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px dashed var(--border)" }}>
                        <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>
                          Aperçu de la sélection :
                        </div>
                        <BodyMap
                          selected={rec.regions}
                          readOnly
                          height={280}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
