import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";

type TabKey = "staff" | "oncall";

const TABS: { key: TabKey; label: string }[] = [
  { key: "staff", label: "Personnel" },
  { key: "oncall", label: "Garde" },
];

const STAFF_ROLE_OPTIONS = [
  { value: "DOCTOR", label: "Médecin" },
  { value: "NURSE", label: "Infirmier(e)" },
  { value: "MIDWIFE", label: "Sage-femme" },
  { value: "TECHNICIAN", label: "Technicien" },
  { value: "ADMIN", label: "Administratif" },
  { value: "PHARMACIST", label: "Pharmacien" },
  { value: "LAB_TECH", label: "Laborantin" },
  { value: "OTHER", label: "Autre" },
];

const roleLabel: Record<string, string> = Object.fromEntries(
  STAFF_ROLE_OPTIONS.map((o) => [o.value, o.label])
);

const roleBadge: Record<string, string> = {
  DOCTOR: "badge-blue",
  NURSE: "badge-green",
  MIDWIFE: "badge-yellow",
  TECHNICIAN: "badge-gray",
  ADMIN: "badge-gray",
  PHARMACIST: "badge-green",
  LAB_TECH: "badge-gray",
  OTHER: "badge-gray",
};

export function PersonnelPage({ lookups }: { lookups: LookupData }) {
  const [activeTab, setActiveTab] = useState<TabKey>("staff");

  return (
    <section>
      <h1>Personnel</h1>
      <p className="muted">Gestion du personnel et planning de garde.</p>

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

      {activeTab === "staff" && <StaffTab lookups={lookups} />}
      {activeTab === "oncall" && <OnCallTab lookups={lookups} />}
    </section>
  );
}

/* ─── Staff Tab ──────────────────────────────────────────────── */

function StaffTab({ lookups }: { lookups: LookupData }) {
  const [staff, setStaff] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");

  // Form fields
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [role, setRole] = useState("DOCTOR");
  const [specialty, setSpecialty] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");

  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  const loadStaff = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (roleFilter) params.set("role", roleFilter);
      const qs = params.toString();
      const payload = await apiRequest<any>(`/personnel/staff${qs ? `?${qs}` : ""}`);
      setStaff(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger le personnel.");
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter]);

  useEffect(() => {
    loadStaff();
    const handler = () => loadStaff();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadStaff]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!firstName.trim() || !lastName.trim()) return;
    setSubmitting(true);
    try {
      await apiRequest("/personnel/staff", {
        method: "POST",
        body: JSON.stringify({
          facility_id: facilityId,
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          role,
          specialty: specialty.trim() || undefined,
          phone: phone.trim() || undefined,
          email: email.trim() || undefined,
        }),
      });
      setFirstName("");
      setLastName("");
      setRole("DOCTOR");
      setSpecialty("");
      setPhone("");
      setEmail("");
      setShowForm(false);
      loadStaff();
      showToast("Membre du personnel ajouté.", "success");
    } catch {
      showToast("Erreur lors de l'ajout.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="section-header">
        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <h2 style={{ margin: 0 }}>Personnel</h2>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <input
              type="text"
              placeholder="Rechercher..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ minWidth: "180px" }}
            />
          </label>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              style={{ minWidth: "160px" }}
            >
              <option value="">Tous les rôles</option>
              {STAFF_ROLE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
        </div>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Ajouter"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Nouveau membre du personnel</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Prénom
              <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
            </label>
            <label className="form-control">
              Nom
              <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} required />
            </label>
            <label className="form-control">
              Rôle
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                {STAFF_ROLE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Spécialité
              <input type="text" value={specialty} onChange={(e) => setSpecialty(e.target.value)} placeholder="Ex: Chirurgie" />
            </label>
            <label className="form-control">
              Téléphone
              <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </label>
            <label className="form-control">
              Email
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Ajout..." : "Ajouter"}
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
      ) : staff.length === 0 ? (
        <div className="card">
          <p className="muted">Aucun membre du personnel trouvé.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Prénom</th>
                  <th>Rôle</th>
                  <th>Spécialité</th>
                  <th>Téléphone</th>
                  <th>Email</th>
                </tr>
              </thead>
              <tbody>
                {staff.map((s) => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600 }}>{s.last_name || "—"}</td>
                    <td>{s.first_name || "—"}</td>
                    <td>
                      <span className={`badge ${roleBadge[s.role] || "badge-gray"}`}>
                        {roleLabel[s.role] || s.role}
                      </span>
                    </td>
                    <td>{s.specialty || "—"}</td>
                    <td>{s.phone || "—"}</td>
                    <td>{s.email || "—"}</td>
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

/* ─── On-Call Tab ────────────────────────────────────────────── */

function OnCallTab({ lookups }: { lookups: LookupData }) {
  const [onCallList, setOnCallList] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form fields
  const [staffId, setStaffId] = useState("");
  const [onCallDate, setOnCallDate] = useState("");
  const [shift, setShift] = useState("DAY");

  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  // We'll use staff list for the dropdown
  const [staffOptions, setStaffOptions] = useState<{ value: string; label: string }[]>([]);

  const loadOnCall = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/personnel/on-call");
      setOnCallList(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger le planning de garde.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadStaffForDropdown = useCallback(async () => {
    try {
      const payload = await apiRequest<any>("/personnel/staff");
      const list = Array.isArray(payload.data) ? payload.data : [];
      setStaffOptions(
        list.map((s: Row) => ({
          value: s.id,
          label: `${s.last_name || ""} ${s.first_name || ""} — ${roleLabel[s.role] || s.role || ""}`.trim(),
        }))
      );
    } catch {
      // Silently fail
    }
  }, []);

  useEffect(() => {
    loadOnCall();
    const handler = () => loadOnCall();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadOnCall]);

  useEffect(() => {
    if (showForm) {
      loadStaffForDropdown();
    }
  }, [showForm, loadStaffForDropdown]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!staffId || !onCallDate) return;
    setSubmitting(true);
    try {
      await apiRequest("/personnel/on-call", {
        method: "POST",
        body: JSON.stringify({
          facility_id: facilityId,
          staff_id: staffId,
          on_call_date: onCallDate,
          shift,
        }),
      });
      setStaffId("");
      setOnCallDate("");
      setShift("DAY");
      setShowForm(false);
      loadOnCall();
      showToast("Garde planifiée.", "success");
    } catch {
      showToast("Erreur lors de la planification.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const shiftLabel: Record<string, string> = {
    DAY: "Jour",
    NIGHT: "Nuit",
  };

  const shiftBadge: Record<string, string> = {
    DAY: "badge-yellow",
    NIGHT: "badge-blue",
  };

  // Group by date
  const byDate = onCallList.reduce<Record<string, Row[]>>((acc, item) => {
    const dateKey = item.on_call_date || "—";
    if (!acc[dateKey]) acc[dateKey] = [];
    acc[dateKey].push(item);
    return acc;
  }, {});

  const sortedDates = Object.keys(byDate).sort((a, b) => a.localeCompare(b));

  return (
    <>
      <div className="section-header">
        <h2>Planning de garde</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "Planifier une garde"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Planifier une garde</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">
              Personnel
              <select value={staffId} onChange={(e) => setStaffId(e.target.value)} required>
                <option value="">-- Choisir --</option>
                {staffOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="form-control">
              Date de garde
              <input type="date" value={onCallDate} onChange={(e) => setOnCallDate(e.target.value)} required />
            </label>
            <label className="form-control">
              Tranche horaire
              <select value={shift} onChange={(e) => setShift(e.target.value)}>
                <option value="DAY">Jour</option>
                <option value="NIGHT">Nuit</option>
              </select>
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Planification..." : "Planifier"}
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
      ) : onCallList.length === 0 ? (
        <div className="card">
          <p className="muted">Aucune garde planifiée.</p>
        </div>
      ) : (
        sortedDates.map((date) => (
          <div className="card" key={date}>
            <h3 style={{ marginBottom: "12px" }}>
              {new Date(date).toLocaleDateString("fr-FR", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </h3>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Personnel</th>
                    <th>Tranche</th>
                  </tr>
                </thead>
                <tbody>
                  {byDate[date].map((item) => (
                    <tr key={item.id}>
                      <td style={{ fontWeight: 600 }}>
                        {item.staff_id || "—"}
                      </td>
                      <td>
                        <span className={`badge ${shiftBadge[item.shift] || "badge-gray"}`}>
                          {shiftLabel[item.shift] || item.shift}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}
    </>
  );
}
