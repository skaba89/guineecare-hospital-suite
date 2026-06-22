import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { showToast } from "../components/Toast";
import { useAuth } from "../contexts/AuthContext";
import {
  Plus, Search, RefreshCw, X, Building2, MapPin, Phone, BedDouble,
} from "lucide-react";

type Facility = {
  id: string;
  name: string;
  code: string;
  type: string;
  address: string | null;
  city: string | null;
  phone: string | null;
  email: string | null;
  is_active: boolean;
};

const FACILITY_TYPES = [
  { value: "CHU", label: "Centre Hospitalier Universitaire" },
  { value: "CHR", label: "Centre Hospitalier Régional" },
  { value: "HOPITAL_REGIONAL", label: "Hôpital Régional" },
  { value: "HOPITAL_DISTRICT", label: "Hôpital de District" },
  { value: "CLINIQUE", label: "Clinique privée" },
  { value: "CENTRE_SANTE", label: "Centre de Santé" },
  { value: "POSTE_SANTE", label: "Poste de Santé" },
  { value: "MATERNITE", label: "Maternité" },
];

const typeLabel: Record<string, string> = Object.fromEntries(
  FACILITY_TYPES.map((t) => [t.value, t.label])
);

export function FacilitiesPage() {
  const { isSuperAdmin } = useAuth();
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    name: "",
    code: "",
    type: "HOPITAL_REGIONAL",
    address: "",
    city: "Conakry",
    phone: "",
    email: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page_size: "1000" });
      if (search) params.set("search", search);
      const res = await apiRequest<{ data: Facility[]; total: number }>(
        `/facilities?${params.toString()}`
      );
      setFacilities(res.data || []);
    } catch (e: any) {
      showToast("Erreur de chargement: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiRequest("/facilities", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          is_active: true,
        }),
      });
      showToast("Établissement créé", "success");
      setShowModal(false);
      setForm({ name: "", code: "", type: "HOPITAL_REGIONAL", address: "", city: "Conakry", phone: "", email: "" });
      await load();
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>
            <Building2 size={28} style={{ display: "inline", marginRight: 8, verticalAlign: "middle" }} />
            Établissements de Santé
          </h1>
          <p className="muted">
            {isSuperAdmin ? "Tous les établissements (vue nationale)" : "Mon établissement"}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-secondary" onClick={load} title="Rafraîchir">
            <RefreshCw size={16} />
          </button>
          {isSuperAdmin && (
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              <Plus size={16} /> Nouvel établissement
            </button>
          )}
        </div>
      </div>

      <div className="filters-bar" style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <div style={{ position: "relative", flex: 1, maxWidth: 400 }}>
          <Search size={16} style={{ position: "absolute", left: 10, top: 10, color: "#94a3b8" }} />
          <input
            className="input"
            placeholder="Rechercher par nom ou code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 34 }}
            onKeyDown={(e) => e.key === "Enter" && load()}
          />
        </div>
        <button className="btn btn-secondary" onClick={load}>Rechercher</button>
      </div>

      {loading ? (
        <div className="card" style={{ padding: 24, textAlign: "center" }}>Chargement...</div>
      ) : facilities.length === 0 ? (
        <div className="card" style={{ padding: 24, textAlign: "center" }}>Aucun établissement</div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
          {facilities.map((f) => (
            <div key={f.id} className="card" style={{ padding: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{f.name}</h3>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>Code: {f.code}</div>
                </div>
                <span className={`badge ${f.is_active ? "badge-green" : "badge-red"}`}>
                  {f.is_active ? "Actif" : "Inactif"}
                </span>
              </div>
              <div style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>
                {typeLabel[f.type] || f.type}
              </div>
              {f.address && (
                <div style={{ fontSize: 12, color: "#64748b", display: "flex", alignItems: "center", gap: 4, marginBottom: 4 }}>
                  <MapPin size={12} /> {f.address}{f.city ? `, ${f.city}` : ""}
                </div>
              )}
              {f.phone && (
                <div style={{ fontSize: 12, color: "#64748b", display: "flex", alignItems: "center", gap: 4, marginBottom: 4 }}>
                  <Phone size={12} /> {f.phone}
                </div>
              )}
              {f.email && (
                <div style={{ fontSize: 12, color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                  <Building2 size={12} /> {f.email}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 550 }}>
            <div className="modal-header">
              <h2>Nouvel établissement</h2>
              <button className="btn-icon" onClick={() => setShowModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleSubmit} className="modal-body">
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 12 }}>
                <div className="form-group">
                  <label>Nom *</label>
                  <input className="input" required value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Code *</label>
                  <input className="input" required value={form.code}
                    onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} />
                </div>
              </div>
              <div className="form-group">
                <label>Type *</label>
                <select className="input" value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value })}>
                  {FACILITY_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Adresse</label>
                <input className="input" value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div className="form-group">
                  <label>Ville</label>
                  <input className="input" value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Téléphone</label>
                  <input className="input" value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                </div>
              </div>
              <div className="form-group">
                <label>Email</label>
                <input className="input" type="email" value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </div>
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 16 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Annuler</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Création..." : "Créer"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
