import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { showToast } from "../components/Toast";

// ── Types ───────────────────────────────────────────────────────────────────

type SmsProvider = {
  id: string;
  code: string;
  name: string;
  enabled: boolean;
  api_url: string | null;
  sender_id: string | null;
  cost_per_sms_gnf: number;
  rate_per_second: number;
  daily_quota: number | null;
  has_api_key: boolean;
  has_api_secret: boolean;
  created_at: string;
  updated_at: string;
};

type SmsRoutingRule = {
  id: string;
  facility_id: string | null;
  category: string;
  channels: string[];
  min_priority: string;
  preferred_provider_id: string | null;
  enabled: boolean;
  description: string | null;
  created_at: string;
};

type SmsMessage = {
  id: string;
  created_at: string;
  facility_id: string | null;
  provider_id: string | null;
  provider_code: string;
  recipient_id: string | null;
  recipient_phone: string;
  body: string;
  category: string;
  priority: string;
  notification_id: string | null;
  status: string;
  operator_message_id: string | null;
  error_code: string | null;
  error_message: string | null;
  cost_gnf: number;
  attempts: number;
  sent_at: string | null;
  delivered_at: string | null;
};

type SmsStats = {
  since: string;
  total: number;
  sent: number;
  failed: number;
  pending: number;
  rejected: number;
  success_rate_pct: number;
  total_cost_gnf: number;
  by_provider: { provider: string; total: number; sent: number }[];
  by_category: { category: string; total: number; sent: number }[];
};

type TabKey = "providers" | "rules" | "messages" | "stats";

const TABS: { key: TabKey; label: string }[] = [
  { key: "providers", label: "Providers" },
  { key: "rules", label: "Règles de routage" },
  { key: "messages", label: "Historique" },
  { key: "stats", label: "Statistiques" },
];

const PROVIDER_CODE_OPTIONS = [
  { value: "mock", label: "Mock (dev/test)" },
  { value: "orange", label: "Orange Guinée SMS Pro" },
  { value: "mtn", label: "MTN Guinée SMS Gateway" },
  { value: "moov", label: "Moov Africa SMS API" },
];

const PRIORITY_OPTIONS = [
  { value: "low", label: "Basse" },
  { value: "normal", label: "Normale" },
  { value: "high", label: "Haute" },
  { value: "urgent", label: "Urgente" },
];

const STATUS_BADGE: Record<string, string> = {
  PENDING: "badge-yellow",
  SENT: "badge-green",
  DELIVERED: "badge-green",
  FAILED: "badge-red",
  REJECTED: "badge-gray",
};

const STATUS_LABEL: Record<string, string> = {
  PENDING: "En attente",
  SENT: "Envoyé",
  DELIVERED: "Livré",
  FAILED: "Échec",
  REJECTED: "Rejeté",
};

// ── Main component ──────────────────────────────────────────────────────────

export function SmsAdminPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("providers");

  return (
    <section>
      <h1>Notifications SMS — Administration</h1>
      <p className="muted">
        Configuration des opérateurs SMS locaux (Orange / MTN / Moov), règles de
        routage par catégorie et suivi des envois. v1.4.0
      </p>

      <div className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`tab-button ${activeTab === tab.key ? "active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "providers" && <ProvidersTab />}
      {activeTab === "rules" && <RulesTab />}
      {activeTab === "messages" && <MessagesTab />}
      {activeTab === "stats" && <StatsTab />}
    </section>
  );
}

// ── Providers Tab ───────────────────────────────────────────────────────────

function ProvidersTab() {
  const [providers, setProviders] = useState<SmsProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [testTarget, setTestTarget] = useState<{ id: string; name: string } | null>(null);
  const [testPhone, setTestPhone] = useState("+224622000000");
  const [testBody, setTestBody] = useState("");

  // Form state
  const [code, setCode] = useState("orange");
  const [name, setName] = useState("");
  const [apiUrl, setApiUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [senderId, setSenderId] = useState("GUINEECARE");
  const [costPerSms, setCostPerSms] = useState("25");
  const [ratePerSecond, setRatePerSecond] = useState("10");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<{ data: SmsProvider[] }>(
        "/notifications/sms/providers"
      );
      setProviders(payload.data || []);
    } catch {
      setError("Impossible de charger les providers.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const handler = () => load();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [load]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!code || !name) return;
    setSubmitting(true);
    try {
      await apiRequest("/notifications/sms/providers", {
        method: "POST",
        body: JSON.stringify({
          code,
          name: name.trim(),
          enabled: true,
          api_url: apiUrl.trim() || undefined,
          api_key: apiKey.trim() || undefined,
          api_secret: apiSecret.trim() || undefined,
          sender_id: senderId.trim() || undefined,
          cost_per_sms_gnf: parseInt(costPerSms, 10) || 0,
          rate_per_second: parseInt(ratePerSecond, 10) || 10,
        }),
      });
      setShowForm(false);
      setName(""); setApiUrl(""); setApiKey(""); setApiSecret("");
      setCostPerSms("25");
      load();
      showToast("Provider créé avec succès.", "success");
    } catch {
      showToast("Erreur lors de la création du provider.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleToggle(p: SmsProvider) {
    try {
      await apiRequest(`/notifications/sms/providers/${p.id}`, {
        method: "PATCH",
        body: JSON.stringify({ enabled: !p.enabled }),
      });
      load();
      showToast(`Provider ${p.code} ${!p.enabled ? "activé" : "désactivé"}.`, "success");
    } catch {
      showToast("Erreur lors du changement d'état.", "error");
    }
  }

  async function handleDelete(p: SmsProvider) {
    if (!confirm(`Supprimer le provider ${p.code} ? Cette action est irréversible.`)) return;
    try {
      await apiRequest(`/notifications/sms/providers/${p.id}`, { method: "DELETE" });
      load();
      showToast("Provider supprimé.", "success");
    } catch (e: any) {
      showToast(e.message || "Erreur lors de la suppression.", "error");
    }
  }

  async function handleTestProvider() {
    if (!testTarget) return;
    try {
      const result = await apiRequest<{ success: boolean; message_id: string | null; error_message: string | null }>(
        `/notifications/sms/providers/${testTarget.id}/test`,
        {
          method: "POST",
          body: JSON.stringify({
            to: testPhone,
            body: testBody || undefined,
          }),
        }
      );
      if (result.success) {
        showToast(`Test réussi — message ID: ${result.message_id}`, "success");
      } else {
        showToast(`Test échoué — ${result.error_message}`, "error");
      }
      setTestTarget(null);
      setTestBody("");
    } catch (e: any) {
      showToast(e.message || "Erreur lors du test.", "error");
    }
  }

  if (loading) return <div className="muted">Chargement…</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Providers SMS ({providers.length})</h2>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Annuler" : "+ Nouveau provider"}
        </button>
      </div>

      {showForm && (
        <form className="card form-card" onSubmit={handleSubmit}>
          <h3>Nouveau provider SMS</h3>
          <div className="form-grid">
            <label>
              Opérateur *
              <select value={code} onChange={(e) => setCode(e.target.value)} required>
                {PROVIDER_CODE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </label>
            <label>
              Nom affiché *
              <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Orange Guinée SMS Pro" />
            </label>
            <label>
              URL API
              <input value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} placeholder="https://api.orange.com/..." />
            </label>
            <label>
              Sender ID
              <input value={senderId} onChange={(e) => setSenderId(e.target.value)} placeholder="GUINEECARE" />
            </label>
            <label>
              Clé API
              <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} type="password" placeholder="••••••••" />
            </label>
            <label>
              Secret API
              <input value={apiSecret} onChange={(e) => setApiSecret(e.target.value)} type="password" placeholder="••••••••" />
            </label>
            <label>
              Coût/SMS (GNF)
              <input type="number" value={costPerSms} onChange={(e) => setCostPerSms(e.target.value)} min="0" />
            </label>
            <label>
              Limite (SMS/s)
              <input type="number" value={ratePerSecond} onChange={(e) => setRatePerSecond(e.target.value)} min="1" max="100" />
            </label>
          </div>
          <div className="form-actions">
            <button type="submit" className="primary-button" disabled={submitting}>
              {submitting ? "Création…" : "Créer le provider"}
            </button>
            <button type="button" className="secondary-button" onClick={() => setShowForm(false)}>
              Annuler
            </button>
          </div>
        </form>
      )}

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Nom</th>
              <th>Statut</th>
              <th>Sender ID</th>
              <th>Credentials</th>
              <th>Coût/SMS (GNF)</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={p.id}>
                <td><code>{p.code}</code></td>
                <td>{p.name}</td>
                <td>
                  <span className={`badge ${p.enabled ? "badge-green" : "badge-gray"}`}>
                    {p.enabled ? "Activé" : "Désactivé"}
                  </span>
                </td>
                <td>{p.sender_id || "—"}</td>
                <td>
                  {p.has_api_key ? "🔑" : "—"} {p.has_api_secret ? "🔑" : ""}
                </td>
                <td>{p.cost_per_sms_gnf}</td>
                <td>
                  <button
                    className="action-button"
                    onClick={() => handleToggle(p)}
                    title={p.enabled ? "Désactiver" : "Activer"}
                  >
                    {p.enabled ? "🔴" : "🟢"}
                  </button>
                  <button
                    className="action-button"
                    onClick={() => setTestTarget({ id: p.id, name: p.name })}
                    title="Tester"
                  >
                    🧪
                  </button>
                  {p.code !== "mock" && (
                    <button
                      className="action-button"
                      onClick={() => handleDelete(p)}
                      title="Supprimer"
                    >
                      🗑️
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {testTarget && (
        <div className="modal-overlay" onClick={() => setTestTarget(null)}>
          <div className="card modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>Tester le provider « {testTarget.name} »</h3>
            <p className="muted">Un SMS réel sera envoyé au numéro indiqué (coût réel selon le provider).</p>
            <label>
              Numéro E.164
              <input value={testPhone} onChange={(e) => setTestPhone(e.target.value)} placeholder="+224622000000" />
            </label>
            <label>
              Message (optionnel)
              <input value={testBody} onChange={(e) => setTestBody(e.target.value)} placeholder="Test GuinéeCare v1.4" />
            </label>
            <div className="form-actions">
              <button className="primary-button" onClick={handleTestProvider}>Envoyer le test</button>
              <button className="secondary-button" onClick={() => setTestTarget(null)}>Annuler</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── Rules Tab ───────────────────────────────────────────────────────────────

function RulesTab() {
  const [rules, setRules] = useState<SmsRoutingRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<{ data: SmsRoutingRule[] }>(
        "/notifications/sms/rules"
      );
      setRules(payload.data || []);
    } catch {
      setError("Impossible de charger les règles.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleToggle(r: SmsRoutingRule) {
    try {
      await apiRequest(`/notifications/sms/rules/${r.id}`, {
        method: "PATCH",
        body: JSON.stringify({ enabled: !r.enabled }),
      });
      load();
      showToast(`Règle ${r.category} ${!r.enabled ? "activée" : "désactivée"}.`, "success");
    } catch {
      showToast("Erreur lors du changement d'état.", "error");
    }
  }

  if (loading) return <div className="muted">Chargement…</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Règles de routage SMS ({rules.length})</h2>
      </div>
      <p className="muted">
        Les règles déterminent quel canal (in_app, sms, email) est utilisé pour
        chaque catégorie de notification, et avec quelle priorité minimale.
      </p>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Catégorie</th>
              <th>Canaux</th>
              <th>Priorité min.</th>
              <th>Périmètre</th>
              <th>Description</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((r) => (
              <tr key={r.id}>
                <td><code>{r.category}</code></td>
                <td>
                  {r.channels.map((c) => (
                    <span key={c} className={`badge ${c === "sms" ? "badge-blue" : "badge-gray"}`} style={{ marginRight: 4 }}>
                      {c}
                    </span>
                  ))}
                </td>
                <td>
                  <span className={`badge ${
                    r.min_priority === "urgent" ? "badge-red" :
                    r.min_priority === "high" ? "badge-yellow" : "badge-gray"
                  }`}>
                    {r.min_priority}
                  </span>
                </td>
                <td>{r.facility_id ? "Facility" : "Global"}</td>
                <td>{r.description || "—"}</td>
                <td>
                  <span className={`badge ${r.enabled ? "badge-green" : "badge-gray"}`}>
                    {r.enabled ? "Active" : "Inactive"}
                  </span>
                </td>
                <td>
                  <button
                    className="action-button"
                    onClick={() => handleToggle(r)}
                    title={r.enabled ? "Désactiver" : "Activer"}
                  >
                    {r.enabled ? "🔴" : "🟢"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ── Messages Tab ────────────────────────────────────────────────────────────

function MessagesTab() {
  const [messages, setMessages] = useState<SmsMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [showSend, setShowSend] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Send form
  const [to, setTo] = useState("+224622334455");
  const [body, setBody] = useState("");
  const [category, setCategory] = useState("manual");
  const [priority, setPriority] = useState("normal");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const path = statusFilter
        ? `/notifications/sms/messages?status=${statusFilter}&page_size=100`
        : `/notifications/sms/messages?page_size=100`;
      const payload = await apiRequest<{ data: SmsMessage[]; total: number }>(path);
      setMessages(payload.data || []);
    } catch {
      setError("Impossible de charger l'historique.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!to || !body) return;
    setSubmitting(true);
    try {
      await apiRequest("/notifications/sms/send", {
        method: "POST",
        body: JSON.stringify({ to, body, category, priority }),
      });
      setShowSend(false);
      setBody("");
      load();
      showToast("SMS envoyé avec succès.", "success");
    } catch {
      showToast("Erreur lors de l'envoi du SMS.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRetry(msgId: string) {
    try {
      await apiRequest(`/notifications/sms/messages/${msgId}/retry`, { method: "POST" });
      load();
      showToast("Retry déclenché.", "success");
    } catch {
      showToast("Erreur lors du retry.", "error");
    }
  }

  if (loading) return <div className="muted">Chargement…</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Historique des SMS ({messages.length})</h2>
        <button className="primary-button" onClick={() => setShowSend(!showSend)}>
          {showSend ? "Annuler" : "+ Envoyer un SMS"}
        </button>
      </div>

      {showSend && (
        <form className="card form-card" onSubmit={handleSend}>
          <h3>Envoi manuel d'un SMS</h3>
          <div className="form-grid">
            <label>
              Destinataire (E.164) *
              <input value={to} onChange={(e) => setTo(e.target.value)} placeholder="+224622334455" required />
            </label>
            <label>
              Catégorie
              <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="manual" />
            </label>
            <label>
              Priorité
              <select value={priority} onChange={(e) => setPriority(e.target.value)}>
                {PRIORITY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </label>
          </div>
          <label>
            Message * <span className="muted">({body.length}/480)</span>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value.slice(0, 480))}
              rows={3}
              placeholder="Rappel RDV demain 10h — CHU Donka"
              required
            />
          </label>
          <div className="form-actions">
            <button type="submit" className="primary-button" disabled={submitting}>
              {submitting ? "Envoi…" : "Envoyer"}
            </button>
            <button type="button" className="secondary-button" onClick={() => setShowSend(false)}>
              Annuler
            </button>
          </div>
        </form>
      )}

      <div className="filter-bar">
        <label>
          Filtrer par statut :
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">Tous</option>
            <option value="SENT">Envoyés</option>
            <option value="FAILED">Échecs</option>
            <option value="PENDING">En attente</option>
            <option value="REJECTED">Rejetés</option>
          </select>
        </label>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Destinataire</th>
              <th>Catégorie</th>
              <th>Provider</th>
              <th>Statut</th>
              <th>Message</th>
              <th>Coût (GNF)</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {messages.length === 0 ? (
              <tr><td colSpan={8} className="muted" style={{ textAlign: "center" }}>Aucun SMS envoyé.</td></tr>
            ) : (
              messages.map((m) => (
                <tr key={m.id}>
                  <td>{new Date(m.created_at).toLocaleString("fr-FR")}</td>
                  <td><code>{m.recipient_phone}</code></td>
                  <td>{m.category}</td>
                  <td><code>{m.provider_code}</code></td>
                  <td>
                    <span className={`badge ${STATUS_BADGE[m.status] || "badge-gray"}`}>
                      {STATUS_LABEL[m.status] || m.status}
                    </span>
                  </td>
                  <td title={m.body}>{m.body.slice(0, 50)}{m.body.length > 50 ? "…" : ""}</td>
                  <td>{m.cost_gnf}</td>
                  <td>
                    {m.status === "FAILED" && m.attempts < 3 && (
                      <button
                        className="action-button"
                        onClick={() => handleRetry(m.id)}
                        title="Réessayer"
                      >
                        🔄
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ── Stats Tab ───────────────────────────────────────────────────────────────

function StatsTab() {
  const [stats, setStats] = useState<SmsStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const payload = await apiRequest<SmsStats>(`/notifications/sms/stats?days=${days}`);
      setStats(payload);
    } catch {
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <div className="muted">Chargement…</div>;
  if (!stats) return <div className="muted">Aucune statistique disponible.</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Statistiques SMS (30 derniers jours)</h2>
        <select value={days} onChange={(e) => setDays(parseInt(e.target.value, 10))}>
          <option value={7}>7 jours</option>
          <option value={30}>30 jours</option>
          <option value={90}>90 jours</option>
        </select>
      </div>

      <div className="stats-grid">
        <div className="card stat-card">
          <div className="stat-label">Total envoyés</div>
          <div className="stat-value">{stats.total}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Succès</div>
          <div className="stat-value stat-success">{stats.sent}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Échecs</div>
          <div className="stat-value stat-error">{stats.failed}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Taux de succès</div>
          <div className="stat-value">{stats.success_rate_pct}%</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Coût total (GNF)</div>
          <div className="stat-value">{stats.total_cost_gnf.toLocaleString("fr-FR")}</div>
        </div>
      </div>

      <div className="card">
        <h3>Répartition par provider</h3>
        <table className="data-table">
          <thead>
            <tr><th>Provider</th><th>Total</th><th>Succès</th><th>Taux</th></tr>
          </thead>
          <tbody>
            {stats.by_provider.map((p) => (
              <tr key={p.provider}>
                <td><code>{p.provider}</code></td>
                <td>{p.total}</td>
                <td>{p.sent}</td>
                <td>{p.total > 0 ? Math.round((p.sent / p.total) * 100) : 0}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Répartition par catégorie</h3>
        <table className="data-table">
          <thead>
            <tr><th>Catégorie</th><th>Total</th><th>Succès</th><th>Taux</th></tr>
          </thead>
          <tbody>
            {stats.by_category.map((c) => (
              <tr key={c.category}>
                <td><code>{c.category}</code></td>
                <td>{c.total}</td>
                <td>{c.sent}</td>
                <td>{c.total > 0 ? Math.round((c.sent / c.total) * 100) : 0}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
