import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";
import { useAuth } from "../contexts/AuthContext";
import { useT } from "../i18n";

type TabKey = "staff" | "oncall" | "leaves" | "contracts" | "stats";

const TABS: { key: TabKey; label: string; permission: string }[] = [
  { key: "staff", label: "personnel.tab.staff", permission: "personnel.read" },
  { key: "oncall", label: "personnel.tab.oncall", permission: "personnel.read" },
  { key: "leaves", label: "personnel.tab.leaves", permission: "personnel.read" },
  { key: "contracts", label: "personnel.tab.contracts", permission: "personnel.read" },
  { key: "stats", label: "personnel.tab.stats", permission: "personnel.read" },
];

const STAFF_ROLE_OPTIONS = [
  { value: "MEDECIN", label: "Médecin" },
  { value: "INFIRMIER", label: "Infirmier(e)" },
  { value: "SAGE_FEMME", label: "Sage-femme" },
  { value: "TECHNICIEN", label: "Technicien" },
  { value: "ADMINISTRATIF", label: "Administratif" },
  { value: "PHARMACIEN", label: "Pharmacien" },
  { value: "LABORANTIN", label: "Laborantin" },
  { value: "AUTRE", label: "Autre" },
];

const LEAVE_TYPE_OPTIONS = [
  { value: "CONGE_ANNUEL", label: "Congé annuel" },
  { value: "MALADIE", label: "Maladie" },
  { value: "MATERNITE", label: "Maternité" },
  { value: "PATERNITE", label: "Paternité" },
  { value: "SANS_SOLDE", label: "Sans solde" },
  { value: "AUTORISATION", label: "Autorisation d'absence" },
];

const CONTRACT_TYPE_OPTIONS = [
  { value: "CDI", label: "CDI" },
  { value: "CDD", label: "CDD" },
  { value: "INTERIM", label: "Intérim" },
  { value: "STAGIAIRE", label: "Stagiaire" },
  { value: "CONSULTANT", label: "Consultant" },
];

const STATUS_OPTIONS = [
  { value: "ACTIVE", label: "Actif" },
  { value: "ON_LEAVE", label: "En congé" },
  { value: "RESIGNED", label: "Démissionné" },
  { value: "RETIRED", label: "Retraité" },
  { value: "SUSPENDED", label: "Suspendu" },
];

const roleLabel: Record<string, string> = Object.fromEntries(
  STAFF_ROLE_OPTIONS.map((o) => [o.value, o.label])
);

const leaveTypeLabel: Record<string, string> = Object.fromEntries(
  LEAVE_TYPE_OPTIONS.map((o) => [o.value, o.label])
);

const contractTypeLabel: Record<string, string> = Object.fromEntries(
  CONTRACT_TYPE_OPTIONS.map((o) => [o.value, o.label])
);

const roleBadge: Record<string, string> = {
  MEDECIN: "badge-blue",
  INFIRMIER: "badge-green",
  SAGE_FEMME: "badge-yellow",
  TECHNICIEN: "badge-gray",
  ADMINISTRATIF: "badge-gray",
  PHARMACIEN: "badge-green",
  LABORANTIN: "badge-gray",
  AUTRE: "badge-gray",
  DOCTOR: "badge-blue",
  NURSE: "badge-green",
  MIDWIFE: "badge-yellow",
  PHARMACIST: "badge-green",
  LAB_TECH: "badge-gray",
};

const statusBadge: Record<string, string> = {
  ACTIVE: "badge-green",
  ON_LEAVE: "badge-yellow",
  RESIGNED: "badge-gray",
  RETIRED: "badge-gray",
  SUSPENDED: "badge-red",
  PENDING: "badge-yellow",
  APPROVED: "badge-green",
  REJECTED: "badge-red",
  CANCELLED: "badge-gray",
};

const shiftLabel: Record<string, string> = { DAY: "Jour", NIGHT: "Nuit", FULL_DAY: "24h" };
const shiftBadge: Record<string, string> = { DAY: "badge-yellow", NIGHT: "badge-blue", FULL_DAY: "badge-red" };

export function PersonnelPage({ lookups, onCreated }: { lookups: LookupData; onCreated?: () => void }) {
  const t = useT();
  const { hasPermission } = useAuth();
  const canManage = hasPermission("personnel.manage");
  const [activeTab, setActiveTab] = useState<TabKey>("staff");

  const visibleTabs = TABS.filter((tab) => hasPermission(tab.permission));

  return (
    <section>
      <h1>{t("nav.personnel")}</h1>
      <p className="muted">{t("personnel.description")}</p>

      <div className="tab-bar">
        {visibleTabs.map((tab) => (
          <button
            key={tab.key}
            className={`tab-button ${activeTab === tab.key ? "active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {t(tab.label)}
          </button>
        ))}
      </div>

      {activeTab === "staff" && <StaffTab lookups={lookups} canManage={canManage} onCreated={onCreated} />}
      {activeTab === "oncall" && <OnCallTab lookups={lookups} canManage={canManage} />}
      {activeTab === "leaves" && <LeavesTab lookups={lookups} canManage={canManage} />}
      {activeTab === "contracts" && <ContractsTab lookups={lookups} canManage={canManage} />}
      {activeTab === "stats" && <StatsTab />}
    </section>
  );
}

/* ─── Staff Tab ──────────────────────────────────────────────── */

function StaffTab({ lookups, canManage, onCreated }: { lookups: LookupData; canManage: boolean; onCreated?: () => void }) {
  const t = useT();
  const [staff, setStaff] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Form fields
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [role, setRole] = useState("MEDECIN");
  const [specialty, setSpecialty] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [contractType, setContractType] = useState("CDI");
  const [salaryGrade, setSalaryGrade] = useState("");
  const [hireDate, setHireDate] = useState("");

  const loadStaff = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (roleFilter) params.set("profession", roleFilter);
      if (statusFilter) params.set("status", statusFilter);
      const qs = params.toString();
      const payload = await apiRequest<any>(`/personnel/staff${qs ? `?${qs}` : ""}`);
      setStaff(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger le personnel.");
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter, statusFilter]);

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
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          role,
          specialty: specialty.trim() || undefined,
          phone: phone.trim() || undefined,
          email: email.trim() || undefined,
          contract_type: contractType || undefined,
          salary_grade: salaryGrade.trim() || undefined,
          hire_date: hireDate || undefined,
        }),
      });
      setFirstName(""); setLastName(""); setRole("MEDECIN"); setSpecialty("");
      setPhone(""); setEmail(""); setContractType("CDI"); setSalaryGrade(""); setHireDate("");
      setShowForm(false);
      loadStaff();
      onCreated?.();
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
          <h2 style={{ margin: 0 }}>{t("personnel.tab.staff")}</h2>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <input type="text" placeholder={t("action.search") + "..."} value={search} onChange={(e) => setSearch(e.target.value)} style={{ minWidth: "180px" }} />
          </label>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} style={{ minWidth: "160px" }}>
              <option value="">{t("label.all_roles")}</option>
              {STAFF_ROLE_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
            </select>
          </label>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ minWidth: "140px" }}>
              <option value="">{t("label.all_statuses")}</option>
              {STATUS_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
            </select>
          </label>
        </div>
        {canManage && (
          <button className="primary-button" onClick={() => setShowForm(!showForm)}>
            {showForm ? t("action.cancel") : t("action.add")}
          </button>
        )}
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>{t("personnel.staff.new")}</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">Prénom<input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} required /></label>
            <label className="form-control">Nom<input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} required /></label>
            <label className="form-control">Profession
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                {STAFF_ROLE_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            </label>
            <label className="form-control">Spécialité<input type="text" value={specialty} onChange={(e) => setSpecialty(e.target.value)} placeholder="Ex: Chirurgie" /></label>
            <label className="form-control">Téléphone<input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} /></label>
            <label className="form-control">Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
            <label className="form-control">Type contrat
              <select value={contractType} onChange={(e) => setContractType(e.target.value)}>
                {CONTRACT_TYPE_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            </label>
            <label className="form-control">Échelle salariale<input type="text" value={salaryGrade} onChange={(e) => setSalaryGrade(e.target.value)} placeholder="Ex: A5" /></label>
            <label className="form-control">Date d'embauche<input type="date" value={hireDate} onChange={(e) => setHireDate(e.target.value)} /></label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>{submitting ? "Ajout..." : "Ajouter"}</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}><div className="spinner" /></div>
      ) : error ? (
        <p style={{ color: "crimson" }}>{error}</p>
      ) : staff.length === 0 ? (
        <div className="card"><p className="muted">{t("personnel.staff.empty")}</p></div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr><th>N° Employé</th><th>Nom</th><th>Prénom</th><th>Profession</th><th>Spécialité</th><th>Statut</th><th>Contrat</th><th>Téléphone</th></tr>
              </thead>
              <tbody>
                {staff.map((s) => (
                  <tr key={s.id}>
                    <td style={{ fontFamily: "monospace", fontSize: "12px" }}>{s.employee_number || "—"}</td>
                    <td style={{ fontWeight: 600 }}>{s.last_name || "—"}</td>
                    <td>{s.first_name || "—"}</td>
                    <td>
                      <span className={`badge ${roleBadge[s.profession || s.role] || "badge-gray"}`}>
                        {roleLabel[s.profession || s.role] || s.profession || s.role}
                      </span>
                    </td>
                    <td>{s.specialty || "—"}</td>
                    <td>
                      <span className={`badge ${statusBadge[s.status] || "badge-gray"}`}>
                        {STATUS_OPTIONS.find((o) => o.value === s.status)?.label || s.status}
                      </span>
                    </td>
                    <td>{contractTypeLabel[s.contract_type] || s.contract_type || "—"}</td>
                    <td>{s.phone || "—"}</td>
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

function OnCallTab({ lookups, canManage }: { lookups: LookupData; canManage: boolean }) {
  const t = useT();
  const [onCallList, setOnCallList] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [staffId, setStaffId] = useState("");
  const [onCallDate, setOnCallDate] = useState("");
  const [shift, setShift] = useState("DAY");
  const [staffOptions, setStaffOptions] = useState<{ value: string; label: string }[]>([]);

  const loadOnCall = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/personnel/on-call?page_size=1000");
      setOnCallList(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger le planning de garde.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadStaffForDropdown = useCallback(async () => {
    try {
      const payload = await apiRequest<any>("/personnel/staff?page_size=1000");
      const list = Array.isArray(payload.data) ? payload.data : [];
      setStaffOptions(
        list.map((s: Row) => ({
          value: s.id,
          label: `${s.last_name || ""} ${s.first_name || ""} — ${roleLabel[s.profession || s.role] || s.profession || s.role || ""}`.trim(),
        }))
      );
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    loadOnCall();
    const handler = () => loadOnCall();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadOnCall]);

  useEffect(() => {
    if (showForm) loadStaffForDropdown();
  }, [showForm, loadStaffForDropdown]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!staffId || !onCallDate) return;
    setSubmitting(true);
    try {
      await apiRequest("/personnel/on-call", {
        method: "POST",
        body: JSON.stringify({ staff_id: staffId, on_call_date: onCallDate, shift }),
      });
      setStaffId(""); setOnCallDate(""); setShift("DAY"); setShowForm(false);
      loadOnCall();
      showToast("Garde planifiée.", "success");
    } catch {
      showToast("Erreur lors de la planification.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  function getStaffName(sid: string): string {
    const staffMember = lookups.staff.find((s) => s.id === sid);
    if (!staffMember) return "Inconnu";
    return `${staffMember.first_name || ""} ${staffMember.last_name || ""}`.trim() || staffMember.employee_number || "N/A";
  }

  const byDate = onCallList.reduce<Record<string, Row[]>>((acc, item) => {
    const dateKey = item.on_call_date ? item.on_call_date.toString().split("T")[0] : "—";
    if (!acc[dateKey]) acc[dateKey] = [];
    acc[dateKey].push(item);
    return acc;
  }, {});

  const sortedDates = Object.keys(byDate).sort((a, b) => a.localeCompare(b));

  return (
    <>
      <div className="section-header">
        <h2>{t("personnel.oncall.title")}</h2>
        {canManage && (
          <button className="primary-button" onClick={() => setShowForm(!showForm)}>
            {showForm ? t("action.cancel") : t("personnel.oncall.new")}
          </button>
        )}
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>{t("personnel.oncall.new")}</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">Personnel
              <select value={staffId} onChange={(e) => setStaffId(e.target.value)} required>
                <option value="">-- Choisir --</option>
                {staffOptions.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            </label>
            <label className="form-control">Date de garde<input type="date" value={onCallDate} onChange={(e) => setOnCallDate(e.target.value)} required /></label>
            <label className="form-control">Tranche horaire
              <select value={shift} onChange={(e) => setShift(e.target.value)}>
                <option value="DAY">Jour</option><option value="NIGHT">Nuit</option><option value="FULL_DAY">24h</option>
              </select>
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>{submitting ? "Planification..." : "Planifier"}</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}><div className="spinner" /></div>
      ) : error ? (
        <p style={{ color: "crimson" }}>{error}</p>
      ) : onCallList.length === 0 ? (
        <div className="card"><p className="muted">{t("personnel.oncall.empty")}</p></div>
      ) : (
        sortedDates.map((date) => (
          <div className="card" key={date}>
            <h3 style={{ marginBottom: "12px" }}>
              {new Date(date).toLocaleDateString("fr-FR", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
            </h3>
            <div className="table-wrapper">
              <table className="table">
                <thead><tr><th>Personnel</th><th>Tranche</th></tr></thead>
                <tbody>
                  {byDate[date].map((item) => (
                    <tr key={item.id}>
                      <td style={{ fontWeight: 600 }}>{getStaffName(item.staff_id)}</td>
                      <td>
                        <span className={`badge ${shiftBadge[item.shift_type || item.shift] || "badge-gray"}`}>
                          {shiftLabel[item.shift_type || item.shift] || item.shift_type || item.shift}
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

/* ─── Leaves Tab ─────────────────────────────────────────────── */

function LeavesTab({ lookups, canManage }: { lookups: LookupData; canManage: boolean }) {
  const t = useT();
  const [leaves, setLeaves] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");

  const [staffId, setStaffId] = useState("");
  const [leaveType, setLeaveType] = useState("CONGE_ANNUEL");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");
  const [staffOptions, setStaffOptions] = useState<{ value: string; label: string }[]>([]);

  const loadLeaves = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      const qs = params.toString();
      const payload = await apiRequest<any>(`/personnel/leaves${qs ? `?${qs}` : ""}`);
      setLeaves(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les congés.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  const loadStaffForDropdown = useCallback(async () => {
    try {
      const payload = await apiRequest<any>("/personnel/staff?status=ACTIVE&page_size=1000");
      const list = Array.isArray(payload.data) ? payload.data : [];
      setStaffOptions(
        list.map((s: Row) => ({
          value: s.id,
          label: `${s.last_name || ""} ${s.first_name || ""}`.trim(),
        }))
      );
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    loadLeaves();
    const handler = () => loadLeaves();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadLeaves]);

  useEffect(() => {
    if (showForm) loadStaffForDropdown();
  }, [showForm, loadStaffForDropdown]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!staffId || !startDate || !endDate) return;
    setSubmitting(true);
    try {
      await apiRequest("/personnel/leaves", {
        method: "POST",
        body: JSON.stringify({ staff_id: staffId, leave_type: leaveType, start_date: startDate, end_date: endDate, reason: reason.trim() || undefined }),
      });
      setStaffId(""); setLeaveType("CONGE_ANNUEL"); setStartDate(""); setEndDate(""); setReason(""); setShowForm(false);
      loadLeaves();
      showToast("Demande de congé créée.", "success");
    } catch {
      showToast("Erreur lors de la création.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAction(leaveId: string, action: string) {
    try {
      await apiRequest(`/personnel/leaves/${leaveId}`, {
        method: "PUT",
        body: JSON.stringify({ status: action }),
      });
      loadLeaves();
      showToast(`Congé ${action === "APPROVED" ? "approuvé" : "refusé"}.`, "success");
    } catch {
      showToast("Erreur.", "error");
    }
  }

  function getStaffName(sid: string): string {
    const s = lookups.staff.find((s) => s.id === sid);
    return s ? `${s.first_name || ""} ${s.last_name || ""}`.trim() : "Inconnu";
  }

  return (
    <>
      <div className="section-header">
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>{t("personnel.leaves.title")}</h2>
          <label className="toolbar-control" style={{ marginBottom: 0 }}>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ minWidth: "160px" }}>
              <option value="">Tous</option>
              <option value="PENDING">En attente</option>
              <option value="APPROVED">Approuvé</option>
              <option value="REJECTED">Refusé</option>
            </select>
          </label>
        </div>
        {canManage && (
          <button className="primary-button" onClick={() => setShowForm(!showForm)}>
            {showForm ? t("action.cancel") : t("personnel.leaves.new")}
          </button>
        )}
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>{t("personnel.leaves.new")}</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">Personnel
              <select value={staffId} onChange={(e) => setStaffId(e.target.value)} required>
                <option value="">-- Choisir --</option>
                {staffOptions.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            </label>
            <label className="form-control">Type de congé
              <select value={leaveType} onChange={(e) => setLeaveType(e.target.value)}>
                {LEAVE_TYPE_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            </label>
            <label className="form-control">Date début<input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required /></label>
            <label className="form-control">Date fin<input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required /></label>
            <label className="form-control">Motif<input type="text" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Optionnel" /></label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>{submitting ? "Création..." : "Créer"}</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}><div className="spinner" /></div>
      ) : error ? (
        <p style={{ color: "crimson" }}>{error}</p>
      ) : leaves.length === 0 ? (
        <div className="card"><p className="muted">{t("personnel.leaves.empty")}</p></div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead><tr><th>Personnel</th><th>Type</th><th>Début</th><th>Fin</th><th>Statut</th><th>Actions</th></tr></thead>
              <tbody>
                {leaves.map((l) => (
                  <tr key={l.id}>
                    <td style={{ fontWeight: 600 }}>{getStaffName(l.staff_id)}</td>
                    <td>{leaveTypeLabel[l.leave_type] || l.leave_type}</td>
                    <td>{l.start_date ? new Date(l.start_date).toLocaleDateString("fr-FR") : "—"}</td>
                    <td>{l.end_date ? new Date(l.end_date).toLocaleDateString("fr-FR") : "—"}</td>
                    <td><span className={`badge ${statusBadge[l.status] || "badge-gray"}`}>{STATUS_OPTIONS.find((o) => o.value === l.status)?.label || l.status}</span></td>
                    <td>
                      {canManage && l.status === "PENDING" && (
                        <div style={{ display: "flex", gap: "6px" }}>
                          <button className="primary-button" style={{ padding: "2px 10px", fontSize: "12px" }} onClick={() => handleAction(l.id, "APPROVED")}>{t("action.approve")}</button>
                          <button className="button" style={{ padding: "2px 10px", fontSize: "12px", background: "#ef4444", color: "white" }} onClick={() => handleAction(l.id, "REJECTED")}>{t("action.reject")}</button>
                        </div>
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

/* ─── Contracts Tab ──────────────────────────────────────────── */

function ContractsTab({ lookups, canManage }: { lookups: LookupData; canManage: boolean }) {
  const t = useT();
  const [contracts, setContracts] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [staffId, setStaffId] = useState("");
  const [contractType, setContractType] = useState("CDI");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [position, setPosition] = useState("");
  const [salaryGrade, setSalaryGrade] = useState("");
  const [staffOptions, setStaffOptions] = useState<{ value: string; label: string }[]>([]);

  const loadContracts = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/personnel/contracts?page_size=1000");
      setContracts(Array.isArray(payload.data) ? payload.data : []);
    } catch {
      setError("Impossible de charger les contrats.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadStaffForDropdown = useCallback(async () => {
    try {
      const payload = await apiRequest<any>("/personnel/staff?page_size=1000");
      const list = Array.isArray(payload.data) ? payload.data : [];
      setStaffOptions(
        list.map((s: Row) => ({
          value: s.id,
          label: `${s.last_name || ""} ${s.first_name || ""}`.trim(),
        }))
      );
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    loadContracts();
    const handler = () => loadContracts();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadContracts]);

  useEffect(() => {
    if (showForm) loadStaffForDropdown();
  }, [showForm, loadStaffForDropdown]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!staffId || !startDate) return;
    setSubmitting(true);
    try {
      await apiRequest("/personnel/contracts", {
        method: "POST",
        body: JSON.stringify({
          staff_id: staffId, contract_type: contractType, start_date: startDate,
          end_date: endDate || undefined, position: position.trim() || undefined,
          salary_grade: salaryGrade.trim() || undefined,
        }),
      });
      setStaffId(""); setContractType("CDI"); setStartDate(""); setEndDate("");
      setPosition(""); setSalaryGrade(""); setShowForm(false);
      loadContracts();
      showToast("Contrat créé.", "success");
    } catch {
      showToast("Erreur lors de la création.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  function getStaffName(sid: string): string {
    const s = lookups.staff.find((s) => s.id === sid);
    return s ? `${s.first_name || ""} ${s.last_name || ""}`.trim() : "Inconnu";
  }

  return (
    <>
      <div className="section-header">
        <h2>{t("personnel.contracts.title")}</h2>
        {canManage && (
          <button className="primary-button" onClick={() => setShowForm(!showForm)}>
            {showForm ? t("action.cancel") : t("personnel.contracts.new")}
          </button>
        )}
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>{t("personnel.contracts.new")}</h3>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="form-control">Personnel
              <select value={staffId} onChange={(e) => setStaffId(e.target.value)} required>
                <option value="">-- Choisir --</option>
                {staffOptions.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            </label>
            <label className="form-control">Type
              <select value={contractType} onChange={(e) => setContractType(e.target.value)}>
                {CONTRACT_TYPE_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            </label>
            <label className="form-control">Date début<input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required /></label>
            <label className="form-control">Date fin (CDD)<input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></label>
            <label className="form-control">Poste<input type="text" value={position} onChange={(e) => setPosition(e.target.value)} placeholder="Ex: Médecin chef de service" /></label>
            <label className="form-control">Échelle salariale<input type="text" value={salaryGrade} onChange={(e) => setSalaryGrade(e.target.value)} placeholder="Ex: A5" /></label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>{submitting ? "Création..." : "Créer"}</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}><div className="spinner" /></div>
      ) : error ? (
        <p style={{ color: "crimson" }}>{error}</p>
      ) : contracts.length === 0 ? (
        <div className="card"><p className="muted">{t("personnel.contracts.empty")}</p></div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead><tr><th>Personnel</th><th>Type</th><th>Poste</th><th>Début</th><th>Fin</th><th>Échelle</th><th>Statut</th></tr></thead>
              <tbody>
                {contracts.map((c) => (
                  <tr key={c.id}>
                    <td style={{ fontWeight: 600 }}>{getStaffName(c.staff_id)}</td>
                    <td>{contractTypeLabel[c.contract_type] || c.contract_type}</td>
                    <td>{c.position || "—"}</td>
                    <td>{c.start_date ? new Date(c.start_date).toLocaleDateString("fr-FR") : "—"}</td>
                    <td>{c.end_date ? new Date(c.end_date).toLocaleDateString("fr-FR") : "—"}</td>
                    <td>{c.salary_grade || "—"}</td>
                    <td><span className={`badge ${statusBadge[c.status] || "badge-gray"}`}>{c.status === "ACTIVE" ? "Actif" : c.status}</span></td>
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

/* ─── Stats Tab ──────────────────────────────────────────────── */

function StatsTab() {
  const t = useT();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadStats = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<any>("/personnel/stats?page_size=1000");
      setStats(payload.data);
    } catch {
      setError("Impossible de charger les statistiques.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadStats(); }, [loadStats]);

  if (loading) return <div className="card" style={{ textAlign: "center", padding: "32px" }}><div className="spinner" /></div>;
  if (error) return <p style={{ color: "crimson" }}>{error}</p>;
  if (!stats) return <div className="card"><p className="muted">{t("label.no_data")}</p></div>;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "16px" }}>
      <div className="card">
        <h3>Effectif total</h3>
        <p style={{ fontSize: "2rem", fontWeight: 700, margin: "8px 0" }}>{stats.total_staff || 0}</p>
      </div>
      <div className="card">
        <h3>Par profession</h3>
        {Object.entries(stats.by_profession || {}).map(([prof, count]) => (
          <div key={prof} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
            <span>{roleLabel[prof] || prof}</span>
            <span style={{ fontWeight: 600 }}>{count as number}</span>
          </div>
        ))}
      </div>
      <div className="card">
        <h3>Par statut</h3>
        {Object.entries(stats.by_status || {}).map(([st, count]) => (
          <div key={st} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
            <span>{STATUS_OPTIONS.find((o) => o.value === st)?.label || st}</span>
            <span style={{ fontWeight: 600 }}>{count as number}</span>
          </div>
        ))}
      </div>
      <div className="card">
        <h3>Congés en attente</h3>
        <p style={{ fontSize: "2rem", fontWeight: 700, margin: "8px 0", color: "#f59e0b" }}>{stats.pending_leaves || 0}</p>
      </div>
    </div>
  );
}
