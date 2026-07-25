import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { showToast } from "../components/Toast";
import { useAuth } from "../contexts/AuthContext";
import {
  Plus, Search, RefreshCw, X, Shield, Key, Lock, Check,
} from "lucide-react";

type Role = {
  code: string;
  name: string;
  description: string | null;
  is_system: boolean;
};

type Permission = {
  code: string;
  name: string;
  module: string;
  description: string | null;
};

type RolePermission = {
  id: string;
  role_code: string;
  permission_code: string;
};

export function RbacPage() {
  const { isSuperAdmin } = useAuth();
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [rolePerms, setRolePerms] = useState<RolePermission[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchPerm, setSearchPerm] = useState("");
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [showPermModal, setShowPermModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [roleForm, setRoleForm] = useState({ code: "", name: "", description: "" });
  const [permForm, setPermForm] = useState({ code: "", name: "", module: "", description: "" });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [rolesRes, permsRes] = await Promise.all([
        apiRequest<{ data: Role[] }>(`/rbac/roles?page_size=1000`),
        apiRequest<{ data: Permission[] }>(`/rbac/permissions?page_size=1000`),
      ]);
      setRoles(rolesRes.data || []);
      setPermissions(permsRes.data || []);
      if (!selectedRole && (rolesRes.data || []).length > 0) {
        setSelectedRole(rolesRes.data[0].code);
      }
    } catch (e: any) {
      showToast("Erreur de chargement: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  }, [selectedRole]);

  useEffect(() => {
    load();
  }, [load]);

  const filteredPermissions = permissions.filter(
    (p) =>
      !searchPerm ||
      p.name.toLowerCase().includes(searchPerm.toLowerCase()) ||
      p.code.toLowerCase().includes(searchPerm.toLowerCase()) ||
      p.module.toLowerCase().includes(searchPerm.toLowerCase())
  );

  const groupedPerms = filteredPermissions.reduce<Record<string, Permission[]>>((acc, p) => {
    if (!acc[p.module]) acc[p.module] = [];
    acc[p.module].push(p);
    return acc;
  }, {});

  const hasPermissionForRole = (permCode: string) =>
    rolePerms.some((rp) => rp.role_code === selectedRole && rp.permission_code === permCode);

  const togglePermission = async (permCode: string) => {
    if (!selectedRole) return;
    try {
      if (hasPermissionForRole(permCode)) {
        // Note: backend doesn't have a DELETE endpoint for role-permissions
        showToast("Désactivation non supportée par l'API (à venir)", "success");
      } else {
        await apiRequest("/rbac/role-permissions", {
          method: "POST",
          body: JSON.stringify({
            role_code: selectedRole,
            permission_code: permCode,
          }),
        });
        showToast("Permission assignée", "success");
        await load();
      }
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    }
  };

  const handleCreateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiRequest("/rbac/roles", {
        method: "POST",
        body: JSON.stringify(roleForm),
      });
      showToast("Rôle créé", "success");
      setShowRoleModal(false);
      setRoleForm({ code: "", name: "", description: "" });
      await load();
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreatePerm = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiRequest("/rbac/permissions", {
        method: "POST",
        body: JSON.stringify(permForm),
      });
      showToast("Permission créée", "success");
      setShowPermModal(false);
      setPermForm({ code: "", name: "", module: "", description: "" });
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
            <Shield size={28} style={{ display: "inline", marginRight: 8, verticalAlign: "middle" }} />
            Rôles & Permissions
          </h1>
          <p className="muted">Gestion du contrôle d'accès basé sur les rôles (RBAC)</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-secondary" onClick={load} title="Rafraîchir">
            <RefreshCw size={16} />
          </button>
          <button className="btn btn-secondary" onClick={() => setShowPermModal(true)}>
            <Plus size={16} /> Permission
          </button>
          <button className="btn btn-primary" onClick={() => setShowRoleModal(true)}>
            <Plus size={16} /> Nouveau rôle
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 16, marginTop: 16 }}>
        {/* Roles list */}
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: 12, borderBottom: "1px solid var(--border, #e2e8f0)" }}>
            <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>
              <Key size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }} />
              Rôles ({roles.length})
            </h3>
          </div>
          <div style={{ maxHeight: 600, overflowY: "auto" }}>
            {loading ? (
              <div style={{ padding: 16, textAlign: "center" }}>Chargement...</div>
            ) : (
              roles.map((r) => (
                <button
                  key={r.code}
                  onClick={() => setSelectedRole(r.code)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    padding: "10px 14px",
                    background: selectedRole === r.code ? "var(--primary-light, #eff6ff)" : "transparent",
                    border: "none",
                    borderBottom: "1px solid var(--border, #f1f5f9)",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{r.name}</div>
                  <div style={{ fontSize: 11, color: "#94a3b8" }}>{r.code}</div>
                  {r.is_system && (
                    <span className="badge badge-gray" style={{ fontSize: 9, marginTop: 4 }}>SYSTÈME</span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Permissions matrix */}
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: 12, borderBottom: "1px solid var(--border, #e2e8f0)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>
              <Lock size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }} />
              Permissions {selectedRole && `pour ${roles.find((r) => r.code === selectedRole)?.name || ""}`}
            </h3>
            <div style={{ position: "relative" }}>
              <Search size={14} style={{ position: "absolute", left: 8, top: 9, color: "#94a3b8" }} />
              <input
                className="input"
                placeholder="Rechercher..."
                value={searchPerm}
                onChange={(e) => setSearchPerm(e.target.value)}
                style={{ paddingLeft: 28, width: 200, height: 30 }}
              />
            </div>
          </div>
          <div style={{ maxHeight: 600, overflowY: "auto", padding: 12 }}>
            {!selectedRole ? (
              <div style={{ textAlign: "center", padding: 24, color: "#94a3b8" }}>
                Sélectionnez un rôle à gauche
              </div>
            ) : Object.keys(groupedPerms).length === 0 ? (
              <div style={{ textAlign: "center", padding: 24, color: "#94a3b8" }}>
                Aucune permission trouvée
              </div>
            ) : (
              Object.entries(groupedPerms).map(([module, perms]) => (
                <div key={module} style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", marginBottom: 6 }}>
                    {module}
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 8 }}>
                    {perms.map((p) => {
                      const has = hasPermissionForRole(p.code);
                      return (
                        <button
                          key={p.code}
                          onClick={() => togglePermission(p.code)}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                            padding: "8px 10px",
                            background: has ? "#dcfce7" : "#f8fafc",
                            border: `1px solid ${has ? "#86efac" : "#e2e8f0"}`,
                            borderRadius: 6,
                            cursor: "pointer",
                            textAlign: "left",
                          }}
                        >
                          <div style={{
                            width: 18, height: 18, borderRadius: 4,
                            background: has ? "#16a34a" : "#e2e8f0",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            color: "white", flexShrink: 0,
                          }}>
                            {has && <Check size={12} />}
                          </div>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 12, fontWeight: 600 }}>{p.name}</div>
                            <div style={{ fontSize: 10, color: "#94a3b8" }}>{p.code}</div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Role modal */}
      {showRoleModal && (
        <div className="modal-overlay" onClick={() => setShowRoleModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 450 }}>
            <div className="modal-header">
              <h2>Nouveau rôle</h2>
              <button className="btn-icon" onClick={() => setShowRoleModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleCreateRole} className="modal-body">
              <div className="form-group">
                <label>Code * (ex: AUDIT)</label>
                <input className="input" required value={roleForm.code}
                  onChange={(e) => setRoleForm({ ...roleForm, code: e.target.value.toUpperCase() })} />
              </div>
              <div className="form-group">
                <label>Nom *</label>
                <input className="input" required value={roleForm.name}
                  onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea className="input" rows={2} value={roleForm.description}
                  onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })} />
              </div>
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowRoleModal(false)}>Annuler</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>Créer</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Permission modal */}
      {showPermModal && (
        <div className="modal-overlay" onClick={() => setShowPermModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 450 }}>
            <div className="modal-header">
              <h2>Nouvelle permission</h2>
              <button className="btn-icon" onClick={() => setShowPermModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleCreatePerm} className="modal-body">
              <div className="form-group">
                <label>Code * (ex: audit.read)</label>
                <input className="input" required value={permForm.code}
                  onChange={(e) => setPermForm({ ...permForm, code: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Nom *</label>
                <input className="input" required value={permForm.name}
                  onChange={(e) => setPermForm({ ...permForm, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Module *</label>
                <input className="input" required value={permForm.module}
                  onChange={(e) => setPermForm({ ...permForm, module: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea className="input" rows={2} value={permForm.description}
                  onChange={(e) => setPermForm({ ...permForm, description: e.target.value })} />
              </div>
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowPermModal(false)}>Annuler</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>Créer</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
