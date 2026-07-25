import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { showToast } from "../components/Toast";
import { useAuth } from "../contexts/AuthContext";
import { useT } from "../i18n";
import {
  Search, RefreshCw, Filter, ChevronLeft, ChevronRight,
  Activity, Shield, AlertCircle,
} from "lucide-react";

type AuditLog = {
  id: string;
  created_at: string;
  user_id: string | null;
  facility_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  http_method: string | null;
  http_path: string | null;
  status_code: number | null;
  ip_address: string | null;
  user_agent: string | null;
  payload: any;
};

type PaginatedResponse = {
  data: AuditLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  "auth.login": { label: "Connexion", color: "#10b981" },
  "auth.login_failed": { label: "Échec connexion", color: "#ef4444" },
  "auth.login_inactive": { label: "Connexion inactif", color: "#f59e0b" },
  "auth.logout": { label: "Déconnexion", color: "#6b7280" },
  "patient.create": { label: "Patient créé", color: "#3b82f6" },
  "patient.update": { label: "Patient modifié", color: "#3b82f6" },
  "patient.delete": { label: "Patient supprimé", color: "#dc2626" },
  "user.create": { label: "Utilisateur créé", color: "#8b5cf6" },
  "user.update": { label: "Utilisateur modifié", color: "#8b5cf6" },
};

function getActionLabel(action: string): { label: string; color: string } {
  return ACTION_LABELS[action] || { label: action, color: "#6b7280" };
}

function formatDateTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function AuditPage() {
  const t = useT();
  const { isSuperAdmin, isAdmin } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [filters, setFilters] = useState({
    action: "",
    resource_type: "",
    resource_id: "",
    user_id: "",
  });
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (filters.action) params.set("action", filters.action);
      if (filters.resource_type) params.set("resource_type", filters.resource_type);
      if (filters.resource_id) params.set("resource_id", filters.resource_id);
      if (filters.user_id) params.set("user_id", filters.user_id);
      const res = await apiRequest<PaginatedResponse>(`/audit/logs?${params.toString()}`);
      setLogs(res.data || []);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (e: any) {
      showToast("Erreur de chargement: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    load();
  }, [load]);

  if (!isSuperAdmin && !isAdmin) {
    return (
      <div className="page-container">
        <div className="card" style={{ padding: "32px", textAlign: "center" }}>
          <AlertCircle size={48} style={{ color: "#ef4444", margin: "0 auto 16px" }} />
          <h2>{t("audit.access_denied")}</h2>
          <p className="muted">{t("audit.access_denied_desc")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ marginBottom: "24px" }}>
        <h1>
          <Shield size={28} style={{ verticalAlign: "middle", marginRight: "8px" }} />
          {t("nav.audit")}
        </h1>
        <p className="muted">
          {t("audit.description", { total })}
        </p>
      </div>

      {/* Filters */}
      <div className="card" style={{ padding: "16px", marginBottom: "16px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px" }}>
          <label className="form-control">
            <Filter size={14} style={{ verticalAlign: "middle" }} /> Action
            <select
              value={filters.action}
              onChange={(e) => { setFilters({ ...filters, action: e.target.value }); setPage(1); }}
            >
              <option value="">Toutes</option>
              <option value="auth.login">Connexion</option>
              <option value="auth.login_failed">Échec connexion</option>
              <option value="auth.login_inactive">Inactif</option>
              <option value="auth.logout">Déconnexion</option>
              <option value="patient.create">Patient créé</option>
              <option value="patient.update">Patient modifié</option>
              <option value="user.create">Utilisateur créé</option>
            </select>
          </label>
          <label className="form-control">
            Type ressource
            <input
              type="text"
              placeholder="patient, user, admission..."
              value={filters.resource_type}
              onChange={(e) => { setFilters({ ...filters, resource_type: e.target.value }); setPage(1); }}
            />
          </label>
          <label className="form-control">
            ID ressource
            <input
              type="text"
              placeholder="UUID"
              value={filters.resource_id}
              onChange={(e) => { setFilters({ ...filters, resource_id: e.target.value }); setPage(1); }}
            />
          </label>
          <label className="form-control">
            ID utilisateur
            <input
              type="text"
              placeholder="UUID"
              value={filters.user_id}
              onChange={(e) => { setFilters({ ...filters, user_id: e.target.value }); setPage(1); }}
            />
          </label>
          <button
            className="primary-button"
            onClick={load}
            style={{ alignSelf: "flex-end" }}
            disabled={loading}
          >
            <RefreshCw size={14} style={{ verticalAlign: "middle" }} /> {t("audit.button.refresh")}
          </button>
        </div>
      </div>

      {/* Logs table */}
      <div className="card" style={{ padding: "0", overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f1f5f9", textAlign: "left" }}>
              <th style={{ padding: "12px", fontSize: "12px", textTransform: "uppercase", color: "#64748b" }}>Date</th>
              <th style={{ padding: "12px", fontSize: "12px", textTransform: "uppercase", color: "#64748b" }}>Action</th>
              <th style={{ padding: "12px", fontSize: "12px", textTransform: "uppercase", color: "#64748b" }}>Ressource</th>
              <th style={{ padding: "12px", fontSize: "12px", textTransform: "uppercase", color: "#64748b" }}>Statut</th>
              <th style={{ padding: "12px", fontSize: "12px", textTransform: "uppercase", color: "#64748b" }}>IP</th>
              <th style={{ padding: "12px", fontSize: "12px", textTransform: "uppercase", color: "#64748b" }}>Méthode</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={6} style={{ padding: "32px", textAlign: "center", color: "#94a3b8" }}>
                <Activity size={20} style={{ animation: "spin 1s linear infinite", display: "inline-block" }} /> {t("label.loading")}
              </td></tr>
            )}
            {!loading && logs.length === 0 && (
              <tr><td colSpan={6} style={{ padding: "32px", textAlign: "center", color: "#94a3b8" }}>
                {t("audit.empty")}
              </td></tr>
            )}
            {!loading && logs.map((log) => {
              const actionInfo = getActionLabel(log.action);
              return (
                <tr
                  key={log.id}
                  onClick={() => setSelectedLog(log)}
                  style={{ borderBottom: "1px solid #e2e8f0", cursor: "pointer" }}
                  onMouseEnter={(e) => e.currentTarget.style.background = "#f8fafc"}
                  onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                >
                  <td style={{ padding: "12px", fontSize: "13px", fontFamily: "monospace" }}>
                    {formatDateTime(log.created_at)}
                  </td>
                  <td style={{ padding: "12px" }}>
                    <span style={{
                      padding: "4px 8px",
                      borderRadius: "4px",
                      background: `${actionInfo.color}20`,
                      color: actionInfo.color,
                      fontSize: "12px",
                      fontWeight: 500,
                    }}>
                      {actionInfo.label}
                    </span>
                  </td>
                  <td style={{ padding: "12px", fontSize: "13px" }}>
                    {log.resource_type ? `${log.resource_type}/${log.resource_id?.substring(0, 8) || ""}…` : "—"}
                  </td>
                  <td style={{ padding: "12px" }}>
                    {log.status_code && (
                      <span style={{
                        fontFamily: "monospace",
                        color: log.status_code < 300 ? "#10b981" : log.status_code < 500 ? "#f59e0b" : "#ef4444",
                        fontWeight: 600,
                      }}>
                        {log.status_code}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: "12px", fontSize: "12px", fontFamily: "monospace", color: "#64748b" }}>
                    {log.ip_address || "—"}
                  </td>
                  <td style={{ padding: "12px", fontSize: "12px", fontFamily: "monospace" }}>
                    {log.http_method || "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid #e2e8f0" }}>
            <span style={{ fontSize: "13px", color: "#64748b" }}>
              Page {page} / {totalPages}
            </span>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                className="secondary-button"
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1 || loading}
                style={{ padding: "6px 12px", fontSize: "13px" }}
              >
                <ChevronLeft size={14} /> {t("action.previous")}
              </button>
              <button
                className="secondary-button"
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages || loading}
                style={{ padding: "6px 12px", fontSize: "13px" }}
              >
                {t("action.next")} <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail modal */}
      {selectedLog && (
        <div
          onClick={() => setSelectedLog(null)}
          style={{
            position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
            background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="card"
            style={{ maxWidth: "700px", width: "90%", maxHeight: "80vh", overflow: "auto", padding: "24px" }}
          >
            <h2 style={{ marginBottom: "16px" }}>{t("audit.detail.title")}</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "13px" }}>
              <div><strong>ID :</strong> <code>{selectedLog.id}</code></div>
              <div><strong>Date :</strong> {formatDateTime(selectedLog.created_at)}</div>
              <div><strong>Action :</strong> {getActionLabel(selectedLog.action).label}</div>
              <div><strong>Statut :</strong> {selectedLog.status_code || "—"}</div>
              <div><strong>User ID :</strong> <code>{selectedLog.user_id || "—"}</code></div>
              <div><strong>Facility ID :</strong> <code>{selectedLog.facility_id || "—"}</code></div>
              <div><strong>Ressource :</strong> {selectedLog.resource_type || "—"}/{selectedLog.resource_id || "—"}</div>
              <div><strong>HTTP :</strong> {selectedLog.http_method} {selectedLog.http_path}</div>
              <div><strong>IP :</strong> {selectedLog.ip_address || "—"}</div>
              <div><strong>User-Agent :</strong> <span style={{ fontSize: "11px" }}>{selectedLog.user_agent || "—"}</span></div>
            </div>
            {selectedLog.payload && (
              <div style={{ marginTop: "16px" }}>
                <strong>Payload :</strong>
                <pre style={{
                  background: "#f1f5f9",
                  padding: "12px",
                  borderRadius: "4px",
                  fontSize: "12px",
                  overflow: "auto",
                  marginTop: "8px",
                }}>
                  {JSON.stringify(selectedLog.payload, null, 2)}
                </pre>
              </div>
            )}
            <button
              className="secondary-button"
              onClick={() => setSelectedLog(null)}
              style={{ marginTop: "16px" }}
            >
              {t("action.close")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
