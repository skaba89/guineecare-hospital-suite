import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";

type TabKey = "beds" | "stays";

const TABS: { key: TabKey; label: string }[] = [
  { key: "beds", label: "Tableau des lits" },
  { key: "stays", label: "Séjours" },
];

const BED_STATUS_CONFIG: Record<string, { label: string; cssClass: string; color: string }> = {
  AVAILABLE: { label: "Disponible", cssClass: "available", color: "#047857" },
  OCCUPIED: { label: "Occupé", cssClass: "occupied", color: "#b91c1c" },
  RESERVED: { label: "Réservé", cssClass: "reserved", color: "#92400e" },
  OUT_OF_SERVICE: { label: "Hors service", cssClass: "out_of_service", color: "#6b7280" },
};

export function HospitalizationPage({ lookups }: { lookups: LookupData }) {
  const [activeTab, setActiveTab] = useState<TabKey>("beds");

  return (
    <section>
      <h1>Hospitalisation</h1>
      <p className="muted">Gestion des lits et des séjours hospitaliers.</p>

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

      {activeTab === "beds" && <BedBoardTab lookups={lookups} />}
      {activeTab === "stays" && <StaysTab lookups={lookups} />}
    </section>
  );
}

/* ─── Bed Board Tab ──────────────────────────────────────────── */

function BedBoardTab({ lookups }: { lookups: LookupData }) {
  const [beds, setBeds] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  const loadBeds = useCallback(async () => {
    if (!facilityId) return;
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>(`/hospitalization/bed-board?facility_id=${facilityId}`);
      setBeds(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger le tableau des lits.");
    } finally {
      setLoading(false);
    }
  }, [facilityId]);

  useEffect(() => {
    loadBeds();
    const handler = () => loadBeds();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadBeds]);

  // Group beds by room
  const rooms = beds.reduce<Record<string, Row[]>>((acc, bed) => {
    const key = bed.room_code || "SALLE ?";
    if (!acc[key]) acc[key] = [];
    acc[key].push(bed);
    return acc;
  }, {});

  // Count by status
  const statusCounts = beds.reduce<Record<string, number>>((acc, bed) => {
    acc[bed.bed_status] = (acc[bed.bed_status] || 0) + 1;
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "32px" }}>
        <div className="spinner" />
        <p className="muted" style={{ marginTop: "12px" }}>Chargement du tableau des lits...</p>
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
          <span style={{ fontWeight: 700, fontSize: "18px" }}>{beds.length} lit(s)</span>
          {Object.entries(BED_STATUS_CONFIG).map(([status, config]) => (
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
        </div>
      </div>

      {/* Bed grid by room */}
      {Object.entries(rooms).map(([roomCode, roomBeds]) => (
        <div className="card" key={roomCode}>
          <h3 style={{ marginBottom: "12px" }}>
            {roomCode} — {roomBeds[0]?.room_name || roomCode}
            <span className="muted" style={{ fontWeight: 400, fontSize: "14px", marginLeft: "8px" }}>
              ({roomBeds.length} lit{roomBeds.length > 1 ? "s" : ""})
            </span>
          </h3>
          <div className="bed-grid">
            {roomBeds.map((bed) => {
              const config = BED_STATUS_CONFIG[bed.bed_status] || BED_STATUS_CONFIG.AVAILABLE;
              return (
                <div key={bed.bed_id} className={`bed-card ${config.cssClass}`}>
                  <div className="bed-number">Lit {bed.bed_number}</div>
                  <div className="bed-room">{config.label}</div>
                  {bed.patient_name && (
                    <div className="bed-patient">{bed.patient_name}</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {beds.length === 0 && (
        <div className="card">
          <p className="muted">Aucun lit configuré pour cet établissement.</p>
        </div>
      )}
    </>
  );
}

/* ─── Stays Tab ──────────────────────────────────────────────── */

function StaysTab({ lookups }: { lookups: LookupData }) {
  const [stays, setStays] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [showAdmitForm, setShowAdmitForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Admit form state
  const [patientId, setPatientId] = useState("");
  const [bedId, setBedId] = useState("");
  const [reason, setReason] = useState("");

  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  // Build bed options from available beds
  const [availableBeds, setAvailableBeds] = useState<Row[]>([]);

  const loadStays = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      const qs = params.toString();
      const payload = await apiRequest<any>(`/hospitalization/stays${qs ? `?${qs}&page_size=1000` : "?page_size=1000"}`);
      setStays(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les séjours.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  const loadAvailableBeds = useCallback(async () => {
    if (!facilityId) return;
    try {
      const payload = await apiRequest<any>(`/hospitalization/beds?bed_status=AVAILABLE&page_size=1000`);
      setAvailableBeds(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      // Silently fail
    }
  }, [facilityId]);

  useEffect(() => {
    loadStays();
    const handler = () => loadStays();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadStays]);

  useEffect(() => {
    if (showAdmitForm) {
      loadAvailableBeds();
    }
  }, [showAdmitForm, loadAvailableBeds]);

  async function handleAdmit(e: React.FormEvent) {
    e.preventDefault();
    if (!patientId) return;
    setSubmitting(true);
    try {
      await apiRequest("/hospitalization/stays", {
        method: "POST",
        body: JSON.stringify({
          facility_id: facilityId,
          patient_id: patientId,
          bed_id: bedId || undefined,
          reason: reason.trim() || undefined,
        }),
      });
      setPatientId("");
      setBedId("");
      setReason("");
      setShowAdmitForm(false);
      loadStays();
      showToast("Patient admis avec succès.", "success");
    } catch {
      showToast("Erreur lors de l'admission.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDischarge(stayId: string) {
    if (!confirm("Confirmer la sortie de ce patient ?")) return;
    try {
      await apiRequest(`/hospitalization/stays/${stayId}/discharge`, { method: "POST" });
      loadStays();
      showToast("Patient sorti avec succès.", "success");
    } catch {
      showToast("Erreur lors de la sortie.", "error");
    }
  }

  const stayStatusBadge: Record<string, string> = {
    ACTIVE: "badge-blue",
    DISCHARGED: "badge-green",
    TRANSFERRED: "badge-yellow",
  };

  const stayStatusLabel: Record<string, string> = {
    ACTIVE: "En cours",
    DISCHARGED: "Sorti",
    TRANSFERRED: "Transféré",
  };

  const bedOptions = availableBeds.map((b) => ({
    value: b.id,
    label: `Lit ${b.bed_number}`,
  }));

  function getPatientName(patientId: string): string {
    const patient = lookups.patients.find((p) => p.id === patientId);
    if (!patient) return "Inconnu";
    return `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.patient_number || "N/A";
  }

  return (
    <>
      <div className="section-header">
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>Séjours hospitaliers</h2>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ minWidth: "160px" }}
            >
              <option value="">Tous les statuts</option>
              <option value="ACTIVE">En cours</option>
              <option value="DISCHARGED">Sortis</option>
              <option value="TRANSFERRED">Transférés</option>
            </select>
          </label>
        </div>
        <button className="primary-button" onClick={() => setShowAdmitForm(!showAdmitForm)}>
          {showAdmitForm ? "Annuler" : "Admettre un patient"}
        </button>
      </div>

      {showAdmitForm && (
        <div className="card form-card">
          <h3>Admission d'un patient</h3>
          <form onSubmit={handleAdmit} className="form-grid">
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
              Lit (optionnel)
              <select value={bedId} onChange={(e) => setBedId(e.target.value)}>
                <option value="">-- Sans lit --</option>
                {bedOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Motif
              <input
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Motif d'hospitalisation"
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Admission..." : "Admettre"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : stays.length === 0 ? (
        <div className="card">
          <p className="muted">Aucun séjour trouvé.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date d'admission</th>
                  <th>Patient</th>
                  <th>Motif</th>
                  <th>Statut</th>
                  <th>Date de sortie</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {stays.map((stay) => (
                  <tr key={stay.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {stay.admitted_at ? new Date(stay.admitted_at).toLocaleString("fr-FR") : "—"}
                    </td>
                    <td style={{ fontWeight: 600 }}>{getPatientName(stay.patient_id)}</td>
                    <td>{stay.reason || "—"}</td>
                    <td>
                      <span className={`badge ${stayStatusBadge[stay.status] || "badge-gray"}`}>
                        {stayStatusLabel[stay.status] || stay.status}
                      </span>
                    </td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {stay.discharged_at ? new Date(stay.discharged_at).toLocaleString("fr-FR") : "—"}
                    </td>
                    <td>
                      {stay.status === "ACTIVE" && (
                        <button
                          className="secondary-button"
                          style={{ padding: "6px 14px", fontSize: "13px" }}
                          onClick={() => handleDischarge(stay.id)}
                        >
                          Sortie
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
