import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { showToast } from "../components/Toast";
import { useAuth } from "../contexts/AuthContext";
import {
  RefreshCw, Bell, BellOff, CheckCheck, Trash2, ChevronLeft, ChevronRight,
  AlertCircle, Filter, Mail, MessageSquare, Inbox,
} from "lucide-react";

type Notification = {
  id: string;
  created_at: string | null;
  recipient_id: string;
  sender_id: string | null;
  category: string;
  priority: "low" | "normal" | "high" | "urgent";
  title: string;
  body: string | null;
  action_url: string | null;
  channels: string[];
  in_app_delivered: boolean;
  email_delivered: boolean;
  sms_delivered: boolean;
  delivery_error: string | null;
  read_at: string | null;
  dismissed_at: string | null;
  resource_type: string | null;
  resource_id: string | null;
  is_read: boolean;
};

type PaginatedResponse = {
  data: Notification[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  unread_count: number;
};

const CATEGORY_LABELS: Record<string, { label: string; color: string; icon: typeof Bell }> = {
  system: { label: "Système", color: "#6b7280", icon: Bell },
  lab_result: { label: "Résultat labo", color: "#3b82f6", icon: Mail },
  appointment: { label: "Rendez-vous", color: "#10b981", icon: Bell },
  pharmacy: { label: "Pharmacie", color: "#f59e0b", icon: Bell },
  billing: { label: "Facturation", color: "#8b5cf6", icon: Bell },
  emergency: { label: "Urgence", color: "#ef4444", icon: AlertCircle },
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "#94a3b8",
  normal: "#3b82f6",
  high: "#f59e0b",
  urgent: "#ef4444",
};

function getCategoryMeta(category: string) {
  return CATEGORY_LABELS[category] || { label: category, color: "#6b7280", icon: Bell };
}

function formatRelative(iso: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    const diffH = Math.floor(diffMin / 60);
    const diffD = Math.floor(diffH / 24);
    if (diffMin < 1) return "à l'instant";
    if (diffMin < 60) return `il y a ${diffMin} min`;
    if (diffH < 24) return `il y a ${diffH} h`;
    if (diffD < 7) return `il y a ${diffD} j`;
    return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch {
    return iso;
  }
}

export function NotificationsPage() {
  const { isSuperAdmin, isAdmin } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [filterCategory, setFilterCategory] = useState("");
  const [unreadOnly, setUnreadOnly] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (filterCategory) params.set("category", filterCategory);
      if (unreadOnly) params.set("unread_only", "true");
      const res = await apiRequest<PaginatedResponse>(`/notifications?${params.toString()}`);
      setNotifications(res.data || []);
      setTotal(res.total);
      setTotalPages(res.total_pages);
      setUnreadCount(res.unread_count);
    } catch (e: any) {
      showToast("Erreur de chargement: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filterCategory, unreadOnly]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleMarkRead(id: string) {
    try {
      await apiRequest(`/notifications/${id}/read`, { method: "PATCH" });
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    }
  }

  async function handleMarkAllRead() {
    try {
      await apiRequest(`/notifications/mark-all-read`, { method: "POST" });
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, is_read: true, read_at: n.read_at || new Date().toISOString() }))
      );
      setUnreadCount(0);
      showToast("Toutes les notifications marquées comme lues", "success");
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    }
  }

  async function handleDismiss(id: string) {
    try {
      await apiRequest(`/notifications/${id}`, { method: "DELETE" });
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setTotal((t) => Math.max(0, t - 1));
      showToast("Notification supprimée", "success");
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    }
  }

  // Notifications page is visible to all authenticated users — it's their inbox.
  // (No role gate here; route protection is handled in App.tsx via auth-only check.)
  const canSend = isSuperAdmin || isAdmin;

  return (
    <div className="page-container">
      <div className="page-header" style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1>
            <Bell size={28} style={{ verticalAlign: "middle", marginRight: "8px" }} />
            Notifications
          </h1>
          <p className="muted">
            {unreadCount > 0
              ? `${unreadCount} notification${unreadCount > 1 ? "s" : ""} non lue${unreadCount > 1 ? "s" : ""} sur ${total}`
              : `${total} notification${total > 1 ? "s" : ""} — tout est lu`}
          </p>
        </div>
        {unreadCount > 0 && (
          <button
            className="primary-button"
            onClick={handleMarkAllRead}
            disabled={loading}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <CheckCheck size={14} /> Tout marquer comme lu
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="card" style={{ padding: "16px", marginBottom: "16px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px", alignItems: "flex-end" }}>
          <label className="form-control">
            <Filter size={14} style={{ verticalAlign: "middle" }} /> Catégorie
            <select
              value={filterCategory}
              onChange={(e) => { setFilterCategory(e.target.value); setPage(1); }}
            >
              <option value="">Toutes</option>
              <option value="system">Système</option>
              <option value="lab_result">Résultat labo</option>
              <option value="appointment">Rendez-vous</option>
              <option value="pharmacy">Pharmacie</option>
              <option value="billing">Facturation</option>
              <option value="emergency">Urgence</option>
            </select>
          </label>
          <label className="form-control" style={{ display: "flex", alignItems: "center", gap: "6px", flexDirection: "row" }}>
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => { setUnreadOnly(e.target.checked); setPage(1); }}
            />
            Non lues seulement
          </label>
          <button
            className="primary-button"
            onClick={load}
            disabled={loading}
            style={{ alignSelf: "flex-end" }}
          >
            <RefreshCw size={14} style={{ verticalAlign: "middle" }} /> Actualiser
          </button>
        </div>
      </div>

      {/* Notifications list */}
      <div className="card" style={{ padding: "0", overflow: "hidden" }}>
        {loading && (
          <div style={{ padding: "32px", textAlign: "center", color: "#94a3b8" }}>
            <RefreshCw size={20} style={{ animation: "spin 1s linear infinite", display: "inline-block" }} /> Chargement…
          </div>
        )}
        {!loading && notifications.length === 0 && (
          <div style={{ padding: "48px 32px", textAlign: "center", color: "#94a3b8" }}>
            <Inbox size={48} style={{ margin: "0 auto 12px", opacity: 0.5 }} />
            <div style={{ fontSize: "16px", marginBottom: "4px" }}>Aucune notification</div>
            <div style={{ fontSize: "13px" }}>Les nouvelles notifications apparaîtront ici.</div>
          </div>
        )}
        {!loading && notifications.map((n) => {
          const meta = getCategoryMeta(n.category);
          const Icon = meta.icon;
          return (
            <div
              key={n.id}
              style={{
                padding: "16px 20px",
                borderBottom: "1px solid #e2e8f0",
                background: n.is_read ? "transparent" : "#f0f9ff",
                display: "flex",
                gap: "16px",
                alignItems: "flex-start",
              }}
            >
              <div
                style={{
                  flexShrink: 0,
                  width: "40px",
                  height: "40px",
                  borderRadius: "50%",
                  background: `${meta.color}20`,
                  color: meta.color,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Icon size={20} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                  <strong style={{ color: n.is_read ? "#475569" : "#0f172a" }}>{n.title}</strong>
                  {!n.is_read && (
                    <span
                      style={{
                        background: "#3b82f6",
                        color: "white",
                        fontSize: "10px",
                        padding: "2px 6px",
                        borderRadius: "8px",
                        fontWeight: 600,
                      }}
                    >
                      NEW
                    </span>
                  )}
                  <span
                    style={{
                      background: `${PRIORITY_COLORS[n.priority]}20`,
                      color: PRIORITY_COLORS[n.priority],
                      fontSize: "10px",
                      padding: "2px 6px",
                      borderRadius: "8px",
                      fontWeight: 600,
                      textTransform: "uppercase",
                    }}
                  >
                    {n.priority}
                  </span>
                </div>
                {n.body && (
                  <p style={{ margin: "0 0 6px", color: "#475569", fontSize: "13px", whiteSpace: "pre-wrap" }}>
                    {n.body}
                  </p>
                )}
                <div style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "11px", color: "#94a3b8" }}>
                  <span>{formatRelative(n.created_at)}</span>
                  <span style={{ color: meta.color, fontWeight: 500 }}>{meta.label}</span>
                  {n.channels.includes("email") && (
                    <span title="Email" style={{ display: "inline-flex", alignItems: "center", gap: "2px" }}>
                      <Mail size={11} /> {n.email_delivered ? "envoyé" : "échec"}
                    </span>
                  )}
                  {n.channels.includes("sms") && (
                    <span title="SMS" style={{ display: "inline-flex", alignItems: "center", gap: "2px" }}>
                      <MessageSquare size={11} /> {n.sms_delivered ? "envoyé" : "échec"}
                    </span>
                  )}
                  {n.delivery_error && (
                    <span title={n.delivery_error} style={{ color: "#ef4444" }}>
                      ⚠ Erreur de livraison
                    </span>
                  )}
                  {n.action_url && (
                    <a
                      href={n.action_url}
                      style={{ color: "#3b82f6", textDecoration: "none" }}
                      onClick={(e) => {
                        // Use React Router navigation if it's an internal link
                        if (n.action_url?.startsWith("/")) {
                          e.preventDefault();
                          window.location.href = n.action_url!;
                        }
                      }}
                    >
                      Voir →
                    </a>
                  )}
                </div>
              </div>
              <div style={{ display: "flex", gap: "4px", flexShrink: 0 }}>
                {!n.is_read && (
                  <button
                    title="Marquer comme lu"
                    onClick={() => handleMarkRead(n.id)}
                    style={{
                      background: "transparent",
                      border: "1px solid #e2e8f0",
                      borderRadius: "4px",
                      padding: "4px",
                      cursor: "pointer",
                      color: "#3b82f6",
                    }}
                  >
                    <CheckCheck size={14} />
                  </button>
                )}
                <button
                  title="Supprimer"
                  onClick={() => handleDismiss(n.id)}
                  style={{
                    background: "transparent",
                    border: "1px solid #e2e8f0",
                    borderRadius: "4px",
                    padding: "4px",
                    cursor: "pointer",
                    color: "#ef4444",
                  }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "12px", marginTop: "16px" }}>
          <button
            className="secondary-button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
            style={{ display: "flex", alignItems: "center", gap: "4px" }}
          >
            <ChevronLeft size={14} /> Précédent
          </button>
          <span className="muted">Page {page} / {totalPages}</span>
          <button
            className="secondary-button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages || loading}
            style={{ display: "flex", alignItems: "center", gap: "4px" }}
          >
            Suivant <ChevronRight size={14} />
          </button>
        </div>
      )}

      {/* Admin hint */}
      {canSend && (
        <div className="card" style={{ padding: "12px 16px", marginTop: "16px", background: "#f8fafc", fontSize: "13px", color: "#64748b" }}>
          <BellOff size={14} style={{ verticalAlign: "middle", marginRight: "6px" }} />
          Astuce admin : pour envoyer une notification à un utilisateur spécifique, utilisez l'endpoint <code>POST /api/v1/notifications/send</code> avec la permission <code>notification.send</code>.
        </div>
      )}
    </div>
  );
}
