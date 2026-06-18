import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";

type TabKey = "records" | "new_record" | "consultations" | "deliveries";

const TABS: { key: TabKey; label: string }[] = [
  { key: "records", label: "Dossiers maternité" },
  { key: "new_record", label: "Nouveau dossier" },
  { key: "consultations", label: "Consultations" },
  { key: "deliveries", label: "Accouchements" },
];

const PREGNANCY_STATUS_OPTIONS = [
  { value: "ONGOING", label: "En cours" },
  { value: "COMPLETED", label: "Terminée" },
  { value: "COMPLICATED", label: "Compliquée" },
  { value: "MISCARRIAGE", label: "Fausse couche" },
];

const DELIVERY_TYPE_OPTIONS = [
  { value: "VAGINAL", label: "Vaginal" },
  { value: "CESAREAN", label: "Césarienne" },
  { value: "INSTRUMENTAL", label: "Instrumental" },
];

const BABY_STATUS_OPTIONS = [
  { value: "ALIVE", label: "Vivant" },
  { value: "STILLBORN", label: "Mort-né" },
];

export function MaternityPage({ lookups }: { lookups: LookupData }) {
  const [activeTab, setActiveTab] = useState<TabKey>("records");
  const [selectedRecord, setSelectedRecord] = useState<string>("");

  return (
    <section>
      <h1>Maternité</h1>
      <p className="muted">Suivi des grossesses, consultations prénatales et accouchements.</p>

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

      {activeTab === "records" && (
        <RecordsTab
          lookups={lookups}
          onSelectRecord={(id) => {
            setSelectedRecord(id);
            setActiveTab("consultations");
          }}
        />
      )}
      {activeTab === "new_record" && (
        <NewRecordTab lookups={lookups} onCreated={() => setActiveTab("records")} />
      )}
      {activeTab === "consultations" && (
        <ConsultationsTab lookups={lookups} selectedRecord={selectedRecord} />
      )}
      {activeTab === "deliveries" && (
        <DeliveriesTab lookups={lookups} selectedRecord={selectedRecord} />
      )}
    </section>
  );
}

/* ─── Records Tab ────────────────────────────────────────────── */

function RecordsTab({
  lookups,
  onSelectRecord,
}: {
  lookups: LookupData;
  onSelectRecord: (id: string) => void;
}) {
  const [records, setRecords] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadRecords() {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/maternity/records?page_size=1000");
      setRecords(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les dossiers maternité.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRecords();
    const handler = () => loadRecords();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, []);

  const statusBadge: Record<string, string> = {
    ONGOING: "badge-blue",
    COMPLETED: "badge-green",
    COMPLICATED: "badge-yellow",
    MISCARRIAGE: "badge-red",
  };

  const statusLabel: Record<string, string> = {
    ONGOING: "En cours",
    COMPLETED: "Terminée",
    COMPLICATED: "Compliquée",
    MISCARRIAGE: "Fausse couche",
  };

  return (
    <>
      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
          <p className="muted" style={{ marginTop: "12px" }}>Chargement...</p>
        </div>
      ) : error ? (
        <p style={{ color: "crimson" }}>{error}</p>
      ) : records.length === 0 ? (
        <div className="card">
          <p className="muted">Aucun dossier maternité enregistré.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Date prévue</th>
                  <th>Statut</th>
                  <th>Nombre de consultations</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map((rec) => (
                  <tr key={rec.id}>
                    <td style={{ fontWeight: 600 }}>{rec.patient_id || "—"}</td>
                    <td>
                      {rec.expected_due_date
                        ? new Date(rec.expected_due_date).toLocaleDateString("fr-FR")
                        : "—"}
                    </td>
                    <td>
                      <span className={`badge ${statusBadge[rec.status] || "badge-gray"}`}>
                        {statusLabel[rec.status] || rec.status}
                      </span>
                    </td>
                    <td>{rec.consultation_count ?? "—"}</td>
                    <td>
                      <button
                        className="secondary-button"
                        style={{ padding: "4px 12px", fontSize: "13px" }}
                        onClick={() => onSelectRecord(rec.id)}
                      >
                        Voir
                      </button>
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

/* ─── New Record Tab ─────────────────────────────────────────── */

function NewRecordTab({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const options = buildOptions(lookups);
  const [patientId, setPatientId] = useState("");
  const [expectedDueDate, setExpectedDueDate] = useState("");
  const [gravida, setGravida] = useState("");
  const [para, setPara] = useState("");
  const [bloodType, setBloodType] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!patientId) return;
    setSubmitting(true);
    try {
      await apiRequest("/maternity/records", {
        method: "POST",
        body: JSON.stringify({
          facility_id: firstValue(options.facilities),
          patient_id: patientId,
          expected_due_date: expectedDueDate || undefined,
          gravida: gravida || undefined,
          para: para || undefined,
          blood_type: bloodType || undefined,
        }),
      });
      showToast("Dossier maternité créé avec succès.", "success");
      onCreated();
    } catch {
      showToast("Erreur lors de la création du dossier.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card form-card">
      <h2>Nouveau dossier maternité</h2>
      <form onSubmit={handleSubmit} className="form-grid">
        <label className="form-control">
          Patient
          <select value={patientId} onChange={(e) => setPatientId(e.target.value)} required>
            <option value="">-- Choisir une patiente --</option>
            {options.patients.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </label>
        <label className="form-control">
          Date prévue d'accouchement
          <input
            type="date"
            value={expectedDueDate}
            onChange={(e) => setExpectedDueDate(e.target.value)}
          />
        </label>
        <label className="form-control">
          Geste (Gravida)
          <input
            type="number"
            min="0"
            value={gravida}
            onChange={(e) => setGravida(e.target.value)}
            placeholder="Nombre de grossesses"
          />
        </label>
        <label className="form-control">
          Parité (Para)
          <input
            type="number"
            min="0"
            value={para}
            onChange={(e) => setPara(e.target.value)}
            placeholder="Nombre d'accouchements"
          />
        </label>
        <label className="form-control">
          Groupe sanguin
          <select value={bloodType} onChange={(e) => setBloodType(e.target.value)}>
            <option value="">-- Choisir --</option>
            {["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((bt) => (
              <option key={bt} value={bt}>{bt}</option>
            ))}
          </select>
        </label>
        <div className="form-actions">
          <button className="primary-button" type="submit" disabled={submitting}>
            {submitting ? "Création..." : "Créer le dossier"}
          </button>
        </div>
      </form>
    </div>
  );
}

/* ─── Consultations Tab ──────────────────────────────────────── */

function ConsultationsTab({
  lookups,
  selectedRecord,
}: {
  lookups: LookupData;
  selectedRecord: string;
}) {
  const [records, setRecords] = useState<Row[]>([]);
  const [consultations, setConsultations] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentRecord, setCurrentRecord] = useState(selectedRecord);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Consultation form fields
  const [consultDate, setConsultDate] = useState("");
  const [gestationalAge, setGestationalAge] = useState("");
  const [weight, setWeight] = useState("");
  const [bloodPressure, setBloodPressure] = useState("");
  const [notes, setNotes] = useState("");

  const options = buildOptions(lookups);

  async function loadRecords() {
    try {
      const payload = await apiRequest<any>("/maternity/records?page_size=1000");
      setRecords(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      // Silently fail
    }
  }

  async function loadConsultations(recordId: string) {
    setLoading(true);
    try {
      const payload = await apiRequest<any>(`/maternity/records/${recordId}`);
      setConsultations(Array.isArray(payload.data?.consultations) ? payload.data.consultations : []);
    } catch {
      setConsultations([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRecords();
  }, []);

  useEffect(() => {
    if (currentRecord) {
      loadConsultations(currentRecord);
    } else {
      setConsultations([]);
      setLoading(false);
    }
  }, [currentRecord]);

  // Sync with external selection
  useEffect(() => {
    if (selectedRecord) {
      setCurrentRecord(selectedRecord);
    }
  }, [selectedRecord]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!currentRecord) return;
    setSubmitting(true);
    try {
      await apiRequest(`/maternity/records/${currentRecord}/consultations`, {
        method: "POST",
        body: JSON.stringify({
          facility_id: firstValue(options.facilities),
          consultation_date: consultDate || undefined,
          gestational_age_weeks: gestationalAge ? parseInt(gestationalAge) : undefined,
          weight: weight || undefined,
          blood_pressure: bloodPressure || undefined,
          notes: notes.trim() || undefined,
        }),
      });
      setConsultDate("");
      setGestationalAge("");
      setWeight("");
      setBloodPressure("");
      setNotes("");
      setShowForm(false);
      loadConsultations(currentRecord);
      showToast("Consultation enregistrée.", "success");
    } catch {
      showToast("Erreur lors de l'enregistrement.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const recordOptions = records.map((r) => ({
    value: r.id,
    label: `${r.patient_id || r.id} — ${r.status || ""}`,
  }));

  return (
    <>
      <div className="section-header">
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>Consultations prénatales</h2>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <select
              value={currentRecord}
              onChange={(e) => setCurrentRecord(e.target.value)}
              style={{ minWidth: "200px" }}
            >
              <option value="">-- Sélectionner un dossier --</option>
              {recordOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
        </div>
        {currentRecord && (
          <button className="primary-button" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Annuler" : "Nouvelle consultation"}
          </button>
        )}
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouvelle consultation prénatale</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Date de consultation
              <input type="date" value={consultDate} onChange={(e) => setConsultDate(e.target.value)} />
            </label>
            <label className="form-control">
              Âge gestationnel (semaines)
              <input type="number" min="0" max="45" value={gestationalAge} onChange={(e) => setGestationalAge(e.target.value)} />
            </label>
            <label className="form-control">
              Poids (kg)
              <input type="text" value={weight} onChange={(e) => setWeight(e.target.value)} placeholder="Ex: 68" />
            </label>
            <label className="form-control">
              Tension artérielle
              <input type="text" value={bloodPressure} onChange={(e) => setBloodPressure(e.target.value)} placeholder="Ex: 120/80" />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Notes
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                style={{
                  width: "100%",
                  border: "1px solid var(--border)",
                  borderRadius: "10px",
                  padding: "12px",
                  font: "inherit",
                  resize: "vertical",
                }}
                placeholder="Observations..."
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

      {!currentRecord ? (
        <div className="card">
          <p className="muted">Sélectionnez un dossier maternité pour voir les consultations.</p>
        </div>
      ) : loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : consultations.length === 0 ? (
        <div className="card">
          <p className="muted">Aucune consultation pour ce dossier.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Âge gestationnel</th>
                  <th>Poids</th>
                  <th>Tension</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {consultations.map((c) => (
                  <tr key={c.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {c.consultation_date
                        ? new Date(c.consultation_date).toLocaleDateString("fr-FR")
                        : "—"}
                    </td>
                    <td>{c.gestational_age_weeks ? `${c.gestational_age_weeks} SA` : "—"}</td>
                    <td>{c.weight ? `${c.weight} kg` : "—"}</td>
                    <td>{c.blood_pressure || "—"}</td>
                    <td style={{ maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.notes || "—"}
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

/* ─── Deliveries Tab ─────────────────────────────────────────── */

function DeliveriesTab({
  lookups,
  selectedRecord,
}: {
  lookups: LookupData;
  selectedRecord: string;
}) {
  const [records, setRecords] = useState<Row[]>([]);
  const [deliveries, setDeliveries] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentRecord, setCurrentRecord] = useState(selectedRecord);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Delivery form fields
  const [deliveryDate, setDeliveryDate] = useState("");
  const [deliveryType, setDeliveryType] = useState("VAGINAL");
  const [babyGender, setBabyGender] = useState("M");
  const [babyWeight, setBabyWeight] = useState("");
  const [babyStatus, setBabyStatus] = useState("ALIVE");
  const [complications, setComplications] = useState("");

  const options = buildOptions(lookups);

  async function loadRecords() {
    try {
      const payload = await apiRequest<any>("/maternity/records?page_size=1000");
      setRecords(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      // Silently fail
    }
  }

  async function loadDeliveries(recordId: string) {
    setLoading(true);
    try {
      const payload = await apiRequest<any>(`/maternity/records/${recordId}`);
      setDeliveries(Array.isArray(payload.data?.deliveries) ? payload.data.deliveries : []);
    } catch {
      setDeliveries([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRecords();
  }, []);

  useEffect(() => {
    if (currentRecord) {
      loadDeliveries(currentRecord);
    } else {
      setDeliveries([]);
      setLoading(false);
    }
  }, [currentRecord]);

  useEffect(() => {
    if (selectedRecord) {
      setCurrentRecord(selectedRecord);
    }
  }, [selectedRecord]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!currentRecord) return;
    setSubmitting(true);
    try {
      await apiRequest(`/maternity/records/${currentRecord}/deliveries`, {
        method: "POST",
        body: JSON.stringify({
          facility_id: firstValue(options.facilities),
          delivery_date: deliveryDate || undefined,
          delivery_type: deliveryType,
          baby_gender: babyGender,
          baby_weight: babyWeight || undefined,
          baby_status: babyStatus,
          complications: complications.trim() || undefined,
        }),
      });
      setDeliveryDate("");
      setDeliveryType("VAGINAL");
      setBabyGender("M");
      setBabyWeight("");
      setBabyStatus("ALIVE");
      setComplications("");
      setShowForm(false);
      loadDeliveries(currentRecord);
      showToast("Accouchement enregistré.", "success");
    } catch {
      showToast("Erreur lors de l'enregistrement.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const recordOptions = records.map((r) => ({
    value: r.id,
    label: `${r.patient_id || r.id} — ${r.status || ""}`,
  }));

  const deliveryTypeLabel: Record<string, string> = {
    VAGINAL: "Vaginal",
    CESAREAN: "Césarienne",
    INSTRUMENTAL: "Instrumental",
  };

  const babyStatusLabel: Record<string, string> = {
    ALIVE: "Vivant",
    STILLBORN: "Mort-né",
  };

  return (
    <>
      <div className="section-header">
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>Accouchements</h2>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <select
              value={currentRecord}
              onChange={(e) => setCurrentRecord(e.target.value)}
              style={{ minWidth: "200px" }}
            >
              <option value="">-- Sélectionner un dossier --</option>
              {recordOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
        </div>
        {currentRecord && (
          <button className="primary-button" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Annuler" : "Nouvel accouchement"}
          </button>
        )}
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Enregistrer un accouchement</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Date d'accouchement
              <input type="datetime-local" value={deliveryDate} onChange={(e) => setDeliveryDate(e.target.value)} />
            </label>
            <label className="form-control">
              Type d'accouchement
              <select value={deliveryType} onChange={(e) => setDeliveryType(e.target.value)}>
                {DELIVERY_TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Sexe du bébé
              <select value={babyGender} onChange={(e) => setBabyGender(e.target.value)}>
                <option value="M">Masculin</option>
                <option value="F">Féminin</option>
              </select>
            </label>
            <label className="form-control">
              Poids du bébé (g)
              <input type="number" min="0" value={babyWeight} onChange={(e) => setBabyWeight(e.target.value)} placeholder="Ex: 3200" />
            </label>
            <label className="form-control">
              État du bébé
              <select value={babyStatus} onChange={(e) => setBabyStatus(e.target.value)}>
                {BABY_STATUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Complications
              <textarea
                value={complications}
                onChange={(e) => setComplications(e.target.value)}
                rows={2}
                style={{
                  width: "100%",
                  border: "1px solid var(--border)",
                  borderRadius: "10px",
                  padding: "12px",
                  font: "inherit",
                  resize: "vertical",
                }}
                placeholder="Décrivez les complications éventuelles..."
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

      {!currentRecord ? (
        <div className="card">
          <p className="muted">Sélectionnez un dossier maternité pour voir les accouchements.</p>
        </div>
      ) : loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : deliveries.length === 0 ? (
        <div className="card">
          <p className="muted">Aucun accouchement pour ce dossier.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Sexe bébé</th>
                  <th>Poids</th>
                  <th>État bébé</th>
                  <th>Complications</th>
                </tr>
              </thead>
              <tbody>
                {deliveries.map((d) => (
                  <tr key={d.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {d.delivery_date
                        ? new Date(d.delivery_date).toLocaleString("fr-FR")
                        : "—"}
                    </td>
                    <td>
                      <span className="badge badge-blue">
                        {deliveryTypeLabel[d.delivery_type] || d.delivery_type}
                      </span>
                    </td>
                    <td>{d.baby_gender === "M" ? "Masculin" : d.baby_gender === "F" ? "Féminin" : d.baby_gender || "—"}</td>
                    <td>{d.baby_weight ? `${d.baby_weight} g` : "—"}</td>
                    <td>
                      <span className={`badge ${d.baby_status === "ALIVE" ? "badge-green" : "badge-red"}`}>
                        {babyStatusLabel[d.baby_status] || d.baby_status}
                      </span>
                    </td>
                    <td style={{ maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {d.complications || "—"}
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
