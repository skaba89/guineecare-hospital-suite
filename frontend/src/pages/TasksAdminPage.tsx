import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { showToast } from "../components/Toast";
import { useAuth } from "../contexts/AuthContext";
import {
  RefreshCw, Play, Clock, CheckCircle, XCircle, AlertTriangle,
  Database, Trash2, Send, Activity, Server,
} from "lucide-react";

/**
 * Tasks Admin Page — v2.9.2
 *
 * Interface d'administration des tâches planifiées Celery :
 *   - Liste les 5 tâches disponibles (prune audit, backup, retry SMS, push DHIS2, digest qualité)
 *   - Affiche le statut du worker Celery (disponible / synchrone)
 *   - Permet de déclencher manuellement chaque tâche (SUPER_ADMIN seulement)
 *   - Historique des exécutions récentes (via audit_logs filtrés)
 *
 * Accès : SUPER_ADMIN uniquement (page protégée via ProtectedRoute dans App.tsx)
 */

type TaskInfo = {
  name: string;
  path: string;
  async_enabled: boolean;
};

type TasksListResponse = {
  tasks: TaskInfo[];
  celery_available: boolean;
  broker_url_configured: boolean;
};

type TriggerResponse = {
  task: string;
  status: "sync_executed" | "submitted";
  result: Record<string, unknown>;
};

type AuditLogEntry = {
  id: string;
  created_at: string;
  action: string;
  status_code: number | null;
  payload: any;
};

type PaginatedAuditResponse = {
  data: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

// Métadonnées d'affichage par tâche
const TASK_META: Record<
  string,
  {
    label: string;
    description: string;
    icon: typeof Database;
    color: string;
    schedule: string;
    danger?: boolean;
  }
> = {
  prune_audit_logs: {
    label: "Purge audit log",
    description: "Supprime les entrées audit_logs > 365 jours (RGPD Art. 25)",
    icon: Trash2,
    color: "#dc2626",
    schedule: "Quotidien 03h00 UTC",
    danger: true,
  },
  backup_database: {
    label: "Backup database",
    description: "Dump PostgreSQL complet + rotation 30 jours",
    icon: Database,
    color: "#2563eb",
    schedule: "Quotidien 04h00 UTC",
  },
  retry_sms_pending: {
    label: "Retry SMS pending",
    description: "Re-tente l'envoi des SMS en échec (max 24h)",
    icon: Send,
    color: "#f59e0b",
    schedule: "Toutes les 5 minutes",
  },
  push_dhis2_monthly: {
    label: "Push DHIS2 mensuel",
    description: "Pousse le dataset DHIS2 du mois précédent vers l'instance nationale",
    icon: Send,
    color: "#7c3aed",
    schedule: "Le 5 du mois à 06h00 UTC",
  },
  send_quality_alerts_digest: {
    label: "Digest qualité",
    description: "Envoie un digest quotidien des alertes qualité aux administrateurs",
    icon: Activity,
    color: "#10b981",
    schedule: "Quotidien 06h30 UTC",
  },
};

function formatDateTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function TasksAdminPage() {
  const { isSuperAdmin } = useAuth();
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [celeryAvailable, setCeleryAvailable] = useState(false);
  const [brokerConfigured, setBrokerConfigured] = useState(false);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [lastResults, setLastResults] = useState<Record<string, TriggerResponse>>({});
  const [history, setHistory] = useState<AuditLogEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Charger la liste des tâches
  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiRequest<TasksListResponse>("/tasks");
      setTasks(res.tasks || []);
      setCeleryAvailable(res.celery_available);
      setBrokerConfigured(res.broker_url_configured);
    } catch (e: any) {
      showToast("Erreur chargement tâches: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  }, []);

  // Charger l'historique des exécutions de tâches (audit logs)
  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const params = new URLSearchParams({
        page: "1",
        page_size: "20",
        resource_type: "task",
      });
      const res = await apiRequest<PaginatedAuditResponse>(
        `/audit/logs?${params.toString()}`
      );
      setHistory(res.data || []);
    } catch {
      // Audit endpoint peut échouer si user n'a pas la permission — silencieux
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTasks();
    loadHistory();
  }, [loadTasks, loadHistory]);

  // Déclencher une tâche
  const triggerTask = async (taskName: string) => {
    const meta = TASK_META[taskName];
    const confirmMsg = meta?.danger
      ? `⚠️ Cette tâche est destructrice (${meta.label}). Continuer ?`
      : `Déclencher la tâche "${meta?.label || taskName}" maintenant ?`;

    if (!window.confirm(confirmMsg)) return;

    setTriggering(taskName);
    try {
      // Paramètres optionnels selon la tâche
      const payload: Record<string, unknown> = {};
      if (taskName === "prune_audit_logs") {
        const days = window.prompt("Rétention en jours (défaut: 365):", "365");
        if (days === null) return;

        const retentionDays = Number(days);
        if (
          !Number.isInteger(retentionDays) ||
          retentionDays < 30 ||
          retentionDays > 3650
        ) {
          showToast(
            "Rétention invalide : saisir un entier entre 30 et 3650 jours.",
            "error"
          );
          return;
        }
        payload.retention_days = retentionDays;
      } else if (taskName === "push_dhis2_monthly") {
        const period = window.prompt(
          "Période YYYYMM (vide = mois précédent):",
          ""
        );
        if (period) payload.period = period;
      }

      const res = await apiRequest<TriggerResponse>(
        `/tasks/trigger/${taskName}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );

      setLastResults((prev) => ({ ...prev, [taskName]: res }));
      showToast(
        `✓ Tâche "${taskName}" exécutée (${res.status})`,
        "success"
      );
      // Rafraîchir l'historique
      loadHistory();
    } catch (e: any) {
      showToast(`Erreur exécution "${taskName}": ${e.message}`, "error");
    } finally {
      setTriggering(null);
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <h1>⚙️ Tâches planifiées</h1>
        <div className="loading-state">
          <RefreshCw className="spin" size={24} /> Chargement…
        </div>
      </div>
    );
  }

  return (
    <div className="page-container" style={{ padding: "24px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: "28px", color: "var(--text)" }}>
            ⚙️ Tâches planifiées
          </h1>
          <p
            style={{
              margin: "4px 0 0",
              color: "var(--muted)",
              fontSize: "14px",
            }}
          >
            Gestion et exécution des tâches Celery — v2.9.2
          </p>
        </div>
        <button
          onClick={() => {
            loadTasks();
            loadHistory();
          }}
          className="btn-secondary"
          style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
        >
          <RefreshCw size={16} /> Rafraîchir
        </button>
      </div>

      {/* ── Statut infrastructure ─────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
          gap: "16px",
          marginBottom: "24px",
        }}
      >
        <StatusCard
          icon={Server}
          label="Worker Celery"
          value={celeryAvailable ? "Actif" : "Synchrone (fallback)"}
          color={celeryAvailable ? "#10b981" : "#f59e0b"}
        />
        <StatusCard
          icon={Database}
          label="Broker Redis"
          value={brokerConfigured ? "Configuré" : "Non configuré"}
          color={brokerConfigured ? "#10b981" : "#ef4444"}
        />
        <StatusCard
          icon={Activity}
          label="Tâches disponibles"
          value={String(tasks.length)}
          color="#2563eb"
        />
      </div>

      {!celeryAvailable && (
        <div
          style={{
            background: "var(--warning-light)",
            border: "1px solid var(--warning)",
            borderRadius: "var(--radius-md)",
            padding: "12px 16px",
            marginBottom: "24px",
            display: "flex",
            gap: "12px",
            alignItems: "center",
          }}
        >
          <AlertTriangle size={20} color="var(--warning)" />
          <div style={{ flex: 1 }}>
            <strong>Mode synchrone actif.</strong> Les tâches s'exécutent dans
            le processus de l'API (pas de worker Celery). Pour activer le mode
            asynchrone, configurez{" "}
            <code>REDIS_URL</code> et démarrez un worker Celery.
          </div>
        </div>
      )}

      {/* ── Liste des tâches ──────────────────────────────────── */}
      <h2 style={{ fontSize: "20px", marginBottom: "12px", color: "var(--text)" }}>
        Tâches disponibles
      </h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(380px, 1fr))",
          gap: "16px",
          marginBottom: "32px",
        }}
      >
        {tasks.map((task) => {
          const meta = TASK_META[task.name] || {
            label: task.name,
            description: "",
            icon: Activity,
            color: "#6b7280",
            schedule: "",
          };
          const Icon = meta.icon;
          const result = lastResults[task.name];
          const isTriggering = triggering === task.name;

          return (
            <div
              key={task.name}
              className="card"
              style={{
                padding: "20px",
                borderLeft: `4px solid ${meta.color}`,
                display: "flex",
                flexDirection: "column",
                gap: "12px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                }}
              >
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "var(--radius-md)",
                    background: `${meta.color}20`,
                    color: meta.color,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Icon size={20} />
                </div>
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      fontWeight: 600,
                      fontSize: "16px",
                      color: "var(--text)",
                    }}
                  >
                    {meta.label}
                  </div>
                  <div
                    style={{
                      fontSize: "12px",
                      color: "var(--muted)",
                      fontFamily: "monospace",
                    }}
                  >
                    {task.name}
                  </div>
                </div>
              </div>

              <p
                style={{
                  margin: 0,
                  fontSize: "13px",
                  color: "var(--text-secondary)",
                  minHeight: "32px",
                }}
              >
                {meta.description}
              </p>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  fontSize: "12px",
                  color: "var(--muted)",
                }}
              >
                <Clock size={12} />
                <span>{meta.schedule}</span>
              </div>

              {/* Résultat dernière exécution */}
              {result && (
                <div
                  style={{
                    background: "var(--success-light)",
                    border: "1px solid var(--success)",
                    borderRadius: "var(--radius-sm)",
                    padding: "8px 12px",
                    fontSize: "12px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      color: "var(--success)",
                      fontWeight: 600,
                      marginBottom: "4px",
                    }}
                  >
                    <CheckCircle size={14} />
                    Exécuté ({result.status})
                  </div>
                  <pre
                    style={{
                      margin: 0,
                      fontSize: "11px",
                      color: "var(--text-secondary)",
                      whiteSpace: "pre-wrap",
                      maxHeight: "100px",
                      overflow: "auto",
                    }}
                  >
                    {JSON.stringify(result.result, null, 2)}
                  </pre>
                </div>
              )}

              <button
                onClick={() => triggerTask(task.name)}
                disabled={isTriggering || !isSuperAdmin}
                className={meta.danger ? "btn-danger" : "btn-primary"}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "6px",
                  width: "100%",
                  marginTop: "auto",
                }}
              >
                {isTriggering ? (
                  <>
                    <RefreshCw size={14} className="spin" /> Exécution…
                  </>
                ) : (
                  <>
                    <Play size={14} /> Exécuter maintenant
                  </>
                )}
              </button>
            </div>
          );
        })}
      </div>

      {/* ── Historique des exécutions ─────────────────────────── */}
      <h2 style={{ fontSize: "20px", marginBottom: "12px", color: "var(--text)" }}>
        Historique récent
      </h2>
      {historyLoading ? (
        <div style={{ padding: "24px", textAlign: "center", color: "var(--muted)" }}>
          <RefreshCw className="spin" size={20} /> Chargement…
        </div>
      ) : history.length === 0 ? (
        <div
          style={{
            padding: "24px",
            textAlign: "center",
            color: "var(--muted)",
            background: "var(--card)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border)",
          }}
        >
          Aucune exécution de tâche enregistrée dans l'audit log.
        </div>
      ) : (
        <div
          style={{
            background: "var(--card)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border)",
            overflow: "hidden",
          }}
        >
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: "13px",
            }}
          >
            <thead>
              <tr
                style={{
                  background: "var(--bg)",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <th style={{ padding: "10px 12px", textAlign: "left" }}>Date</th>
                <th style={{ padding: "10px 12px", textAlign: "left" }}>Tâche</th>
                <th style={{ padding: "10px 12px", textAlign: "left" }}>Statut</th>
                <th style={{ padding: "10px 12px", textAlign: "left" }}>
                  Détails
                </th>
              </tr>
            </thead>
            <tbody>
              {history.map((entry) => {
                const isSuccess = (entry.status_code ?? 0) < 400;
                const taskName =
                  typeof entry.payload === "object" && entry.payload?.task
                    ? entry.payload.task
                    : entry.action.replace("system.", "");
                const meta = TASK_META[taskName];
                return (
                  <tr
                    key={entry.id}
                    style={{ borderBottom: "1px solid var(--border-light)" }}
                  >
                    <td
                      style={{
                        padding: "10px 12px",
                        color: "var(--muted)",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {formatDateTime(entry.created_at)}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      {meta?.label || taskName}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      {isSuccess ? (
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                            color: "var(--success)",
                          }}
                        >
                          <CheckCircle size={14} /> {entry.status_code}
                        </span>
                      ) : (
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                            color: "var(--danger)",
                          }}
                        >
                          <XCircle size={14} /> {entry.status_code}
                        </span>
                      )}
                    </td>
                    <td
                      style={{
                        padding: "10px 12px",
                        color: "var(--muted)",
                        fontSize: "12px",
                        maxWidth: "300px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {typeof entry.payload === "object"
                        ? JSON.stringify(entry.payload).slice(0, 80)
                        : String(entry.payload).slice(0, 80)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {!isSuperAdmin && (
        <div
          style={{
            marginTop: "24px",
            padding: "12px 16px",
            background: "var(--danger-light)",
            border: "1px solid var(--danger)",
            borderRadius: "var(--radius-md)",
            color: "var(--danger)",
            fontSize: "13px",
          }}
        >
          ⚠️ Seul un SUPER_ADMIN peut déclencher des tâches. Vous pouvez
          consulter la liste et l'historique en lecture seule.
        </div>
      )}
    </div>
  );
}

// ── Sous-composant StatusCard ─────────────────────────────────
function StatusCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Database;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div
      className="card"
      style={{
        padding: "16px",
        display: "flex",
        alignItems: "center",
        gap: "12px",
      }}
    >
      <div
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "var(--radius-md)",
          background: `${color}20`,
          color,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Icon size={24} />
      </div>
      <div>
        <div
          style={{
            fontSize: "12px",
            color: "var(--muted)",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
          }}
        >
          {label}
        </div>
        <div
          style={{
            fontSize: "18px",
            fontWeight: 600,
            color: "var(--text)",
          }}
        >
          {value}
        </div>
      </div>
    </div>
  );
}