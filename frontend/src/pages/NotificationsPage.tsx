import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { showToast } from "../components/Toast";
import { useAuth } from "../contexts/AuthContext";
import { useT } from "../i18n";
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

const CATEGORY_ICONS: Record<string, { color: string; icon: typeof Bell }> = {
  system: { color: "#6b7280", icon: Bell },
  lab_result: { color: "#3b82f6", icon: Mail },
  appointment: { color: "#10b981", icon: Bell },
  pharmacy: { color: "#f59e0b", icon: Bell },
  billing: { color: "#8b5cf6", icon: Bell },
  emergency: { color: "#ef4444", icon: AlertCircle },
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "#94a3b8",
  normal: "#3b82f6",
  high: "#f59e0b",
  urgent: "#ef4444",
};

export function NotificationsPage() {
  const t = useT();
  const { isSuperAdmin, isAdmin } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState("");
  const [unreadOnly, setUnreadOnly] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (filterCategory) params.set("category", filterCategory);
      if (unreadOnly) params.set("unread_only", "true");
      const resp = await apiRequest<PaginatedResponse>(`/notifications?${params}`);
      setNotifications(resp.data || []);
      setTotal(resp.total || 0);
      setUnreadCount(resp.unread_count || 0);
      setTotalPages(resp.total_pages || 1);
    } catch (e: any) {
      showToast(t("notif.error_toast", { message: e.message || "" }), "error");
    } finally {
      setLoading(false);
    }
  }, [page, filterCategory, unreadOnly, t]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleMarkRead(id: string) {
    try {
      await apiRequest(`/notifications/${id}/read`, { method: "PATCH" });
      setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n));
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (e: any) {
      showToast(t("notif.error_toast", { message: e.message || "" }), "error");
    }
  }

  async function handleMarkAllRead() {
    try {
      await apiRequest("/notifications/mark-all-read", { method: "POST" });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true, read_at: new Date().toISOString() })));
      setUnreadCount(0);
      showToast(t("notif.marked_read_toast"), "success");
    } catch (e: any) {
      showToast(t("notif.error_toast", { message: e.message || "" }), "error");
    }
  }

  async function handleDismiss(id: string) {
    try {
      await apiRequest(`/notifications/${id}`, { method: "DELETE" });
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setTotal((tt) => Math.max(0, tt - 1));
      showToast(t("notif.deleted_toast"), "success");
    } catch (e: any) {
      showToast(t("notif.error_toast", { message: e.message || "" }), "error");
    }
  }

  function getCategoryMeta(category: string) {
    return CATEGORY_ICONS[category] || { color: "#6b7280", icon: Bell };
  }

  function getCategoryLabel(category: string): string {
    const key = `notif.cat.${category}`;
    const val = t(key);
    return val === key ? category : val;
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
      if (diffMin < 1) return t("notif.time.now");
      if (diffMin < 60) return t("notif.time.min_ago", { count: diffMin });
      if (diffH < 24) return t("notif.time.h_ago", { count: diffH });
      if (diffD < 7) return t("notif.time.d_ago", { count: diffD });
      return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" });
    } catch {
      return iso;
    }
  }

  const canSend = isSuperAdmin || isAdmin;

  return (
    <div className="page-container">
      <div className="page-header" style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1>
            <Bell size={28} style={{ verticalAlign: "middle", marginRight: "8px" }} />
            {t("notif.title")}
          </h1>
          <p className="muted">
            {unreadCount > 0
              ? t("notif.unread_count", { count: unreadCount, total })
              : t("notif.all_read", { total })}
          </p>
        </div>
        {unreadCount > 0 && (
          <button
            className="primary-button"
            onClick={handleMarkAllRead}
            disabled={loading}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <CheckCheck size={14} /> {t("notif.mark_all_read")}
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="card" style={{ padding: "16px", marginBottom: "16px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px", alignItems: "flex-end" }}>
          <label className="form-control">
            <Filter size={14} style={{ verticalAlign: "middle" }} /> {t("notif.category")}
            <select value={filterCategory} onChange={(e) => { setFilterCategory(e.target.value); setPage(1); }}>
              <option value="">{t("notif.all_categories")}</option>
              <option value="system">{t("notif.cat.system")}</option>
              <option value="lab_result">{t("notif.cat.lab_result")}</option>
              <option value="appointment">{t("notif.cat.appointment")}</option>
              <option value="pharmacy">{t("notif.cat.pharmacy")}</option>
              <option value="billing">{t("notif.cat.billing")}</option>
              <option value="emergency">{t("notif.cat.emergency")}</option>
            </select>
          </label>
          <label className="form-control" style={{ display: "flex", alignItems: "center", gap: "6px", flexDirection: "row" }}>
            <input type="checkbox" checked={unreadOnly} onChange={(e) => { setUnreadOnly(e.target.checked); setPage(1); }} />
            {t("notif.unread_only")}
          </label>
          <button className="primary-button" onClick={load} disabled={loading} style={{ alignSelf: "flex-end" }}>
            <RefreshCw size={14} style={{ verticalAlign: "middle" }} /> {t("notif.refresh")}
          </button>
        </div>
      </div>

      {/* Notifications list */}
      <div className="card" style={{ padding: "0", overflow: "hidden" }}>
        {loading && (
          <div style={{ padding: "32px", textAlign: "center", color: "#94a3b8" }}>
            <RefreshCw size={20} style={{ animation: "spin 1s linear infinite", display: "inline-block" }} /> {t("notif.loading")}
          </div>
        )}
        {!loading && notifications.length === 0 && (
          <div style={{ padding: "48px 32px", textAlign: "center", color: "#94a3b8" }}>
            <Inbox size={48} style={{ margin: "0 auto 12px", opacity: 0.5 }} />
            <div style={{ fontSize: "16px", marginBottom: "4px" }}>{t("notif.empty_title")}</div>
            <div style={{ fontSize: "13px" }}>{t("notif.empty_desc")}</div>
          </div>
        )}
        {!loading && notifications.map((n) => {
          const meta = getCategoryMeta(n.category);
          const Icon = meta.icon;
          return (
            <div key={n.id} style={{ padding: "16px 20px", borderBottom: "1px solid #e2e8f0", background: n.is_read ? "transparent" : "#f0f9ff", display: "flex", gap: "16px", alignItems: "flex-start" }}>
              <div style={{ flexShrink: 0, width: "40px", height: "40px", borderRadius: "50%", background: `${meta.color}20`, color: meta.color, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Icon size={20} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                  <strong style={{ color: n.is_read ? "#475569" : "#0f172a" }}>{n.title}</strong>
                  {!n.is_read && (
                    <span style={{ background: "#3b82f6", color: "white", fontSize: "10px", padding: "2px 6px", borderRadius: "8px", fontWeight: 600 }}>
                      {t("notif.new_badge")}
                    </span>
                  )}
                  <span style={{ background: `${PRIORITY_COLORS[n.priority]}20`, color: PRIORITY_COLORS[n.priority], fontSize: "10px", padding: "2px 6px", borderRadius: "8px", fontWeight: 600, textTransform: "uppercase" }}>
                    {n.priority}
                  </span>
                </div>
                {n.body && (
                  <p style={{ margin: "0 0 6px", color: "#475569", fontSize: "13px", whiteSpace: "pre-wrap" }}>{n.body}</p>
                )}
                <div style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "11px", color: "#94a3b8" }}>
                  <span>{formatRelative(n.created_at)}</span>
                  <span style={{ color: meta.color, fontWeight: 500 }}>{getCategoryLabel(n.category)}</span>
                  {n.channels.includes("email") && (
                    <span title="Email" style={{ display: "inline-flex", alignItems: "center", gap: "2px" }}>
                      <Mail size={11} /> {n.email_delivered ? t("notif.sent") : t("notif.failed")}
                    </span>
                  )}
                  {n.channels.includes("sms") && (
                    <span title="SMS" style={{ display: "inline-flex", alignItems: "center", gap: "2px" }}>
                      <MessageSquare size={11} /> {n.sms_delivered ? t("notif.sent") : t("notif.failed")}
                    </span>
                  )}
                  {n.delivery_error && (
                    <span title={n.delivery_error} style={{ color: "#ef4444" }}>{t("notif.delivery_error")}</span>
                  )}
                  {n.action_url && (
                    <a href={n.action_url} style={{ color: "#3b82f6", textDecoration: "none" }} onClick={(e) => { if (n.action_url?.startsWith("/")) { e.preventDefault(); window.location.href = n.action_url!; } }}>
                      {t("notif.view")}
                    </a>
                  )}
                </div>
              </div>
              <div style={{ display: "flex", gap: "4px", flexShrink: 0 }}>
                {!n.is_read && (
                  <button title={t("notif.mark_read")} onClick={() => handleMarkRead(n.id)} style={{ background: "transparent", border: "1px solid #e2e8f0", borderRadius: "4px", padding: "4px", cursor: "pointer", color: "#3b82f6" }}>
                    <CheckCheck size={14} />
                  </button>
                )}
                <button title={t("notif.delete")} onClick={() => handleDismiss(n.id)} style={{ background: "transparent", border: "1px solid #e2e8f0", borderRadius: "4px", padding: "4px", cursor: "pointer", color: "#ef4444" }}>
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
          <button className="secondary-button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1 || loading} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <ChevronLeft size={14} /> {t("notif.previous")}
          </button>
          <span className="muted">{t("notif.page_of", { page, total: totalPages })}</span>
          <button className="secondary-button" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages || loading} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            {t("notif.next")} <ChevronRight size={14} />
          </button>
        </div>
      )}

      {/* Admin hint */}
      {canSend && (
        <div className="card" style={{ padding: "12px 16px", marginTop: "16px", background: "#f8fafc", fontSize: "13px", color: "#64748b" }}>
          <BellOff size={14} style={{ verticalAlign: "middle", marginRight: "6px" }} />
          {t("notif.admin_hint")}
        </div>
      )}
    </div>
  );
}
