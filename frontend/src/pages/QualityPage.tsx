import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";

type TabKey = "indicators" | "measurements" | "incidents";

const TABS: { key: TabKey; label: string }[] = [
  { key: "indicators", label: "Indicateurs" },
  { key: "measurements", label: "Mesures" },
  { key: "incidents", label: "Événements indésirables" },
];

const CATEGORY_OPTIONS: { value: string; label: string }[] = [
  { value: "SAFETY", label: "Sécurité" },
  { value: "EFFICIENCY", label: "Efficacité" },
  { value: "PATIENT_EXPERIENCE", label: "Expérience patient" },
  { value: "CLINICAL_OUTCOME", label: "Résultat clinique" },
];

const FREQUENCY_OPTIONS: { value: string; label: string }[] = [
  { value: "DAILY", label: "Quotidien" },
  { value: "WEEKLY", label: "Hebdomadaire" },
  { value: "MONTHLY", label: "Mensuel" },
  { value: "QUARTERLY", label: "Trimestriel" },
  { value: "YEARLY", label: "Annuel" },
];

const INCIDENT_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: "FALL", label: "Chute" },
  { value: "MEDICATION_ERROR", label: "Erreur médicamenteuse" },
  { value: "NOSOCOMIAL_INFECTION", label: "Infection nosocomiale" },
  { value: "EQUIPMENT_FAILURE", label: "Défaillance équipement" },
  { value: "OTHER", label: "Autre" },
];

const INCIDENT_TYPE_LABEL: Record<string, string> = {
  FALL: "Chute",
  MEDICATION_ERROR: "Erreur médicamenteuse",
  NOSOCOMIAL_INFECTION: "Infection nosocomiale",
  EQUIPMENT_FAILURE: "Défaillance équipement",
  OTHER: "Autre",
};

const SEVERITY_OPTIONS: { value: string; label: string }[] = [
  { value: "NEAR_MISS", label: "Presque incident" },
  { value: "MINOR", label: "Mineur" },
  { value: "MODERATE", label: "Modéré" },
  { value: "MAJOR", label: "Majeur" },
  { value: "CRITICAL", label: "Critique" },
];

const SEVERITY_BADGE: Record<string, string> = {
  NEAR_MISS: "badge-green",
  MINOR: "badge-yellow",
  MODERATE: "badge-yellow",
  MAJOR: "badge-red",
  CRITICAL: "badge-red",
};

const SEVERITY_LABEL: Record<string, string> = {
  NEAR_MISS: "Presque incident",
  MINOR: "Mineur",
  MODERATE: "Modéré",
  MAJOR: "Majeur",
  CRITICAL: "Critique",
};

const INCIDENT_STATUS_BADGE: Record<string, string> = {
  REPORTED: "badge-yellow",
  UNDER_INVESTIGATION: "badge-blue",
  RESOLVED: "badge-green",
};

const INCIDENT_STATUS_LABEL: Record<string, string> = {
  REPORTED: "Signalé",
  UNDER_INVESTIGATION: "En investigation",
  RESOLVED: "Résolu",
};

const CATEGORY_LABEL: Record<string, string> = {
  SAFETY: "Sécurité",
  EFFICIENCY: "Efficacité",
  PATIENT_EXPERIENCE: "Expérience patient",
  CLINICAL_OUTCOME: "Résultat clinique",
};

const FREQUENCY_LABEL: Record<string, string> = {
  DAILY: "Quotidien",
  WEEKLY: "Hebdomadaire",
  MONTHLY: "Mensuel",
  QUARTERLY: "Trimestriel",
  YEARLY: "Annuel",
};

export function QualityPage({ lookups }: { lookups: LookupData }) {
  const [activeTab, setActiveTab] = useState<TabKey>("indicators");

  return (
    <section>
      <h1>Qualité / Pilotage</h1>
      <p className="muted">Gestion des indicateurs qualité, mesures et événements indésirables.</p>

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

      {activeTab === "indicators" && <IndicatorsTab lookups={lookups} />}
      {activeTab === "measurements" && <MeasurementsTab lookups={lookups} />}
      {activeTab === "incidents" && <IncidentsTab lookups={lookups} />}
    </section>
  );
}

/* ─── Indicators Tab ──────────────────────────────────────────── */

function IndicatorsTab({ lookups }: { lookups: LookupData }) {
  const [indicators, setIndicators] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("SAFETY");
  const [description, setDescription] = useState("");
  const [unit, setUnit] = useState("");
  const [targetValue, setTargetValue] = useState("");
  const [frequency, setFrequency] = useState("MONTHLY");

  const loadIndicators = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/quality/indicators");
      setIndicators(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les indicateurs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadIndicators();
    const handler = () => loadIndicators();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadIndicators]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!code || !name) return;
    setSubmitting(true);
    try {
      await apiRequest("/quality/indicators", {
        method: "POST",
        body: JSON.stringify({
          code: code.trim(),
          name: name.trim(),
          category,
          description: description.trim() || undefined,
          unit: unit.trim() || undefined,
          target_value: targetValue.trim() || undefined,
          frequency,
        }),
      });
      setCode("");
      setName("");
      setCategory("SAFETY");
      setDescription("");
      setUnit("");
      setTargetValue("");
      setFrequency("MONTHLY");
      setShowForm(false);
      loadIndicators();
      showToast("Indicateur créé avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création de l'indicateur.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Indicateurs qualité</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouvel indicateur"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouvel indicateur qualité</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Code
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Code de l'indicateur"
                required
              />
            </label>
            <label className="form-control">
              Nom
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Nom de l'indicateur"
                required
              />
            </label>
            <label className="form-control">
              Catégorie
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORY_OPTIONS.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Unité
              <input
                type="text"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                placeholder="Unité de mesure"
              />
            </label>
            <label className="form-control">
              Valeur cible
              <input
                type="text"
                value={targetValue}
                onChange={(e) => setTargetValue(e.target.value)}
                placeholder="Objectif"
              />
            </label>
            <label className="form-control">
              Fréquence
              <select value={frequency} onChange={(e) => setFrequency(e.target.value)}>
                {FREQUENCY_OPTIONS.map((f) => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Description
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Description de l'indicateur..."
                rows={2}
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer l'indicateur"}
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
      ) : indicators.length === 0 ? (
        <div className="card">
          <p className="muted">Aucun indicateur trouvé.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Nom</th>
                  <th>Catégorie</th>
                  <th>Unité</th>
                  <th>Cible</th>
                  <th>Fréquence</th>
                </tr>
              </thead>
              <tbody>
                {indicators.map((ind) => (
                  <tr key={ind.id}>
                    <td style={{ fontWeight: 600 }}>{ind.code || "—"}</td>
                    <td>{ind.name || "—"}</td>
                    <td>
                      <span className="badge badge-blue">
                        {CATEGORY_LABEL[ind.category] || ind.category || "—"}
                      </span>
                    </td>
                    <td>{ind.unit || "—"}</td>
                    <td>{ind.target_value ?? "—"}</td>
                    <td>{FREQUENCY_LABEL[ind.frequency] || ind.frequency || "—"}</td>
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

/* ─── Measurements Tab ──────────────────────────────────────────── */

function MeasurementsTab({ lookups }: { lookups: LookupData }) {
  const [measurements, setMeasurements] = useState<Row[]>([]);
  const [indicators, setIndicators] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [indicatorId, setIndicatorId] = useState("");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [value, setValue] = useState("");
  const [numerator, setNumerator] = useState("");
  const [denominator, setDenominator] = useState("");
  const [notes, setNotes] = useState("");

  const loadMeasurements = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/quality/measurements");
      setMeasurements(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les mesures.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadIndicators = useCallback(async () => {
    try {
      const payload = await apiRequest<any>("/quality/indicators");
      setIndicators(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      // Silently fail
    }
  }, []);

  useEffect(() => {
    loadMeasurements();
    const handler = () => loadMeasurements();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadMeasurements]);

  useEffect(() => {
    if (showForm) {
      loadIndicators();
    }
  }, [showForm, loadIndicators]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!indicatorId || !periodStart) return;
    setSubmitting(true);
    try {
      await apiRequest("/quality/measurements", {
        method: "POST",
        body: JSON.stringify({
          indicator_id: indicatorId,
          period_start: periodStart,
          period_end: periodEnd || undefined,
          value: value.trim() || undefined,
          numerator: numerator.trim() || undefined,
          denominator: denominator.trim() || undefined,
          notes: notes.trim() || undefined,
        }),
      });
      setIndicatorId("");
      setPeriodStart("");
      setPeriodEnd("");
      setValue("");
      setNumerator("");
      setDenominator("");
      setNotes("");
      setShowForm(false);
      loadMeasurements();
      showToast("Mesure créée avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création de la mesure.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const indicatorOptions = indicators.map((ind) => ({
    value: ind.id,
    label: `${ind.code || "IND"} - ${ind.name || ind.id}`,
  }));

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Mesures</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Nouvelle mesure"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouvelle mesure</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Indicateur
              <select value={indicatorId} onChange={(e) => setIndicatorId(e.target.value)} required>
                <option value="">-- Choisir un indicateur --</option>
                {indicatorOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Début de période
              <input
                type="date"
                value={periodStart}
                onChange={(e) => setPeriodStart(e.target.value)}
                required
              />
            </label>
            <label className="form-control">
              Fin de période
              <input
                type="date"
                value={periodEnd}
                onChange={(e) => setPeriodEnd(e.target.value)}
              />
            </label>
            <label className="form-control">
              Valeur
              <input
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="Valeur mesurée"
              />
            </label>
            <label className="form-control">
              Numérateur
              <input
                type="text"
                value={numerator}
                onChange={(e) => setNumerator(e.target.value)}
                placeholder="Numérateur"
              />
            </label>
            <label className="form-control">
              Dénominateur
              <input
                type="text"
                value={denominator}
                onChange={(e) => setDenominator(e.target.value)}
                placeholder="Dénominateur"
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Notes
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Notes complémentaires..."
                rows={2}
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer la mesure"}
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
      ) : measurements.length === 0 ? (
        <div className="card">
          <p className="muted">Aucune mesure trouvée.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Indicateur</th>
                  <th>Période</th>
                  <th>Valeur</th>
                  <th>Numérateur</th>
                  <th>Dénominateur</th>
                </tr>
              </thead>
              <tbody>
                {measurements.map((m) => (
                  <tr key={m.id}>
                    <td style={{ fontWeight: 600 }}>{m.indicator_id || "—"}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {m.period_start ? new Date(m.period_start).toLocaleDateString("fr-FR") : "—"}
                      {m.period_end ? ` — ${new Date(m.period_end).toLocaleDateString("fr-FR")}` : ""}
                    </td>
                    <td>{m.value ?? "—"}</td>
                    <td>{m.numerator ?? "—"}</td>
                    <td>{m.denominator ?? "—"}</td>
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

/* ─── Incidents Tab ──────────────────────────────────────────── */

function IncidentsTab({ lookups }: { lookups: LookupData }) {
  const [incidents, setIncidents] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [incidentDate, setIncidentDate] = useState("");
  const [incidentType, setIncidentType] = useState("OTHER");
  const [severity, setSeverity] = useState("MINOR");
  const [description, setDescription] = useState("");
  const [immediateActions, setImmediateActions] = useState("");

  const loadIncidents = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/quality/incidents");
      setIncidents(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les événements indésirables.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadIncidents();
    const handler = () => loadIncidents();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadIncidents]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!description) return;
    setSubmitting(true);
    try {
      await apiRequest("/quality/incidents", {
        method: "POST",
        body: JSON.stringify({
          incident_date: incidentDate || undefined,
          incident_type: incidentType,
          severity,
          description: description.trim(),
          immediate_actions: immediateActions.trim() || undefined,
        }),
      });
      setIncidentDate("");
      setIncidentType("OTHER");
      setSeverity("MINOR");
      setDescription("");
      setImmediateActions("");
      setShowForm(false);
      loadIncidents();
      showToast("Événement indésirable signalé avec succès.", "success");
    } catch {
      showToast("Erreur lors du signalement.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleInvestigate(incidentId: string) {
    try {
      await apiRequest(`/quality/incidents/${incidentId}/investigate`, { method: "POST" });
      loadIncidents();
      showToast("Investigation ouverte.", "success");
    } catch {
      showToast("Erreur lors de l'ouverture de l'investigation.", "error");
    }
  }

  async function handleResolve(incidentId: string) {
    try {
      await apiRequest(`/quality/incidents/${incidentId}/resolve`, { method: "POST" });
      loadIncidents();
      showToast("Événement résolu.", "success");
    } catch {
      showToast("Erreur lors de la résolution.", "error");
    }
  }

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Événements indésirables</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Signaler un événement"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Signaler un événement indésirable</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Date de l'événement
              <input
                type="date"
                value={incidentDate}
                onChange={(e) => setIncidentDate(e.target.value)}
              />
            </label>
            <label className="form-control">
              Type
              <select value={incidentType} onChange={(e) => setIncidentType(e.target.value)}>
                {INCIDENT_TYPE_OPTIONS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Sévérité
              <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
                {SEVERITY_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Description
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Description de l'événement..."
                rows={3}
                required
              />
            </label>
            <label className="form-control" style={{ gridColumn: "1 / -1" }}>
              Actions immédiates
              <textarea
                value={immediateActions}
                onChange={(e) => setImmediateActions(e.target.value)}
                placeholder="Actions immédiates prises..."
                rows={2}
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Envoi..." : "Signaler"}
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
      ) : incidents.length === 0 ? (
        <div className="card">
          <p className="muted">Aucun événement indésirable trouvé.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Sévérité</th>
                  <th>Description</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((inc) => (
                  <tr key={inc.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {inc.incident_date ? new Date(inc.incident_date).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td>{INCIDENT_TYPE_LABEL[inc.incident_type] || inc.incident_type || "—"}</td>
                    <td>
                      <span className={`badge ${SEVERITY_BADGE[inc.severity] || "badge-gray"}`} style={inc.severity === "CRITICAL" ? { fontWeight: 700 } : undefined}>
                        {SEVERITY_LABEL[inc.severity] || inc.severity || "—"}
                      </span>
                    </td>
                    <td>{inc.description || "—"}</td>
                    <td>
                      <span className={`badge ${INCIDENT_STATUS_BADGE[inc.status] || "badge-gray"}`}>
                        {INCIDENT_STATUS_LABEL[inc.status] || inc.status}
                      </span>
                    </td>
                    <td>
                      {inc.status === "REPORTED" && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px" }}
                          onClick={() => handleInvestigate(inc.id)}
                        >
                          Investiguer
                        </button>
                      )}
                      {inc.status === "UNDER_INVESTIGATION" && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px" }}
                          onClick={() => handleResolve(inc.id)}
                        >
                          Résoudre
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
