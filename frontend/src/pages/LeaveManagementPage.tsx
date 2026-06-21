import { useCallback, useEffect, useMemo, useState } from "react";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";

// ── Types ───────────────────────────────────────────────────────────────────

type LeaveRequest = {
  id: string;
  staff_id: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  reason: string | null;
  status: string;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
};

type LeaveBalance = {
  id: string;
  staff_id: string;
  year: number;
  accumulated_days: number;
  used_days: number;
  carried_over_days: number;
  pending_days: number;
  remaining_days: number;
};

type TabKey = "requests" | "balances";

const TABS: { key: TabKey; label: string }[] = [
  { key: "requests", label: "Demandes de congé" },
  { key: "balances", label: "Soldes" },
];

const LEAVE_TYPE_LABEL: Record<string, string> = {
  CONGE_ANNUEL: "Congé annuel",
  MALADIE: "Maladie",
  MATERNITE: "Maternité",
  PATERNITE: "Paternité",
  SANS_SOLDE: "Sans solde",
  AUTORISATION: "Autorisation d'absence",
};

const LEAVE_STATUS_LABEL: Record<string, string> = {
  PENDING: "En attente",
  APPROVED: "Approuvée",
  REJECTED: "Refusée",
  CANCELLED: "Annulée",
};

const LEAVE_STATUS_BADGE: Record<string, string> = {
  PENDING: "badge-yellow",
  APPROVED: "badge-green",
  REJECTED: "badge-red",
  CANCELLED: "badge-gray",
};

// ── Main ────────────────────────────────────────────────────────────────────

export function LeaveManagementPage({ lookups }: { lookups: LookupData }) {
  const [activeTab, setActiveTab] = useState<TabKey>("requests");

  return (
    <section>
      <h1>Congés — Demandes & Soldes</h1>
      <p className="muted">
        Module RH v2 : gestion des demandes de congé et soldes annuels.
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

      {activeTab === "requests" && <RequestsTab lookups={lookups} />}
      {activeTab === "balances" && <BalancesTab lookups={lookups} />}
    </section>
  );
}

// ── Requests Tab ────────────────────────────────────────────────────────────

function RequestsTab({ lookups }: { lookups: LookupData }) {
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("PENDING");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      // Reuse existing personnel/leaves endpoint (RH v1)
      const path = statusFilter
        ? `/personnel/leaves?status=${statusFilter}&page_size=100`
        : `/personnel/leaves?page_size=100`;
      const payload = await apiRequest<{ data: LeaveRequest[]; total: number }>(path);
      setRequests(payload.data || []);
    } catch {
      setRequests([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAction(reqId: string, action: "approve" | "reject") {
    try {
      // The existing personnel route uses PATCH /personnel/leaves/{id} with status field
      await apiRequest(`/personnel/leaves/${reqId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: action === "approve" ? "APPROVED" : "REJECTED" }),
      });
      showToast(`Demande ${action === "approve" ? "approuvée" : "refusée"}.`, "success");
      load();
    } catch (e: any) {
      showToast(e.message || "Erreur.", "error");
    }
  }

  const staffById = useMemo(() => {
    const m: Record<string, Row> = {};
    (lookups.staff || []).forEach((s: Row) => { m[s.id] = s; });
    return m;
  }, [lookups.staff]);

  if (loading) return <div className="muted">Chargement…</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Demandes de congé ({requests.length})</h2>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Toutes</option>
          <option value="PENDING">En attente</option>
          <option value="APPROVED">Approuvées</option>
          <option value="REJECTED">Refusées</option>
          <option value="CANCELLED">Annulées</option>
        </select>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date demande</th>
              <th>Staff</th>
              <th>Type</th>
              <th>Période</th>
              <th>Jours</th>
              <th>Raison</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.length === 0 ? (
              <tr><td colSpan={8} className="muted" style={{ textAlign: "center" }}>Aucune demande.</td></tr>
            ) : (
              requests.map((r) => {
                const staff = staffById[r.staff_id];
                const days = Math.ceil(
                  (new Date(r.end_date).getTime() - new Date(r.start_date).getTime()) / 86400000
                ) + 1;
                return (
                  <tr key={r.id}>
                    <td>{new Date(r.created_at).toLocaleDateString("fr-FR")}</td>
                    <td>
                      {staff ? `${staff.first_name} ${staff.last_name}` : r.staff_id}
                      <div className="muted" style={{ fontSize: 11 }}>{staff?.employee_number}</div>
                    </td>
                    <td>{LEAVE_TYPE_LABEL[r.leave_type] || r.leave_type}</td>
                    <td>
                      {new Date(r.start_date).toLocaleDateString("fr-FR")}
                      {" → "}
                      {new Date(r.end_date).toLocaleDateString("fr-FR")}
                    </td>
                    <td><strong>{days}j</strong></td>
                    <td>{r.reason || "—"}</td>
                    <td>
                      <span className={`badge ${LEAVE_STATUS_BADGE[r.status] || "badge-gray"}`}>
                        {LEAVE_STATUS_LABEL[r.status] || r.status}
                      </span>
                    </td>
                    <td>
                      {r.status === "PENDING" && (
                        <>
                          <button
                            className="action-button"
                            onClick={() => handleAction(r.id, "approve")}
                            title="Approuver"
                          >
                            ✅
                          </button>
                          <button
                            className="action-button"
                            onClick={() => handleAction(r.id, "reject")}
                            title="Refuser"
                          >
                            ❌
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ── Balances Tab ────────────────────────────────────────────────────────────

function BalancesTab({ lookups }: { lookups: LookupData }) {
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState(new Date().getFullYear());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const payload = await apiRequest<{ data: LeaveBalance[]; total: number }>(
        `/personnel/leave-balances?year=${year}`
      );
      setBalances(payload.data || []);
    } catch {
      setBalances([]);
    } finally {
      setLoading(false);
    }
  }, [year]);

  useEffect(() => {
    load();
  }, [load]);

  const staffById = useMemo(() => {
    const m: Record<string, Row> = {};
    (lookups.staff || []).forEach((s: Row) => { m[s.id] = s; });
    return m;
  }, [lookups.staff]);

  if (loading) return <div className="muted">Chargement…</div>;

  return (
    <>
      <div className="section-header">
        <h2 style={{ margin: 0 }}>Soldes de congés {year}</h2>
        <select value={year} onChange={(e) => setYear(parseInt(e.target.value, 10))}>
          {[year - 1, year, year + 1].map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Staff</th>
              <th>Droit annuel</th>
              <th>Report N-1</th>
              <th>Pris</th>
              <th>En attente</th>
              <th>Restant</th>
              <th>Taux utilisation</th>
            </tr>
          </thead>
          <tbody>
            {balances.length === 0 ? (
              <tr><td colSpan={7} className="muted" style={{ textAlign: "center" }}>Aucun solde pour {year}.</td></tr>
            ) : (
              balances.map((b) => {
                const staff = staffById[b.staff_id];
                const total = b.accumulated_days + b.carried_over_days;
                const usedPct = total > 0 ? Math.round((b.used_days / total) * 100) : 0;
                return (
                  <tr key={b.id}>
                    <td>
                      {staff ? `${staff.first_name} ${staff.last_name}` : b.staff_id}
                      <div className="muted" style={{ fontSize: 11 }}>{staff?.employee_number}</div>
                    </td>
                    <td>{b.accumulated_days}j</td>
                    <td>{b.carried_over_days}j</td>
                    <td>{b.used_days}j</td>
                    <td>{b.pending_days}j</td>
                    <td>
                      <strong style={{
                        color: b.remaining_days < 5 ? "#dc2626" : b.remaining_days < 10 ? "#f59e0b" : "#10b981",
                      }}>
                        {b.remaining_days}j
                      </strong>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ flex: 1, height: 8, background: "#e5e7eb", borderRadius: 4 }}>
                          <div
                            style={{
                              width: `${usedPct}%`,
                              height: "100%",
                              background: usedPct > 80 ? "#dc2626" : usedPct > 50 ? "#f59e0b" : "#10b981",
                              borderRadius: 4,
                            }}
                          />
                        </div>
                        <span style={{ fontSize: 11 }}>{usedPct}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
