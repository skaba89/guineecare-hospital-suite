import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { showToast } from "../components/Toast";
import { useAuth } from "../contexts/AuthContext";
import { useT } from "../i18n";
import {
  Plus, Search, RefreshCw, X, Eye, EyeOff, Mail, Shield, Building2, UserCog,
} from "lucide-react";

type User = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  facility_id: string | null;
  role: string;
  is_active: boolean;
  created_at?: string;
};

type Facility = { id: string; name: string; code: string };

const ROLE_OPTIONS = [
  { value: "SUPER_ADMIN", label: "Super Administrateur" },
  { value: "ADMIN", label: "Administrateur" },
  { value: "DOCTOR", label: "Médecin" },
  { value: "NURSE", label: "Infirmier(e)" },
  { value: "PHARMACIST", label: "Pharmacien" },
  { value: "LAB_TECH", label: "Technicien Labo" },
  { value: "MIDWIFE", label: "Sage-femme" },
  { value: "CASHIER", label: "Caissier" },
];

const roleLabel: Record<string, string> = Object.fromEntries(
  ROLE_OPTIONS.map((o) => [o.value, o.label])
);

const roleBadge: Record<string, string> = {
  SUPER_ADMIN: "badge-red",
  ADMIN: "badge-yellow",
  DOCTOR: "badge-blue",
  NURSE: "badge-green",
  PHARMACIST: "badge-green",
  LAB_TECH: "badge-gray",
  CASHIER: "badge-gray",
  MIDWIFE: "badge-yellow",
};

export function UsersPage() {
  const t = useT();
  const { isSuperAdmin } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    role: "NURSE",
    facility_id: "",
  });

  const facilityName = useCallback(
    (id: string | null) => facilities.find((f) => f.id === id)?.name || "—",
    [facilities]
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page_size: "1000" });
      if (search) params.set("search", search);
      if (roleFilter) params.set("role", roleFilter);
      const res = await apiRequest<{ data: User[]; total: number }>(
        `/users?${params.toString()}`
      );
      setUsers(res.data || []);
    } catch (e: any) {
      showToast("Erreur de chargement: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter]);

  const loadFacilities = useCallback(async () => {
    if (!isSuperAdmin) return;
    try {
      const res = await apiRequest<{ data: Facility[] }>(
        "/facilities?page_size=1000"
      );
      setFacilities(res.data || []);
    } catch {
      /* ignore */
    }
  }, [isSuperAdmin]);

  useEffect(() => {
    load();
    loadFacilities();
  }, [load, loadFacilities]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload: any = {
        email: form.email,
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
        role: form.role,
      };
      if (isSuperAdmin && form.facility_id) {
        payload.facility_id = form.facility_id;
      }
      await apiRequest("/users", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showToast("Utilisateur créé avec succès", "success");
      setShowModal(false);
      setForm({ email: "", password: "", first_name: "", last_name: "", role: "NURSE", facility_id: "" });
      await load();
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleActive = async (user: User) => {
    try {
      await apiRequest(`/users/${user.id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: !user.is_active }),
      });
      showToast(`Utilisateur ${!user.is_active ? "activé" : "désactivé"}`, "success");
      await load();
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>
            <UserCog size={28} style={{ display: "inline", marginRight: 8, verticalAlign: "middle" }} />
            {t("users.title")}
          </h1>
          <p className="muted">{t("users.description")}</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-secondary" onClick={load} title={t("action.refresh")}>
            <RefreshCw size={16} />
          </button>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> {t("users.new")}
          </button>
        </div>
      </div>

      <div className="filters-bar" style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <div style={{ position: "relative", flex: 1, minWidth: 250 }}>
          <Search size={16} style={{ position: "absolute", left: 10, top: 10, color: "#94a3b8" }} />
          <input
            className="input"
            placeholder={`${t("action.search")} (nom, email)...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 34 }}
            onKeyDown={(e) => e.key === "Enter" && load()}
          />
        </div>
        <select
          className="input"
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          style={{ width: 200 }}
        >
          <option value="">{t("label.all_roles")}</option>
          {ROLE_OPTIONS.map((r) => (
            <option key={r.value} value={r.value}>{r.label}</option>
          ))}
        </select>
        <button className="btn btn-secondary" onClick={load}>{t("action.filter")}</button>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Email</th>
              <th>Rôle</th>
              {isSuperAdmin && <th>Établissement</th>}
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={isSuperAdmin ? 6 : 5} style={{ textAlign: "center", padding: 24 }}>{t("label.loading")}</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={isSuperAdmin ? 6 : 5} style={{ textAlign: "center", padding: 24 }}>{t("users.empty")}</td></tr>
            ) : (
              users.map((u) => (
                <tr key={u.id}>
                  <td>{u.first_name} {u.last_name}</td>
                  <td>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                      <Mail size={14} /> {u.email}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${roleBadge[u.role] || "badge-gray"}`}>
                      {roleLabel[u.role] || u.role}
                    </span>
                  </td>
                  {isSuperAdmin && <td>{facilityName(u.facility_id)}</td>}
                  <td>
                    <span className={`badge ${u.is_active ? "badge-green" : "badge-red"}`}>
                      {u.is_active ? t("label.active_only") : t("label.inactive_only")}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => toggleActive(u)}
                      title={u.is_active ? t("action.deactivate") : t("action.activate")}
                    >
                      {u.is_active ? t("action.deactivate") : t("action.activate")}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h2>{t("users.modal.title")}</h2>
              <button className="btn-icon" onClick={() => setShowModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleSubmit} className="modal-body">
              <div className="form-group">
                <label>Prénom *</label>
                <input
                  className="input"
                  required
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Nom *</label>
                <input
                  className="input"
                  required
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Email *</label>
                <input
                  className="input"
                  type="email"
                  required
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Mot de passe * (min. 8 caractères)</label>
                <div style={{ position: "relative" }}>
                  <input
                    className="input"
                    type={showPassword ? "text" : "password"}
                    required
                    minLength={8}
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    style={{ paddingRight: 36 }}
                  />
                  <button
                    type="button"
                    className="btn-icon"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ position: "absolute", right: 6, top: 6 }}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              <div className="form-group">
                <label>Rôle *</label>
                <select
                  className="input"
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                >
                  {ROLE_OPTIONS
                    .filter((r) => r.value !== "SUPER_ADMIN" || isSuperAdmin)
                    .map((r) => (
                      <option key={r.value} value={r.value}>{r.label}</option>
                    ))}
                </select>
              </div>
              {isSuperAdmin && (
                <div className="form-group">
                  <label>Établissement *</label>
                  <select
                    className="input"
                    required
                    value={form.facility_id}
                    onChange={(e) => setForm({ ...form, facility_id: e.target.value })}
                  >
                    <option value="">— Choisir —</option>
                    {facilities.map((f) => (
                      <option key={f.id} value={f.id}>{f.name}</option>
                    ))}
                  </select>
                </div>
              )}
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 16 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  {t("action.cancel")}
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Création..." : t("users.submit.create")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
