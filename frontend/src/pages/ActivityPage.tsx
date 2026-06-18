import { useCallback, useEffect, useMemo, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import {
  Activity,
  Plus,
  Search,
  Filter,
  Clock,
  User,
  ArrowUpCircle,
  LogIn,
  LogOut,
  Trash2,
  RefreshCw,
  BarChart3,
  Users,
  ChevronDown,
  X,
  Eye,
  Zap,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════
   Types & Constants
   ═══════════════════════════════════════════════════════════════════ */

type ActionType = "ALL" | "CREATE" | "UPDATE" | "DELETE" | "LOGIN" | "LOGOUT";
type ModuleType =
  | "ALL"
  | "PATIENTS"
  | "ADMISSIONS"
  | "EMERGENCY"
  | "PHARMACY"
  | "LAB"
  | "BILLING"
  | "HOSPITALIZATION"
  | "MATERNITY"
  | "PERSONNEL"
  | "IMAGING"
  | "SURGERY"
  | "QUALITY"
  | "REPORTING"
  | "AUTH";

const ACTION_OPTIONS: { value: ActionType; label: string; icon: React.ReactNode }[] = [
  { value: "ALL", label: "Toutes actions", icon: <Filter size={14} /> },
  { value: "CREATE", label: "Création", icon: <Plus size={14} /> },
  { value: "UPDATE", label: "Modification", icon: <ArrowUpCircle size={14} /> },
  { value: "DELETE", label: "Suppression", icon: <Trash2 size={14} /> },
  { value: "LOGIN", label: "Connexion", icon: <LogIn size={14} /> },
  { value: "LOGOUT", label: "Déconnexion", icon: <LogOut size={14} /> },
];

const MODULE_OPTIONS: { value: ModuleType; label: string }[] = [
  { value: "ALL", label: "Tous les modules" },
  { value: "PATIENTS", label: "Patients" },
  { value: "ADMISSIONS", label: "Admissions" },
  { value: "EMERGENCY", label: "Urgences" },
  { value: "PHARMACY", label: "Pharmacie" },
  { value: "LAB", label: "Laboratoire" },
  { value: "BILLING", label: "Facturation" },
  { value: "HOSPITALIZATION", label: "Hospitalisation" },
  { value: "MATERNITY", label: "Maternité" },
  { value: "PERSONNEL", label: "Personnel" },
  { value: "IMAGING", label: "Imagerie" },
  { value: "SURGERY", label: "Chirurgie" },
  { value: "QUALITY", label: "Qualité" },
  { value: "REPORTING", label: "Reporting" },
  { value: "AUTH", label: "Authentification" },
];

const ACTION_COLORS: Record<string, { dot: string; bg: string; text: string; border: string }> = {
  CREATE: { dot: "#16a34a", bg: "#f0fdf4", text: "#047857", border: "#86efac" },
  UPDATE: { dot: "#2563eb", bg: "#eff6ff", text: "#1d4ed8", border: "#93c5fd" },
  DELETE: { dot: "#dc2626", bg: "#fef2f2", text: "#b91c1c", border: "#fca5a5" },
  LOGIN: { dot: "#7c3aed", bg: "#f5f3ff", text: "#6d28d9", border: "#c4b5fd" },
  LOGOUT: { dot: "#6b7280", bg: "#f9fafb", text: "#4b5563", border: "#d1d5db" },
};

/* Map action_name prefixes to action types */
function inferActionType(actionName: string): string {
  const lower = actionName.toLowerCase();
  if (lower.includes("created") || lower.includes(".create") || lower.includes("admitted"))
    return "CREATE";
  if (lower.includes("deleted") || lower.includes(".delete") || lower.includes("removed"))
    return "DELETE";
  if (lower.includes("login") || lower.includes("logged_in") || lower.includes("authenticated"))
    return "LOGIN";
  if (lower.includes("logout") || lower.includes("logged_out"))
    return "LOGOUT";
  return "UPDATE";
}

/* Map entity_type to module */
function inferModule(entityType: string | null): string {
  if (!entityType) return "AUTH";
  const lower = entityType.toLowerCase();
  if (lower.includes("patient")) return "PATIENTS";
  if (lower.includes("admission")) return "ADMISSIONS";
  if (lower.includes("emergency")) return "EMERGENCY";
  if (lower.includes("product") || lower.includes("dispensation") || lower.includes("pharmacy"))
    return "PHARMACY";
  if (lower.includes("lab") || lower.includes("order") || lower.includes("result"))
    return "LAB";
  if (lower.includes("invoice") || lower.includes("billing") || lower.includes("payment"))
    return "BILLING";
  if (lower.includes("stay") || lower.includes("bed") || lower.includes("room") || lower.includes("hospital"))
    return "HOSPITALIZATION";
  if (lower.includes("maternity") || lower.includes("delivery"))
    return "MATERNITY";
  if (lower.includes("staff") || lower.includes("personnel"))
    return "PERSONNEL";
  if (lower.includes("imaging") || lower.includes("radiology"))
    return "IMAGING";
  if (lower.includes("surgery") || lower.includes("operation"))
    return "SURGERY";
  if (lower.includes("quality") || lower.includes("audit"))
    return "QUALITY";
  if (lower.includes("report"))
    return "REPORTING";
  return "AUTH";
}

function formatActionLabel(actionName: string): string {
  const parts = actionName.split(".");
  const action = parts[parts.length - 1] || actionName;
  const map: Record<string, string> = {
    created: "Création",
    updated: "Modification",
    deleted: "Suppression",
    closed: "Clôture",
    admitted: "Admission",
    discharged: "Sortie",
    login: "Connexion",
    logged_in: "Connexion",
    logout: "Déconnexion",
    logged_out: "Déconnexion",
    authenticated: "Authentification",
    validated: "Validation",
    cancelled: "Annulation",
    submitted: "Soumission",
    dispensed: "Dispensation",
    ordered: "Commande",
    completed: "Achèvement",
  };
  return map[action.toLowerCase()] || actionName;
}

function formatEntityLabel(entityType: string | null): string {
  if (!entityType) return "—";
  const map: Record<string, string> = {
    patient: "Patient",
    admission: "Admission",
    emergency_visit: "Visite urgence",
    product: "Produit",
    dispensation: "Dispensation",
    lab_order: "Demande labo",
    lab_result: "Résultat labo",
    invoice: "Facture",
    payment: "Paiement",
    hospital_stay: "Séjour",
    bed: "Lit",
    room: "Chambre",
    maternity_record: "Dossier maternité",
    delivery: "Accouchement",
    staff: "Personnel",
    imaging_order: "Demande imagerie",
    surgery: "Chirurgie",
    user: "Utilisateur",
  };
  return map[entityType.toLowerCase()] || entityType;
}

/* ═══════════════════════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════════════════════ */

export function ActivityPage({ lookups }: { lookups: LookupData }) {
  const [entries, setEntries] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState<ActionType>("ALL");
  const [moduleFilter, setModuleFilter] = useState<ModuleType>("ALL");
  const [userFilter, setUserFilter] = useState("");
  const [searchText, setSearchText] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [visibleCount, setVisibleCount] = useState(25);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadEntries = useCallback(async () => {
    setLoading(true);
    try {
      const payload = await apiRequest<any>("/activity?page_size=1000");
      const data: Row[] = Array.isArray(payload.data) ? payload.data : [];
      setEntries(data);
    } catch {
      /* silent */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEntries();
  }, [loadEntries, refreshKey]);

  useEffect(() => {
    const handler = () => setRefreshKey((k) => k + 1);
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      setRefreshKey((k) => k + 1);
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  /* ── Resolve user name ─────────────────────────── */
  function getUserName(actorId: string | null): string {
    if (!actorId) return "Système";
    const staff = lookups.staff.find((s) => s.id === actorId);
    if (staff)
      return `${staff.first_name || ""} ${staff.last_name || ""}`.trim() ||
        staff.email ||
        actorId;
    return actorId;
  }

  type EnrichedEntry = Row & { _actionType: string; _module: string };

  /* ── Enrich entries with inferred types ────────── */
  const enrichedEntries = useMemo((): EnrichedEntry[] => {
    return entries.map((e): EnrichedEntry => ({
      ...e,
      _actionType: inferActionType(e.action_name || ""),
      _module: inferModule(e.entity_type),
    }));
  }, [entries]);

  /* ── Apply filters ─────────────────────────────── */
  const filtered = useMemo(() => {
    let rows = enrichedEntries;

    if (actionFilter !== "ALL") {
      rows = rows.filter((r) => r._actionType === actionFilter);
    }
    if (moduleFilter !== "ALL") {
      rows = rows.filter((r) => r._module === moduleFilter);
    }
    if (userFilter) {
      rows = rows.filter((r) => r.actor_id === userFilter);
    }
    if (searchText.trim()) {
      const q = searchText.toLowerCase();
      rows = rows.filter(
        (r) =>
          (r.action_name || "").toLowerCase().includes(q) ||
          (r.entity_type || "").toLowerCase().includes(q) ||
          (r.notes || "").toLowerCase().includes(q) ||
          getUserName(r.actor_id).toLowerCase().includes(q)
      );
    }
    if (dateFrom) {
      rows = rows.filter(
        (r) => r.created_at && new Date(r.created_at) >= new Date(dateFrom)
      );
    }
    if (dateTo) {
      const to = new Date(dateTo);
      to.setHours(23, 59, 59, 999);
      rows = rows.filter(
        (r) => r.created_at && new Date(r.created_at) <= to
      );
    }
    return rows;
  }, [enrichedEntries, actionFilter, moduleFilter, userFilter, searchText, dateFrom, dateTo]);

  const visibleEntries = filtered.slice(0, visibleCount);
  const hasMore = visibleCount < filtered.length;

  /* ── Summary stats ─────────────────────────────── */
  const todayStr = new Date().toDateString();
  const todayEntries = enrichedEntries.filter(
    (e) => e.created_at && new Date(e.created_at).toDateString() === todayStr
  );

  const topUsersToday = useMemo(() => {
    const countMap: Record<string, number> = {};
    todayEntries.forEach((e) => {
      const name = getUserName(e.actor_id);
      countMap[name] = (countMap[name] || 0) + 1;
    });
    return Object.entries(countMap)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);
  }, [todayEntries]);

  const moduleCounts = useMemo(() => {
    const countMap: Record<string, number> = {};
    todayEntries.forEach((e) => {
      const mod = e._module;
      countMap[mod] = (countMap[mod] || 0) + 1;
    });
    return Object.entries(countMap).sort(([, a], [, b]) => b - a);
  }, [todayEntries]);

  const maxModuleCount = Math.max(...moduleCounts.map(([, c]) => c), 1);

  const moduleLabelMap: Record<string, string> = {
    PATIENTS: "Patients",
    ADMISSIONS: "Admissions",
    EMERGENCY: "Urgences",
    PHARMACY: "Pharmacie",
    LAB: "Laboratoire",
    BILLING: "Facturation",
    HOSPITALIZATION: "Hospit.",
    MATERNITY: "Maternité",
    PERSONNEL: "Personnel",
    IMAGING: "Imagerie",
    SURGERY: "Chirurgie",
    QUALITY: "Qualité",
    REPORTING: "Reporting",
    AUTH: "Auth",
  };

  const actionCountToday = useMemo(() => {
    const countMap: Record<string, number> = {};
    todayEntries.forEach((e) => {
      const act = e._actionType;
      countMap[act] = (countMap[act] || 0) + 1;
    });
    return countMap;
  }, [todayEntries]);

  return (
    <section>
      <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "4px" }}>
        <h1 style={{ margin: 0 }}>Activité & Audit</h1>
      </div>
      <p className="muted" style={{ marginBottom: "16px" }}>
        Journal d'activité et traçabilité des actions utilisateurs.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "20px" }}>
        {/* ── Left Column: Filters + Timeline ──────── */}
        <div>
          {/* ── Filters ──────────────────────────────── */}
          <div
            className="card"
            style={{
              marginBottom: "16px",
              padding: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "14px",
                fontWeight: 700,
                fontSize: "14px",
                color: "var(--text)",
              }}
            >
              <Filter size={16} />
              Filtres
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                gap: "12px",
                alignItems: "end",
              }}
            >
              <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
                <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  Action
                </span>
                <select
                  value={actionFilter}
                  onChange={(e) => setActionFilter(e.target.value as ActionType)}
                  style={{ fontSize: "13px" }}
                >
                  {ACTION_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
                <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  Module
                </span>
                <select
                  value={moduleFilter}
                  onChange={(e) => setModuleFilter(e.target.value as ModuleType)}
                  style={{ fontSize: "13px" }}
                >
                  {MODULE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
                <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  Utilisateur
                </span>
                <select
                  value={userFilter}
                  onChange={(e) => setUserFilter(e.target.value)}
                  style={{ fontSize: "13px" }}
                >
                  <option value="">Tous les utilisateurs</option>
                  {lookups.staff.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.first_name || ""} {s.last_name || ""}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
                <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  Date début
                </span>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  style={{ fontSize: "13px" }}
                />
              </div>
              <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
                <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  Date fin
                </span>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  style={{ fontSize: "13px" }}
                />
              </div>
              <div style={{ display: "grid", gap: "6px", fontWeight: 600, fontSize: "13px" }}>
                <span style={{ color: "var(--muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  Recherche
                </span>
                <div style={{ position: "relative" }}>
                  <Search
                    size={14}
                    style={{
                      position: "absolute",
                      left: "10px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      color: "var(--muted)",
                    }}
                  />
                  <input
                    type="text"
                    placeholder="Rechercher..."
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    style={{ paddingLeft: "30px", fontSize: "13px" }}
                  />
                </div>
              </div>
            </div>
            <div
              style={{
                display: "flex",
                gap: "8px",
                marginTop: "12px",
                alignItems: "center",
              }}
            >
              <button
                className="btn btn-outline btn-sm"
                onClick={() => {
                  setActionFilter("ALL");
                  setModuleFilter("ALL");
                  setUserFilter("");
                  setSearchText("");
                  setDateFrom("");
                  setDateTo("");
                }}
              >
                <X size={14} />
                Réinitialiser
              </button>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setRefreshKey((k) => k + 1)}
              >
                <RefreshCw size={14} />
                Actualiser
              </button>
              <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "6px" }}>
                <button
                  className="btn btn-sm"
                  style={{
                    background: autoRefresh ? "var(--primary-light)" : "transparent",
                    color: autoRefresh ? "var(--primary)" : "var(--muted)",
                    border: `1px solid ${autoRefresh ? "var(--primary)" : "var(--border)"}`,
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                  onClick={() => setAutoRefresh(!autoRefresh)}
                >
                  {autoRefresh ? <ToggleRight size={14} /> : <ToggleLeft size={14} />}
                  Auto-refresh
                </button>
              </div>
            </div>
          </div>

          {/* ── Timeline ─────────────────────────────── */}
          {loading ? (
            <div className="card" style={{ textAlign: "center", padding: "32px" }}>
              <div className="spinner" />
              <p className="muted" style={{ marginTop: "12px" }}>
                Chargement du journal d'activité...
              </p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: "32px" }}>
              <Activity size={32} style={{ color: "var(--muted)", marginBottom: "8px" }} />
              <p className="muted">Aucune activité trouvée.</p>
            </div>
          ) : (
            <div className="card" style={{ padding: "20px" }}>
              {/* Action type legend */}
              <div
                style={{
                  display: "flex",
                  gap: "12px",
                  flexWrap: "wrap",
                  marginBottom: "18px",
                  paddingBottom: "14px",
                  borderBottom: "1px solid var(--border-light)",
                }}
              >
                {Object.entries(ACTION_COLORS).map(([action, colors]) => (
                  <div
                    key={action}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "5px",
                      fontSize: "12px",
                      fontWeight: 600,
                      color: colors.text,
                    }}
                  >
                    <span
                      style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        background: colors.dot,
                        display: "inline-block",
                      }}
                    />
                    {formatActionLabel(action.toLowerCase())}
                    {actionCountToday[action] !== undefined && (
                      <span
                        style={{
                          background: colors.bg,
                          borderRadius: "10px",
                          padding: "0 6px",
                          fontSize: "11px",
                        }}
                      >
                        {actionCountToday[action]}
                      </span>
                    )}
                  </div>
                ))}
              </div>

              {/* Timeline */}
              <div style={{ position: "relative" }}>
                {visibleEntries.map((entry, index) => {
                  const actionType = entry._actionType;
                  const colors = ACTION_COLORS[actionType] || ACTION_COLORS.UPDATE;
                  const isLast = index === visibleEntries.length - 1;

                  return (
                    <div
                      key={entry.id}
                      style={{
                        display: "flex",
                        gap: "16px",
                        position: "relative",
                        minHeight: "56px",
                      }}
                    >
                      {/* Timeline line + dot */}
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          width: "20px",
                          flexShrink: 0,
                        }}
                      >
                        <div
                          style={{
                            width: "12px",
                            height: "12px",
                            borderRadius: "50%",
                            background: colors.dot,
                            border: `2px solid ${colors.bg}`,
                            flexShrink: 0,
                            marginTop: "6px",
                            zIndex: 1,
                          }}
                        />
                        {!isLast && (
                          <div
                            style={{
                              width: "2px",
                              flex: 1,
                              background: "var(--border-light)",
                              minHeight: "40px",
                            }}
                          />
                        )}
                      </div>

                      {/* Content */}
                      <div
                        style={{
                          flex: 1,
                          paddingBottom: isLast ? 0 : "14px",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            flexWrap: "wrap",
                            marginBottom: "4px",
                          }}
                        >
                          {/* Action badge */}
                          <span
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              padding: "2px 8px",
                              borderRadius: "var(--radius-full)",
                              fontSize: "11px",
                              fontWeight: 700,
                              background: colors.bg,
                              color: colors.text,
                              border: `1px solid ${colors.border}`,
                            }}
                          >
                            {formatActionLabel(entry.action_name || "")}
                          </span>

                          {/* Entity */}
                          <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text)" }}>
                            {formatEntityLabel(entry.entity_type)}
                          </span>

                          {/* Module badge */}
                          <span
                            style={{
                              fontSize: "11px",
                              color: "var(--muted)",
                              background: "var(--border-light)",
                              padding: "1px 6px",
                              borderRadius: "var(--radius-full)",
                            }}
                          >
                            {moduleLabelMap[entry._module] || entry._module}
                          </span>
                        </div>

                        {/* Description */}
                        <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "4px" }}>
                          {entry.notes || entry.action_name || "—"}
                        </div>

                        {/* Meta: user + time */}
                        <div
                          style={{
                            display: "flex",
                            gap: "12px",
                            fontSize: "12px",
                            color: "var(--muted)",
                          }}
                        >
                          <span style={{ display: "flex", alignItems: "center", gap: "3px" }}>
                            <User size={12} />
                            {getUserName(entry.actor_id)}
                          </span>
                          <span style={{ display: "flex", alignItems: "center", gap: "3px" }}>
                            <Clock size={12} />
                            {entry.created_at
                              ? new Date(entry.created_at).toLocaleString("fr-FR", {
                                  day: "2-digit",
                                  month: "2-digit",
                                  year: "numeric",
                                  hour: "2-digit",
                                  minute: "2-digit",
                                  second: "2-digit",
                                })
                              : "—"}
                          </span>
                          {entry.entity_id && (
                            <span style={{ display: "flex", alignItems: "center", gap: "3px" }}>
                              <Eye size={12} />
                              {entry.entity_id.slice(0, 8)}...
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Load more */}
              {hasMore && (
                <div
                  style={{
                    textAlign: "center",
                    marginTop: "16px",
                    paddingTop: "16px",
                    borderTop: "1px solid var(--border-light)",
                  }}
                >
                  <button
                    className="btn btn-outline"
                    onClick={() => setVisibleCount((c) => c + 25)}
                  >
                    <ChevronDown size={16} />
                    Charger plus ({filtered.length - visibleCount} restantes)
                  </button>
                </div>
              )}

              <div
                style={{
                  marginTop: "12px",
                  fontSize: "13px",
                  color: "var(--muted)",
                  fontWeight: 600,
                }}
              >
                {filtered.length} entrée{filtered.length > 1 ? "s" : ""} au total
              </div>
            </div>
          )}
        </div>

        {/* ── Right Sidebar: Summary ─────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Activity today card */}
          <div className="card">
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "12px",
                fontWeight: 700,
                fontSize: "14px",
                color: "var(--text)",
              }}
            >
              <Zap size={16} style={{ color: "var(--warning)" }} />
              Activité aujourd'hui
            </div>
            <div
              style={{
                fontSize: "36px",
                fontWeight: 800,
                color: "var(--primary)",
                lineHeight: 1.2,
              }}
            >
              {todayEntries.length}
            </div>
            <div style={{ fontSize: "13px", color: "var(--muted)", fontWeight: 500 }}>
              action{todayEntries.length > 1 ? "s" : ""} aujourd'hui
            </div>

            {/* Action breakdown */}
            {Object.keys(actionCountToday).length > 0 && (
              <div style={{ marginTop: "14px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {Object.entries(actionCountToday).map(([action, count]) => {
                  const colors = ACTION_COLORS[action] || ACTION_COLORS.UPDATE;
                  return (
                    <span
                      key={action}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                        padding: "3px 8px",
                        borderRadius: "var(--radius-full)",
                        fontSize: "12px",
                        fontWeight: 600,
                        background: colors.bg,
                        color: colors.text,
                      }}
                    >
                      <span
                        style={{
                          width: "6px",
                          height: "6px",
                          borderRadius: "50%",
                          background: colors.dot,
                        }}
                      />
                      {count}
                    </span>
                  );
                })}
              </div>
            )}
          </div>

          {/* Top users today */}
          <div className="card">
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "12px",
                fontWeight: 700,
                fontSize: "14px",
                color: "var(--text)",
              }}
            >
              <Users size={16} style={{ color: "var(--accent)" }} />
              Utilisateurs actifs
            </div>
            {topUsersToday.length === 0 ? (
              <p className="muted" style={{ fontSize: "13px" }}>
                Aucune activité aujourd'hui
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {topUsersToday.map(([name, count], idx) => (
                  <div
                    key={name}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                    }}
                  >
                    <div
                      style={{
                        width: "28px",
                        height: "28px",
                        borderRadius: "50%",
                        background:
                          idx === 0
                            ? "var(--primary-light)"
                            : "var(--border-light)",
                        color: idx === 0 ? "var(--primary)" : "var(--muted)",
                        display: "grid",
                        placeItems: "center",
                        fontSize: "12px",
                        fontWeight: 700,
                        flexShrink: 0,
                      }}
                    >
                      {idx + 1}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: "13px",
                          fontWeight: 600,
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {name}
                      </div>
                      <div
                        style={{
                          height: "4px",
                          borderRadius: "2px",
                          background: "var(--border-light)",
                          marginTop: "3px",
                        }}
                      >
                        <div
                          style={{
                            height: "100%",
                            borderRadius: "2px",
                            background: idx === 0 ? "var(--primary)" : "var(--accent)",
                            width: `${Math.round(
                              (count / (topUsersToday[0]?.[1] || 1)) * 100
                            )}%`,
                            transition: "width 0.3s ease",
                          }}
                        />
                      </div>
                    </div>
                    <span
                      style={{
                        fontSize: "13px",
                        fontWeight: 700,
                        color: "var(--text)",
                        flexShrink: 0,
                      }}
                    >
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions by module */}
          <div className="card">
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "12px",
                fontWeight: 700,
                fontSize: "14px",
                color: "var(--text)",
              }}
            >
              <BarChart3 size={16} style={{ color: "var(--primary)" }} />
              Actions par module
            </div>
            {moduleCounts.length === 0 ? (
              <p className="muted" style={{ fontSize: "13px" }}>
                Aucune donnée
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {moduleCounts.map(([mod, count]) => {
                  const pct = Math.round((count / maxModuleCount) * 100);
                  return (
                    <div key={mod}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          fontSize: "12px",
                          marginBottom: "3px",
                        }}
                      >
                        <span style={{ fontWeight: 600, color: "var(--text)" }}>
                          {moduleLabelMap[mod] || mod}
                        </span>
                        <span style={{ fontWeight: 700, color: "var(--muted)" }}>
                          {count}
                        </span>
                      </div>
                      <div
                        style={{
                          height: "6px",
                          borderRadius: "3px",
                          background: "var(--border-light)",
                        }}
                      >
                        <div
                          style={{
                            height: "100%",
                            borderRadius: "3px",
                            background: "var(--primary)",
                            width: `${pct}%`,
                            transition: "width 0.3s ease",
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Quick stats */}
          <div className="card" style={{ background: "var(--primary-light)", border: "1px solid var(--primary-200)" }}>
            <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--primary)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "8px" }}>
              Statistiques globales
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
              <div>
                <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--primary)" }}>
                  {entries.length}
                </div>
                <div style={{ fontSize: "11px", color: "var(--primary)", opacity: 0.8 }}>
                  Total entrées
                </div>
              </div>
              <div>
                <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--primary)" }}>
                  {new Set(entries.map((e) => e.actor_id).filter(Boolean)).size}
                </div>
                <div style={{ fontSize: "11px", color: "var(--primary)", opacity: 0.8 }}>
                  Utilisateurs
                </div>
              </div>
              <div>
                <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--primary)" }}>
                  {new Set(entries.map((e) => e.entity_type).filter(Boolean)).size}
                </div>
                <div style={{ fontSize: "11px", color: "var(--primary)", opacity: 0.8 }}>
                  Types d'entités
                </div>
              </div>
              <div>
                <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--primary)" }}>
                  {new Set(enrichedEntries.map((e) => e._module).filter(Boolean)).size}
                </div>
                <div style={{ fontSize: "11px", color: "var(--primary)", opacity: 0.8 }}>
                  Modules
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
