import { useCallback, useEffect, useState } from "react";
import {
  DollarSign,
  FileText,
  CreditCard,
  AlertCircle,
  TrendingUp,
  Plus,
  Trash2,
  Receipt,
  Banknote,
  Smartphone,
  Shield,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { apiRequest } from "../services/api";
import { LookupData, Row } from "../types";
import { showToast } from "../components/Toast";
import { buildOptions, firstValue } from "../utils/options";

type TabKey = "dashboard" | "invoices" | "payments" | "tariffs";

const TABS: { key: TabKey; label: string }[] = [
  { key: "dashboard", label: "Tableau de bord" },
  { key: "invoices", label: "Facturation" },
  { key: "payments", label: "Paiements" },
  { key: "tariffs", label: "Tarifs" },
];

const TARIFF_CATEGORY_OPTIONS = [
  { value: "", label: "Toutes catégories" },
  { value: "CONSULTATION", label: "Consultation" },
  { value: "LABORATORY", label: "Laboratoire" },
  { value: "IMAGING", label: "Imagerie" },
  { value: "PHARMACY", label: "Pharmacie" },
  { value: "SURGERY", label: "Chirurgie" },
  { value: "HOSPITALIZATION", label: "Hospitalisation" },
  { value: "EMERGENCY", label: "Urgences" },
  { value: "MATERNITY", label: "Maternité" },
  { value: "OTHER", label: "Autre" },
];

const PAYMENT_METHOD_OPTIONS = [
  { value: "CASH", label: "Espèces", icon: Banknote },
  { value: "MOBILE_MONEY", label: "Mobile Money", icon: Smartphone },
  { value: "CARD", label: "Carte bancaire", icon: CreditCard },
  { value: "INSURANCE", label: "Assurance", icon: Shield },
];

const INVOICE_STATUS_MAP: Record<string, { label: string; badge: string }> = {
  DRAFT: { label: "Brouillon", badge: "badge-gray" },
  ISSUED: { label: "Émise", badge: "badge-blue" },
  PAID: { label: "Payée", badge: "badge-green" },
  PARTIALLY_PAID: { label: "Partiellement payée", badge: "badge-yellow" },
  CANCELLED: { label: "Annulée", badge: "badge-red" },
};

const MOCK_REVENUE_30D = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (29 - i));
  return {
    date: date.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" }),
    revenus: Math.floor(Math.random() * 3000000) + 500000,
  };
});

const MOCK_SERVICE_DISTRIBUTION = [
  { name: "Consultation", value: 2850000 },
  { name: "Laboratoire", value: 1920000 },
  { name: "Imagerie", value: 1450000 },
  { name: "Pharmacie", value: 980000 },
  { name: "Chirurgie", value: 3200000 },
  { name: "Hospitalisation", value: 2100000 },
];

const BAR_COLORS = ["#0f6b3e", "#16a34a", "#22c55e", "#4ade80", "#86efac", "#bbf7d0"];

export function FinancePage({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");

  return (
    <section>
      <h1>Facturation &amp; Finance</h1>
      <p className="muted">
        Gestion de la facturation, des paiements et des tarifs.
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

      {activeTab === "dashboard" && <DashboardTab lookups={lookups} />}
      {activeTab === "invoices" && (
        <InvoicesTab lookups={lookups} onCreated={onCreated} />
      )}
      {activeTab === "payments" && (
        <PaymentsTab lookups={lookups} onCreated={onCreated} />
      )}
      {activeTab === "tariffs" && (
        <TariffsTab lookups={lookups} onCreated={onCreated} />
      )}
    </section>
  );
}

/* ═════════════════════════════════════════════════════════════════
   Dashboard Tab
   ═════════════════════════════════════════════════════════════════ */

function DashboardTab({ lookups }: { lookups: LookupData }) {
  const [invoices, setInvoices] = useState<Row[]>([]);
  const [payments, setPayments] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [invoicesRes, paymentsRes] = await Promise.all([
        apiRequest<any>("/billing/invoices?page_size=1000"),
        apiRequest<any>("/billing/payments?page_size=1000"),
      ]);
      setInvoices(Array.isArray(invoicesRes.data) ? invoicesRes.data : []);
      setPayments(Array.isArray(paymentsRes.data) ? paymentsRes.data : []);
    } catch {
      /* silent */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const handler = () => loadData();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadData]);

  // KPIs
  const today = new Date().toDateString();
  const todayPayments = payments.filter(
    (p) => p.received_at && new Date(p.received_at).toDateString() === today
  );
  const todayRevenue = todayPayments.reduce((sum, p) => sum + (p.amount || 0), 0);

  const pendingInvoices = invoices.filter(
    (inv) => inv.status === "ISSUED" || inv.status === "PARTIALLY_PAID"
  ).length;

  const totalUnpaid = invoices
    .filter((inv) => inv.status !== "PAID" && inv.status !== "CANCELLED")
    .reduce((sum, inv) => sum + (inv.balance_due || 0), 0);

  const recentInvoices = invoices.slice(0, 5);

  if (loading) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "32px" }}>
        <div className="spinner" />
        <p className="muted" style={{ marginTop: "12px" }}>
          Chargement du tableau de bord...
        </p>
      </div>
    );
  }

  return (
    <>
      {/* KPI Cards */}
      <div className="kpi-row">
        <div className="kpi-card">
          <div
            className="kpi-card-icon"
            style={{ background: "var(--success-light)", color: "var(--success)" }}
          >
            <DollarSign size={22} />
          </div>
          <div className="kpi-card-content">
            <div className="kpi-card-value" style={{ fontSize: "22px" }}>
              {todayRevenue.toLocaleString("fr-FR")} GNF
            </div>
            <div className="kpi-card-title">CA du jour</div>
          </div>
        </div>
        <div className="kpi-card">
          <div
            className="kpi-card-icon"
            style={{ background: "var(--warning-light)", color: "var(--warning)" }}
          >
            <FileText size={22} />
          </div>
          <div className="kpi-card-content">
            <div className="kpi-card-value" style={{ color: "var(--warning)" }}>
              {pendingInvoices}
            </div>
            <div className="kpi-card-title">Factures en attente</div>
          </div>
        </div>
        <div className="kpi-card">
          <div
            className="kpi-card-icon"
            style={{ background: "var(--info-light)", color: "var(--info)" }}
          >
            <CreditCard size={22} />
          </div>
          <div className="kpi-card-content">
            <div className="kpi-card-value" style={{ color: "var(--info)" }}>
              {todayPayments.length}
            </div>
            <div className="kpi-card-title">Paiements reçus aujourd'hui</div>
          </div>
        </div>
        <div className="kpi-card">
          <div
            className="kpi-card-icon"
            style={{ background: "var(--danger-light)", color: "var(--danger)" }}
          >
            <AlertCircle size={22} />
          </div>
          <div className="kpi-card-content">
            <div className="kpi-card-value" style={{ color: "var(--danger)", fontSize: "22px" }}>
              {totalUnpaid.toLocaleString("fr-FR")} GNF
            </div>
            <div className="kpi-card-title">Impayés</div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="dashboard-charts-row">
        {/* Line Chart — Revenue 30d */}
        <div className="card chart-container">
          <div className="chart-header">
            <h3 className="chart-title">
              <TrendingUp size={16} />
              Revenus 30 derniers jours
            </h3>
          </div>
          <div className="chart-body" style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={MOCK_REVENUE_30D}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11 }}
                  interval={4}
                />
                <YAxis
                  tickFormatter={(v: number) => `${(v / 1000000).toFixed(1)}M`}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip
                  formatter={(value: any) =>
                    [`${Number(value).toLocaleString("fr-FR")} GNF`, "Revenus"]
                  }
                />
                <Line
                  type="monotone"
                  dataKey="revenus"
                  stroke="#0f6b3e"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bar Chart — Service distribution */}
        <div className="card chart-container">
          <div className="chart-header">
            <h3 className="chart-title">
              <DollarSign size={16} />
              Répartition par service
            </h3>
          </div>
          <div className="chart-body" style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MOCK_SERVICE_DISTRIBUTION} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  type="number"
                  tickFormatter={(v: number) => `${(v / 1000000).toFixed(1)}M`}
                  tick={{ fontSize: 11 }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={110}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip
                  formatter={(value: any) =>
                    [`${Number(value).toLocaleString("fr-FR")} GNF`, "Montant"]
                  }
                />
                <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                  {MOCK_SERVICE_DISTRIBUTION.map((_entry, index) => (
                    <Cell
                      key={index}
                      fill={BAR_COLORS[index % BAR_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Invoices Table */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
          <h3 style={{ fontSize: "15px" }}>Dernières factures</h3>
        </div>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>N° Facture</th>
                <th>Patient</th>
                <th>Date</th>
                <th style={{ textAlign: "right" }}>Montant</th>
                <th style={{ textAlign: "right" }}>Solde dû</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {recentInvoices.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: "center", padding: "24px" }}>
                    <span className="muted">Aucune facture récente.</span>
                  </td>
                </tr>
              ) : (
                recentInvoices.map((inv) => {
                  const statusCfg = INVOICE_STATUS_MAP[inv.status] || {
                    label: inv.status,
                    badge: "badge-gray",
                  };
                  const patient = lookups.patients.find(
                    (p) => p.id === inv.patient_id
                  );
                  return (
                    <tr key={inv.id}>
                      <td style={{ fontWeight: 700, fontFamily: "monospace" }}>
                        {inv.invoice_number}
                      </td>
                      <td style={{ fontWeight: 600 }}>
                        {patient
                          ? `${patient.first_name || ""} ${patient.last_name || ""}`.trim()
                          : inv.patient_id}
                      </td>
                      <td style={{ whiteSpace: "nowrap" }}>
                        {inv.created_at
                          ? new Date(inv.created_at).toLocaleDateString("fr-FR")
                          : "—"}
                      </td>
                      <td style={{ textAlign: "right", fontWeight: 700 }}>
                        {(inv.net_amount || 0).toLocaleString("fr-FR")} GNF
                      </td>
                      <td
                        style={{
                          textAlign: "right",
                          fontWeight: 600,
                          color:
                            inv.balance_due > 0 ? "var(--danger)" : "var(--success)",
                        }}
                      >
                        {(inv.balance_due || 0).toLocaleString("fr-FR")} GNF
                      </td>
                      <td>
                        <span className={`badge ${statusCfg.badge}`}>
                          {statusCfg.label}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

/* ═════════════════════════════════════════════════════════════════
   Invoices Tab
   ═════════════════════════════════════════════════════════════════ */

interface InvoiceLine {
  id: string;
  tariff_item_id: string;
  quantity: number;
  unit_price: number;
}

function InvoicesTab({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  const [invoices, setInvoices] = useState<Row[]>([]);
  const [tariffs, setTariffs] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form fields
  const [patientId, setPatientId] = useState("");
  const [invoiceLines, setInvoiceLines] = useState<InvoiceLine[]>([]);
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [description, setDescription] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [invoicesRes, tariffsRes] = await Promise.all([
        apiRequest<any>("/billing/invoices?page_size=1000"),
        apiRequest<any>("/billing/tariffs?page_size=1000"),
      ]);
      setInvoices(Array.isArray(invoicesRes.data) ? invoicesRes.data : []);
      setTariffs(Array.isArray(tariffsRes.data) ? tariffsRes.data : []);
    } catch {
      showToast("Erreur de chargement des factures.", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const handler = () => loadData();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadData]);

  function addLine() {
    setInvoiceLines([
      ...invoiceLines,
      { id: `line-${Date.now()}`, tariff_item_id: "", quantity: 1, unit_price: 0 },
    ]);
  }

  function removeLine(lineId: string) {
    setInvoiceLines(invoiceLines.filter((l) => l.id !== lineId));
  }

  function updateLine(
    lineId: string,
    field: "tariff_item_id" | "quantity",
    value: string | number
  ) {
    setInvoiceLines(
      invoiceLines.map((l) => {
        if (l.id !== lineId) return l;
        if (field === "tariff_item_id") {
          const tariff = tariffs.find((t) => t.id === value);
          return {
            ...l,
            tariff_item_id: value as string,
            unit_price: tariff?.unit_price || 0,
          };
        }
        return { ...l, quantity: Number(value) || 1 };
      })
    );
  }

  const totalAmount = invoiceLines.reduce(
    (sum, l) => sum + l.unit_price * l.quantity,
    0
  );

  function generateInvoiceNumber(): string {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const seq = String(invoices.length + 1).padStart(4, "0");
    return `FAC-${y}${m}-${seq}`;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!patientId || invoiceLines.length === 0) {
      showToast("Veuillez sélectionner un patient et ajouter au moins une ligne.", "error");
      return;
    }
    const invalidLines = invoiceLines.filter(
      (l) => !l.tariff_item_id || l.quantity <= 0
    );
    if (invalidLines.length > 0) {
      showToast("Veuillez remplir toutes les lignes de facturation.", "error");
      return;
    }

    setSubmitting(true);
    try {
      const invNum = invoiceNumber || generateInvoiceNumber();
      await apiRequest("/billing/invoices", {
        method: "POST",
        body: JSON.stringify({
          facility_id: facilityId,
          patient_id: patientId,
          invoice_number: invNum,
          description: description || undefined,
          net_amount: totalAmount,
        }),
      });
      showToast("Facture créée avec succès.", "success");
      setPatientId("");
      setInvoiceLines([]);
      setInvoiceNumber("");
      setDescription("");
      setShowForm(false);
      onCreated();
      loadData();
    } catch (err: any) {
      showToast(err.message || "Erreur lors de la création.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const tariffOptions = tariffs.map((t) => ({
    value: t.id,
    label: `${t.code} — ${t.name} (${(t.unit_price || 0).toLocaleString("fr-FR")} GNF)`,
  }));

  function getPatientName(patientId: string): string {
    const pat = lookups.patients.find((p) => p.id === patientId);
    return pat
      ? `${pat.first_name || ""} ${pat.last_name || ""}`.trim() || patientId
      : patientId;
  }

  return (
    <>
      <div className="section-header">
        <h2>Facturation</h2>
        <button
          className="primary-button"
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
          onClick={() => {
            setShowForm(!showForm);
            if (!showForm) setInvoiceNumber(generateInvoiceNumber());
          }}
        >
          <Plus size={16} />
          {showForm ? "Annuler" : "Nouvelle facture"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3 style={{ marginBottom: "16px" }}>Nouvelle facture</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <label className="form-control">
                Patient *
                <select
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  required
                >
                  <option value="">— Choisir un patient —</option>
                  {options.patients.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-control">
                N° Facture
                <input
                  type="text"
                  value={invoiceNumber}
                  onChange={(e) => setInvoiceNumber(e.target.value)}
                  placeholder="Auto-généré si vide"
                />
              </label>
            </div>
            <label className="form-control" style={{ marginTop: "8px" }}>
              Description
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Description de la facture"
              />
            </label>

            {/* Invoice Lines */}
            <div style={{ marginTop: "16px", marginBottom: "16px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "8px",
                }}
              >
                <strong style={{ fontSize: "14px" }}>Lignes de facturation</strong>
                <button
                  type="button"
                  className="secondary-button"
                  style={{ padding: "6px 12px", fontSize: "13px", display: "flex", alignItems: "center", gap: "4px" }}
                  onClick={addLine}
                >
                  <Plus size={14} /> Ajouter ligne
                </button>
              </div>

              {invoiceLines.length === 0 && (
                <p className="muted" style={{ fontSize: "13px" }}>
                  Aucune ligne ajoutée. Cliquez sur "Ajouter ligne" pour commencer.
                </p>
              )}

              {invoiceLines.map((line) => (
                <div
                  key={line.id}
                  style={{
                    display: "flex",
                    gap: "12px",
                    alignItems: "center",
                    marginBottom: "8px",
                    padding: "8px 12px",
                    background: "var(--bg)",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid var(--border-light)",
                  }}
                >
                  <select
                    value={line.tariff_item_id}
                    onChange={(e) =>
                      updateLine(line.id, "tariff_item_id", e.target.value)
                    }
                    style={{ flex: 2 }}
                    required
                  >
                    <option value="">— Article tarifaire —</option>
                    {tariffOptions.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                  <input
                    type="number"
                    min={1}
                    value={line.quantity}
                    onChange={(e) =>
                      updateLine(line.id, "quantity", parseInt(e.target.value) || 1)
                    }
                    style={{ flex: 0.4, minWidth: "70px" }}
                    required
                  />
                  <span
                    style={{
                      fontWeight: 600,
                      fontSize: "13px",
                      minWidth: "120px",
                      textAlign: "right",
                    }}
                  >
                    {(line.unit_price * line.quantity).toLocaleString("fr-FR")} GNF
                  </span>
                  <button
                    type="button"
                    onClick={() => removeLine(line.id)}
                    style={{
                      border: "none",
                      background: "transparent",
                      color: "var(--danger)",
                      cursor: "pointer",
                      padding: "4px",
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}

              {invoiceLines.length > 0 && (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    padding: "12px 12px 0",
                    borderTop: "2px solid var(--border)",
                    marginTop: "8px",
                  }}
                >
                  <span style={{ fontWeight: 700, fontSize: "16px" }}>
                    Total : {totalAmount.toLocaleString("fr-FR")} GNF
                  </span>
                </div>
              )}
            </div>

            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer la facture"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : (
        <div className="card" style={{ marginTop: showForm ? "16px" : 0, padding: 0, overflow: "hidden" }}>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>N° Facture</th>
                  <th>Patient</th>
                  <th>Date</th>
                  <th style={{ textAlign: "right" }}>Montant</th>
                  <th style={{ textAlign: "right" }}>Payé</th>
                  <th style={{ textAlign: "right" }}>Solde dû</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {invoices.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: "center", padding: "24px" }}>
                      <span className="muted">Aucune facture enregistrée.</span>
                    </td>
                  </tr>
                ) : (
                  invoices.map((inv) => {
                    const statusCfg = INVOICE_STATUS_MAP[inv.status] || {
                      label: inv.status,
                      badge: "badge-gray",
                    };
                    return (
                      <tr key={inv.id}>
                        <td style={{ fontWeight: 700, fontFamily: "monospace" }}>
                          {inv.invoice_number}
                        </td>
                        <td style={{ fontWeight: 600 }}>
                          {getPatientName(inv.patient_id)}
                        </td>
                        <td style={{ whiteSpace: "nowrap" }}>
                          {inv.created_at
                            ? new Date(inv.created_at).toLocaleDateString("fr-FR")
                            : "—"}
                        </td>
                        <td style={{ textAlign: "right", fontWeight: 700 }}>
                          {(inv.net_amount || 0).toLocaleString("fr-FR")} GNF
                        </td>
                        <td style={{ textAlign: "right" }}>
                          {(inv.paid_amount || 0).toLocaleString("fr-FR")} GNF
                        </td>
                        <td
                          style={{
                            textAlign: "right",
                            fontWeight: 600,
                            color:
                              inv.balance_due > 0
                                ? "var(--danger)"
                                : "var(--success)",
                          }}
                        >
                          {(inv.balance_due || 0).toLocaleString("fr-FR")} GNF
                        </td>
                        <td>
                          <span className={`badge ${statusCfg.badge}`}>
                            {statusCfg.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}

/* ═════════════════════════════════════════════════════════════════
   Payments Tab
   ═════════════════════════════════════════════════════════════════ */

function PaymentsTab({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  const [payments, setPayments] = useState<Row[]>([]);
  const [invoices, setInvoices] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form fields
  const [invoiceId, setInvoiceId] = useState("");
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("CASH");
  const [reference, setReference] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [paymentsRes, invoicesRes] = await Promise.all([
        apiRequest<any>("/billing/payments?page_size=1000"),
        apiRequest<any>("/billing/invoices?page_size=1000"),
      ]);
      setPayments(Array.isArray(paymentsRes.data) ? paymentsRes.data : []);
      setInvoices(Array.isArray(invoicesRes.data) ? invoicesRes.data : []);
    } catch {
      showToast("Erreur de chargement des paiements.", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const handler = () => loadData();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadData]);

  // Unpaid/partially paid invoices for selection
  const unpaidInvoices = invoices.filter(
    (inv) =>
      inv.status === "ISSUED" ||
      inv.status === "PARTIALLY_PAID" ||
      inv.status === "DRAFT"
  );

  const invoiceOptions = unpaidInvoices.map((inv) => {
    const patient = lookups.patients.find((p) => p.id === inv.patient_id);
    return {
      value: inv.id,
      label: `${inv.invoice_number} — ${patient ? `${patient.first_name} ${patient.last_name}` : inv.patient_id} — Solde: ${(inv.balance_due || 0).toLocaleString("fr-FR")} GNF`,
    };
  });

  // Auto-fill amount when invoice is selected
  function handleInvoiceChange(invId: string) {
    setInvoiceId(invId);
    const inv = invoices.find((i) => i.id === invId);
    if (inv && inv.balance_due > 0) {
      setAmount(String(inv.balance_due));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!invoiceId || !amount || parseFloat(amount) <= 0) {
      showToast("Veuillez sélectionner une facture et saisir un montant.", "error");
      return;
    }
    setSubmitting(true);
    try {
      await apiRequest(`/billing/invoices/${invoiceId}/payments`, {
        method: "POST",
        body: JSON.stringify({
          facility_id: facilityId,
          amount: parseFloat(amount),
          payment_method: method,
        }),
      });
      showToast("Paiement enregistré avec succès.", "success");
      setInvoiceId("");
      setAmount("");
      setMethod("CASH");
      setReference("");
      setShowForm(false);
      onCreated();
      loadData();
    } catch (err: any) {
      showToast(err.message || "Erreur lors du paiement.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  function getPatientName(patientId: string): string {
    const pat = lookups.patients.find((p) => p.id === patientId);
    return pat
      ? `${pat.first_name || ""} ${pat.last_name || ""}`.trim() || patientId
      : patientId;
  }

  function getInvoicePatient(invoiceId: string): string {
    const inv = invoices.find((i) => i.id === invoiceId);
    if (!inv) return "—";
    return getPatientName(inv.patient_id);
  }

  const methodLabel: Record<string, string> = {};
  PAYMENT_METHOD_OPTIONS.forEach((o) => {
    methodLabel[o.value] = o.label;
  });

  return (
    <>
      <div className="section-header">
        <h2>Paiements</h2>
        <button
          className="primary-button"
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
          onClick={() => setShowForm(!showForm)}
        >
          <Plus size={16} />
          {showForm ? "Annuler" : "Enregistrer un paiement"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3 style={{ marginBottom: "16px" }}>Enregistrer un paiement</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <label className="form-control">
                Facture *
                <select
                  value={invoiceId}
                  onChange={(e) => handleInvoiceChange(e.target.value)}
                  required
                >
                  <option value="">— Choisir une facture —</option>
                  {invoiceOptions.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-control">
                Montant (GNF) *
                <input
                  type="number"
                  min={1}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0"
                  required
                />
              </label>
              <label className="form-control">
                Mode de paiement
                <select
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
                >
                  {PAYMENT_METHOD_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-control">
                Référence
                <input
                  type="text"
                  value={reference}
                  onChange={(e) => setReference(e.target.value)}
                  placeholder="N° de transaction"
                />
              </label>
            </div>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Enregistrement..." : "Enregistrer le paiement"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : (
        <div className="card" style={{ marginTop: showForm ? "16px" : 0, padding: 0, overflow: "hidden" }}>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Patient</th>
                  <th style={{ textAlign: "right" }}>Montant</th>
                  <th>Mode</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {payments.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: "center", padding: "24px" }}>
                      <span className="muted">Aucun paiement enregistré.</span>
                    </td>
                  </tr>
                ) : (
                  payments.map((p) => (
                    <tr key={p.id}>
                      <td style={{ whiteSpace: "nowrap" }}>
                        {p.received_at
                          ? new Date(p.received_at).toLocaleString("fr-FR")
                          : "—"}
                      </td>
                      <td style={{ fontWeight: 600 }}>
                        {getInvoicePatient(p.invoice_id)}
                      </td>
                      <td style={{ textAlign: "right", fontWeight: 700 }}>
                        {(p.amount || 0).toLocaleString("fr-FR")} GNF
                      </td>
                      <td>
                        <span className="badge badge-gray">
                          {methodLabel[p.payment_method] || p.payment_method || "—"}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            p.status === "COMPLETED"
                              ? "badge-green"
                              : "badge-yellow"
                          }`}
                        >
                          {p.status === "COMPLETED" ? "Complété" : p.status || "—"}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}

/* ═════════════════════════════════════════════════════════════════
   Tariffs Tab
   ═════════════════════════════════════════════════════════════════ */

function TariffsTab({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  const [tariffs, setTariffs] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form fields
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("CONSULTATION");
  const [unitPrice, setUnitPrice] = useState("");

  const loadTariffs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiRequest<any>("/billing/tariffs?page_size=1000");
      setTariffs(Array.isArray(res.data) ? res.data : []);
    } catch {
      showToast("Erreur de chargement des tarifs.", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTariffs();
    const handler = () => loadTariffs();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadTariffs]);

  function resetForm() {
    setCode("");
    setName("");
    setCategory("CONSULTATION");
    setUnitPrice("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!code || !name || !unitPrice) {
      showToast("Tous les champs sont obligatoires.", "error");
      return;
    }
    setSubmitting(true);
    try {
      await apiRequest("/billing/tariffs", {
        method: "POST",
        body: JSON.stringify({
          facility_id: facilityId,
          code,
          name,
          category,
          unit_price: parseFloat(unitPrice),
        }),
      });
      showToast("Tarif créé avec succès.", "success");
      resetForm();
      setShowForm(false);
      onCreated();
      loadTariffs();
    } catch (err: any) {
      showToast(err.message || "Erreur lors de la création.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const categoryLabel: Record<string, string> = {};
  TARIFF_CATEGORY_OPTIONS.forEach((o) => {
    categoryLabel[o.value] = o.label;
  });

  return (
    <>
      <div className="section-header">
        <h2>Catalogue des tarifs</h2>
        <button
          className="primary-button"
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
          onClick={() => setShowForm(!showForm)}
        >
          <Plus size={16} />
          {showForm ? "Annuler" : "Nouveau tarif"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3 style={{ marginBottom: "16px" }}>Nouveau tarif</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <label className="form-control">
                Code *
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Ex: CONS001"
                  required
                />
              </label>
              <label className="form-control">
                Nom *
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ex: Consultation générale"
                  required
                />
              </label>
              <label className="form-control">
                Catégorie
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  {TARIFF_CATEGORY_OPTIONS.filter((o) => o.value).map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-control">
                Prix unitaire (GNF) *
                <input
                  type="number"
                  min={0}
                  value={unitPrice}
                  onChange={(e) => setUnitPrice(e.target.value)}
                  placeholder="0"
                  required
                />
              </label>
            </div>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer le tarif"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : (
        <div className="card" style={{ marginTop: showForm ? "16px" : 0, padding: 0, overflow: "hidden" }}>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Nom</th>
                  <th>Catégorie</th>
                  <th style={{ textAlign: "right" }}>Prix unitaire</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {tariffs.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: "center", padding: "24px" }}>
                      <span className="muted">Aucun tarif enregistré.</span>
                    </td>
                  </tr>
                ) : (
                  tariffs.map((t) => (
                    <tr key={t.id}>
                      <td style={{ fontWeight: 700, fontFamily: "monospace" }}>
                        {t.code}
                      </td>
                      <td style={{ fontWeight: 600 }}>{t.name}</td>
                      <td>
                        <span className="badge badge-gray">
                          {categoryLabel[t.category] || t.category || "—"}
                        </span>
                      </td>
                      <td style={{ textAlign: "right", fontWeight: 700 }}>
                        {(t.unit_price || 0).toLocaleString("fr-FR")} GNF
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            t.status === "ACTIVE" ? "badge-green" : "badge-gray"
                          }`}
                        >
                          {t.status === "ACTIVE" ? "Actif" : t.status || "—"}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
