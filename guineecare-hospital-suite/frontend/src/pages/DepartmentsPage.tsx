import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { showToast } from "../components/Toast";
import { useAuth } from "../contexts/AuthContext";
import {
  Plus, Search, RefreshCw, X, Building2, Layers, Folder,
} from "lucide-react";

type Department = {
  id: string;
  name: string;
  code: string;
  facility_id: string;
  description: string | null;
  is_active: boolean;
};

type Facility = { id: string; name: string; code: string };

export function DepartmentsPage() {
  const { isSuperAdmin } = useAuth();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    name: "",
    code: "",
    facility_id: "",
    description: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page_size: "1000" });
      if (search) params.set("search", search);
      const res = await apiRequest<{ data: Department[]; total: number }>(
        `/departments?${params.toString()}`
      );
      setDepartments(res.data || []);
    } catch (e: any) {
      showToast("Erreur de chargement: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  }, [search]);

  const loadFacilities = useCallback(async () => {
    if (!isSuperAdmin) return;
    try {
      const res = await apiRequest<{ data: Facility[] }>("/facilities?page_size=1000");
      setFacilities(res.data || []);
    } catch {
      /* ignore */
    }
  }, [isSuperAdmin]);

  useEffect(() => {
    load();
    loadFacilities();
  }, [load, loadFacilities]);

  const facilityName = useCallback(
    (id: string) => facilities.find((f) => f.id === id)?.name || id,
    [facilities]
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiRequest("/departments", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          is_active: true,
        }),
      });
      showToast("Département créé", "success");
      setShowModal(false);
      setForm({ name: "", code: "", facility_id: "", description: "" });
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
            <Layers size={28} style={{ display: "inline", marginRight: 8, verticalAlign: "middle" }} />
            Départements
          </h1>
          <p className="muted">Unités fonctionnelles des établissements</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-secondary" onClick={load} title="Rafraîchir">
            <RefreshCw size={16} />
          </button>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> Nouveau département
          </button>
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

      <div className="card" style={{ padding: 0 }}>
        <table className="table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Code</th>
              {isSuperAdmin && <th>Établissement</th>}
              <th>Description</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={isSuperAdmin ? 5 : 4} style={{ textAlign: "center", padding: 24 }}>Chargement...</td></tr>
            ) : departments.length === 0 ? (
              <tr><td colSpan={isSuperAdmin ? 5 : 4} style={{ textAlign: "center", padding: 24 }}>Aucun département</td></tr>
            ) : (
              departments.map((d) => (
                <tr key={d.id}>
                  <td>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                      <Folder size={14} style={{ color: "#64748b" }} />
                      <strong>{d.name}</strong>
                    </span>
                  </td>
                  <td><code style={{ fontSize: 11 }}>{d.code}</code></td>
                  {isSuperAdmin && <td><Building2 size={12} style={{ display: "inline", marginRight: 4 }} />{facilityName(d.facility_id)}</td>}
                  <td style={{ color: "#64748b", fontSize: 12 }}>{d.description || "—"}</td>
                  <td>
                    <span className={`badge ${d.is_active ? "badge-green" : "badge-red"}`}>
                      {d.is_active ? "Actif" : "Inactif"}
                    </span>
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
              <h2>Nouveau département</h2>
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
              {isSuperAdmin && (
                <div className="form-group">
                  <label>Établissement *</label>
                  <select className="input" required value={form.facility_id}
                    onChange={(e) => setForm({ ...form, facility_id: e.target.value })}>
                    <option value="">— Choisir —</option>
                    {facilities.map((f) => (
                      <option key={f.id} value={f.id}>{f.name}</option>
                    ))}
                  </select>
                </div>
              )}
              <div className="form-group">
                <label>Description</label>
                <textarea className="input" rows={2} value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })} />
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
