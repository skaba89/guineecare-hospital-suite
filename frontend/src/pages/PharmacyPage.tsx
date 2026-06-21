import { useCallback, useEffect, useState } from "react";
import {
  Package,
  Pill,
  AlertTriangle,
  TrendingUp,
  Plus,
  ShoppingCart,
  ArrowDownCircle,
  ArrowUpCircle,
  CheckCircle2,
  XCircle,
  Trash2,
} from "lucide-react";
import {
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
import { usePaginatedList } from "../hooks/usePaginatedList";
import { Pagination } from "../components/Pagination";

type TabKey = "stock" | "dispensation" | "products" | "movements";

const TABS: { key: TabKey; label: string }[] = [
  { key: "stock", label: "Stock" },
  { key: "dispensation", label: "Dispensation" },
  { key: "products", label: "Produits" },
  { key: "movements", label: "Mouvements" },
];

const CATEGORY_OPTIONS = [
  { value: "", label: "Toutes catégories" },
  { value: "ANTALGIC", label: "Antalgique" },
  { value: "ANTIBIOTIC", label: "Antibiotique" },
  { value: "ANTIVIRAL", label: "Antiviral" },
  { value: "ANTIPARASITIC", label: "Antiparasitaire" },
  { value: "ANTIHYPERTENSIVE", label: "Antihypertenseur" },
  { value: "ANTIDIABETIC", label: "Antidiabétique" },
  { value: "ANTIINFLAMMATORY", label: "Anti-inflammatoire" },
  { value: "ANTIHISTAMINE", label: "Antihistaminique" },
  { value: "BRONCHODILATOR", label: "Bronchodilatateur" },
  { value: "DIURETIC", label: "Diurétique" },
  { value: "VITAMIN", label: "Vitamine" },
  { value: "VACCINE", label: "Vaccin" },
  { value: "OTHER", label: "Autre" },
];

const FORM_OPTIONS = [
  { value: "TABLET", label: "Comprimé" },
  { value: "CAPSULE", label: "Gélule" },
  { value: "SYRUP", label: "Sirop" },
  { value: "INJECTION", label: "Injection" },
  { value: "CREAM", label: "Crème" },
  { value: "OINTMENT", label: "Pommade" },
  { value: "DROPS", label: "Gouttes" },
  { value: "SUPPOSITORY", label: "Suppositoire" },
  { value: "POWDER", label: "Poudre" },
  { value: "SUSPENSION", label: "Suspension" },
];

const MOCK_TOP_DISPENSED = [
  { name: "Paracétamol", value: 342 },
  { name: "Amoxicilline", value: 218 },
  { name: "Métronidazole", value: 176 },
  { name: "Cotrimoxazole", value: 154 },
  { name: "Ibuprofène", value: 129 },
];

const BAR_COLORS = ["#0f6b3e", "#16a34a", "#22c55e", "#4ade80", "#86efac"];

export function PharmacyPage({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const [activeTab, setActiveTab] = useState<TabKey>("stock");

  return (
    <section>
      <h1>Pharmacie</h1>
      <p className="muted">
        Gestion des stocks, dispensation et mouvements pharmaceutiques.
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

      {activeTab === "stock" && <StockTab lookups={lookups} />}
      {activeTab === "dispensation" && (
        <DispensationTab lookups={lookups} onCreated={onCreated} />
      )}
      {activeTab === "products" && (
        <ProductsTab lookups={lookups} onCreated={onCreated} />
      )}
      {activeTab === "movements" && (
        <MovementsTab lookups={lookups} onCreated={onCreated} />
      )}
    </section>
  );
}

/* ═════════════════════════════════════════════════════════════════
   Stock Tab
   ═════════════════════════════════════════════════════════════════ */

function StockTab({ lookups }: { lookups: LookupData }) {
  // Référence produits (petite table) pour l'enrichissement + KPIs
  const [products, setProducts] = useState<Row[]>([]);
  const [categoryFilter, setCategoryFilter] = useState("");

  // Liste paginée des stocks (recherche server-side + debounce 300ms)
  const {
    items: stock,
    total,
    page,
    totalPages,
    loading,
    error,
    search,
    setSearch,
    setPage,
    reload,
  } = usePaginatedList<Row>("/pharmacy/stock", {
    pageSize: 20,
    debounceMs: 300,
  });

  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  // Charger les produits (petite table de référence) une seule fois
  useEffect(() => {
    async function loadProducts() {
      try {
        const res = await apiRequest<any>("/pharmacy/products?page_size=1000");
        setProducts(Array.isArray(res.data) ? res.data : []);
      } catch {
        // silent — KPIs ne seront pas bloqués
      }
    }
    loadProducts();
  }, []);

  // Réagir aux refresh globaux (création d'mouvement ailleurs)
  useEffect(() => {
    const handler = () => reload();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [reload]);

  // Build enriched stock items by merging stock with product info
  const enrichedStock: Row[] = stock.map((s) => {
    const prod = products.find((p: Row) => p.id === s.product_id) || {};
    return { ...s, ...prod, product_name: prod.name, product_code: prod.code };
  });

  // Filtre catégorie appliqué côté client (le backend ne supporte pas category sur /stock)
  const filtered = categoryFilter
    ? enrichedStock.filter((item: Row) => item.category === categoryFilter)
    : enrichedStock;

  // KPIs
  const totalProducts = products.length;
  const totalUnits = stock.reduce(
    (sum, s) => sum + (s.quantity_available || 0),
    0
  );
  const lowStockCount = stock.filter(
    (s) =>
      s.quantity_available > 0 &&
      s.quantity_available <= (s.min_threshold || 0)
  ).length;
  const emptyStockCount = stock.filter(
    (s) => s.quantity_available === 0
  ).length;
  const alertCount = lowStockCount + emptyStockCount;
  const estimatedValue = stock.reduce(
    (sum, s) => sum + (s.quantity_available || 0) * 1500,
    0
  );

  function getStockStatus(item: Row): string {
    const qty = Number(item.quantity_available) || 0;
    const threshold = Number(item.min_threshold) || 0;
    if (qty === 0) return "epuise";
    if (qty <= threshold) return "bas";
    return "ok";
  }

  return (
    <>
      {/* KPI Cards */}
      <div className="kpi-row">
        <div className="kpi-card">
          <div
            className="kpi-card-icon"
            style={{ background: "var(--primary-light)", color: "var(--primary)" }}
          >
            <Package size={22} />
          </div>
          <div className="kpi-card-content">
            <div className="kpi-card-value">{totalProducts}</div>
            <div className="kpi-card-title">Total produits</div>
          </div>
        </div>
        <div className="kpi-card">
          <div
            className="kpi-card-icon"
            style={{ background: "var(--info-light)", color: "var(--info)" }}
          >
            <Pill size={22} />
          </div>
          <div className="kpi-card-content">
            <div className="kpi-card-value">{totalUnits.toLocaleString("fr-FR")}</div>
            <div className="kpi-card-title">Stock total unités</div>
          </div>
        </div>
        <div className="kpi-card">
          <div
            className="kpi-card-icon"
            style={{ background: "var(--danger-light)", color: "var(--danger)" }}
          >
            <AlertTriangle size={22} />
          </div>
          <div className="kpi-card-content">
            <div className="kpi-card-value" style={{ color: "var(--danger)" }}>
              {alertCount}
            </div>
            <div className="kpi-card-title">Alertes stock bas</div>
          </div>
        </div>
        <div className="kpi-card">
          <div
            className="kpi-card-icon"
            style={{ background: "var(--success-light)", color: "var(--success)" }}
          >
            <TrendingUp size={22} />
          </div>
          <div className="kpi-card-content">
            <div className="kpi-card-value">
              {estimatedValue.toLocaleString("fr-FR")} GNF
            </div>
            <div className="kpi-card-title">Valeur stock estimée</div>
          </div>
        </div>
      </div>

      {/* Barre de recherche + filtre catégorie (recherche server-side, debounce 300ms) */}
      <div
        style={{
          display: "flex",
          gap: 12,
          alignItems: "center",
          marginBottom: 12,
          flexWrap: "wrap",
        }}
      >
        <input
          type="text"
          placeholder="🔍 Rechercher un produit..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: 250, padding: "8px 12px" }}
        />
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          style={{ padding: "8px 12px", minWidth: 180 }}
        >
          {CATEGORY_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <button
          className="primary-button"
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <ShoppingCart size={16} />
          Commande fournisseur
        </button>
      </div>

      {/* Stock Table */}
      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : error ? (
        <div className="card" style={{ padding: "16px", color: "var(--danger)" }}>
          {error}
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Produit</th>
                  <th>Catégorie</th>
                  <th>Forme</th>
                  <th>Dosage</th>
                  <th style={{ textAlign: "right" }}>Qté dispo</th>
                  <th style={{ textAlign: "right" }}>Seuil min</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={8} style={{ textAlign: "center", padding: "24px" }}>
                      <span className="muted">Aucun produit en stock.</span>
                    </td>
                  </tr>
                ) : (
                  filtered.map((item: Row) => {
                    const status = getStockStatus(item);
                    return (
                      <tr
                        key={item.id}
                        style={{
                          background:
                            status === "epuise"
                              ? "var(--danger-light)"
                              : status === "bas"
                              ? "var(--warning-light)"
                              : "inherit",
                        }}
                      >
                        <td style={{ fontWeight: 600 }}>
                          {item.product_name || item.product_id || "—"}
                          {item.product_code && (
                            <span
                              className="muted"
                              style={{ fontWeight: 400, marginLeft: "8px", fontSize: "12px" }}
                            >
                              ({item.product_code})
                            </span>
                          )}
                        </td>
                        <td>{item.category || "—"}</td>
                        <td>{item.form || "—"}</td>
                        <td>{item.dosage || "—"}</td>
                        <td style={{ textAlign: "right", fontWeight: 700 }}>
                          {item.quantity_available ?? 0}
                        </td>
                        <td style={{ textAlign: "right" }}>
                          {item.min_threshold ?? 0}
                        </td>
                        <td>
                          <span
                            className={`badge ${
                              status === "ok"
                                ? "badge-green"
                                : status === "bas"
                                ? "badge-yellow"
                                : "badge-red"
                            }`}
                          >
                            {status === "ok"
                              ? "OK"
                              : status === "bas"
                              ? "Bas"
                              : "Épuisé"}
                          </span>
                        </td>
                        <td>
                          <button
                            className="secondary-button"
                            style={{ padding: "4px 10px", fontSize: "12px" }}
                            onClick={() =>
                              alert(
                                `Détail produit: ${item.product_name || item.product_id}`
                              )
                            }
                          >
                            Détail
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
          <div style={{ padding: "0 16px" }}>
            <Pagination
              page={page}
              totalPages={totalPages}
              total={total}
              onPageChange={setPage}
              loading={loading}
            />
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="card chart-container" style={{ marginTop: "20px" }}>
        <div className="chart-header">
          <h3 className="chart-title">
            <TrendingUp size={16} />
            Top 5 produits les plus dispensés
          </h3>
        </div>
        <div className="chart-body" style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={MOCK_TOP_DISPENSED} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis type="number" />
              <YAxis
                type="category"
                dataKey="name"
                width={120}
                tick={{ fontSize: 13 }}
              />
              <Tooltip />
              <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                {MOCK_TOP_DISPENSED.map((_entry, index) => (
                  <Cell key={index} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}

/* ═════════════════════════════════════════════════════════════════
   Dispensation Tab
   ═════════════════════════════════════════════════════════════════ */

interface DispensationLine {
  id: string;
  product_id: string;
  quantity: number;
}

function DispensationTab({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);
  const doctors = lookups.staff.filter((s) => s.role === "DOCTOR");
  const doctorOptions = doctors.map((d) => ({
    value: d.id,
    label: `${d.last_name || ""} ${d.first_name || ""} — ${d.role || ""}`.trim(),
  }));

  const [patientId, setPatientId] = useState("");
  const [prescription, setPrescription] = useState("");
  const [prescriberId, setPrescriberId] = useState("");
  const [lines, setLines] = useState<DispensationLine[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const [stock, setStock] = useState<Row[]>([]);
  const [recentDispensations, setRecentDispensations] = useState<Row[]>([]);

  const loadStock = useCallback(async () => {
    try {
      const res = await apiRequest<any>("/pharmacy/stock?page_size=1000");
      setStock(Array.isArray(res.data) ? res.data : []);
    } catch {
      /* silent */
    }
  }, []);

  const loadMovements = useCallback(async () => {
    try {
      const res = await apiRequest<any>("/pharmacy/stock/movements?page_size=1000");
      const movements = Array.isArray(res.data) ? res.data : [];
      setRecentDispensations(movements.filter((m: Row) => m.movement_type === "OUT"));
    } catch {
      /* silent */
    }
  }, []);

  useEffect(() => {
    loadStock();
    loadMovements();
    const handler = () => {
      loadStock();
      loadMovements();
    };
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [loadStock, loadMovements]);

  function addLine() {
    setLines([
      ...lines,
      { id: `line-${Date.now()}`, product_id: "", quantity: 1 },
    ]);
  }

  function removeLine(lineId: string) {
    setLines(lines.filter((l) => l.id !== lineId));
  }

  function updateLine(lineId: string, field: "product_id" | "quantity", value: string | number) {
    setLines(
      lines.map((l) => (l.id === lineId ? { ...l, [field]: value } : l))
    );
  }

  function getStockForProduct(productId: string): number {
    const item = stock.find((s) => s.product_id === productId);
    return item?.quantity_available ?? 0;
  }

  async function handleDispense(e: React.FormEvent) {
    e.preventDefault();
    if (!patientId || lines.length === 0) {
      showToast("Veuillez sélectionner un patient et au moins un produit.", "error");
      return;
    }

    const invalidLines = lines.filter(
      (l) => !l.product_id || l.quantity <= 0
    );
    if (invalidLines.length > 0) {
      showToast("Veuillez remplir toutes les lignes de prescription.", "error");
      return;
    }

    setSubmitting(true);
    try {
      for (const line of lines) {
        await apiRequest("/pharmacy/stock/movements", {
          method: "POST",
          body: JSON.stringify({
            facility_id: facilityId,
            product_id: line.product_id,
            movement_type: "OUT",
            quantity: line.quantity,
            reason: `Dispensation — Patient: ${patientId} — Prescripteur: ${prescriberId || "N/A"} — Ordonnance: ${prescription || "N/A"}`,
          }),
        });
      }
      showToast("Dispensation enregistrée avec succès.", "success");
      setPatientId("");
      setPrescription("");
      setPrescriberId("");
      setLines([]);
      onCreated();
      loadStock();
      loadMovements();
    } catch (err: any) {
      showToast(err.message || "Erreur lors de la dispensation.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      {/* Dispensation Form */}
      <div className="card form-card">
        <h3 style={{ marginBottom: "16px" }}>Nouvelle dispensation</h3>
        <form onSubmit={handleDispense}>
          <div className="form-grid" style={{ marginBottom: "16px" }}>
            <label className="form-control">
              Patient
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
              Prescripteur
              <select
                value={prescriberId}
                onChange={(e) => setPrescriberId(e.target.value)}
              >
                <option value="">— Choisir un médecin —</option>
                {doctorOptions.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="form-control" style={{ marginBottom: "16px" }}>
            Ordonnance
            <textarea
              value={prescription}
              onChange={(e) => setPrescription(e.target.value)}
              placeholder="Détails de l'ordonnance..."
              rows={2}
              style={{
                width: "100%",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-sm)",
                padding: "10px 12px",
                font: "inherit",
                resize: "vertical",
              }}
            />
          </label>

          {/* Prescription Lines */}
          <div style={{ marginBottom: "16px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "8px",
              }}
            >
              <strong style={{ fontSize: "14px" }}>Lignes de prescription</strong>
              <button
                type="button"
                className="secondary-button"
                style={{ padding: "6px 12px", fontSize: "13px", display: "flex", alignItems: "center", gap: "4px" }}
                onClick={addLine}
              >
                <Plus size={14} /> Ajouter ligne
              </button>
            </div>

            {lines.length === 0 && (
              <p className="muted" style={{ fontSize: "13px" }}>
                Aucune ligne ajoutée. Cliquez sur "Ajouter ligne" pour commencer.
              </p>
            )}

            {lines.map((line) => {
              const available = getStockForProduct(line.product_id);
              const hasStock = line.product_id ? available >= line.quantity : true;
              return (
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
                    value={line.product_id}
                    onChange={(e) => updateLine(line.id, "product_id", e.target.value)}
                    style={{ flex: 2 }}
                    required
                  >
                    <option value="">— Produit —</option>
                    {options.products.map((o) => (
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
                    style={{ flex: 0.5, minWidth: "80px" }}
                    required
                  />
                  {line.product_id && (
                    <span
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                        fontSize: "12px",
                        fontWeight: 600,
                        color: hasStock ? "var(--success)" : "var(--danger)",
                      }}
                    >
                      {hasStock ? (
                        <CheckCircle2 size={14} />
                      ) : (
                        <XCircle size={14} />
                      )}
                      Stock: {available}
                    </span>
                  )}
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
              );
            })}
          </div>

          <div className="form-actions">
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? "Dispensation en cours..." : "Valider la dispensation"}
            </button>
          </div>
        </form>
      </div>

      {/* Recent Dispensations */}
      <div className="card" style={{ marginTop: "20px", padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
          <h3 style={{ fontSize: "15px" }}>Dispensations récentes</h3>
        </div>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Produit</th>
                <th>Quantité</th>
                <th>Motif</th>
              </tr>
            </thead>
            <tbody>
              {recentDispensations.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ textAlign: "center", padding: "24px" }}>
                    <span className="muted">Aucune dispensation récente.</span>
                  </td>
                </tr>
              ) : (
                recentDispensations.map((d) => (
                  <tr key={d.id}>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {d.performed_at
                        ? new Date(d.performed_at).toLocaleString("fr-FR")
                        : "—"}
                    </td>
                    <td style={{ fontWeight: 600 }}>{d.product_id}</td>
                    <td>{d.quantity}</td>
                    <td style={{ fontSize: "13px", maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {d.reason || "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

/* ═════════════════════════════════════════════════════════════════
   Products Tab
   ═════════════════════════════════════════════════════════════════ */

function ProductsTab({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState("");

  // Liste paginée des produits (recherche server-side + filtre catégorie + debounce 300ms)
  const {
    items: products,
    total,
    page,
    totalPages,
    loading,
    error,
    search,
    setSearch,
    setPage,
    reload,
  } = usePaginatedList<Row>("/pharmacy/products", {
    pageSize: 20,
    debounceMs: 300,
    extraParams: { category: categoryFilter || null },
  });

  // Form fields
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("ANTALGIC");
  const [form, setForm] = useState("TABLET");
  const [dosage, setDosage] = useState("");
  const [minThreshold, setMinThreshold] = useState("10");

  // Réagir aux refresh globaux (création d'produit ailleurs)
  useEffect(() => {
    const handler = () => reload();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [reload]);

  function resetForm() {
    setCode("");
    setName("");
    setCategory("ANTALGIC");
    setForm("TABLET");
    setDosage("");
    setMinThreshold("10");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!code || !name) {
      showToast("Le code et le nom sont obligatoires.", "error");
      return;
    }
    setSubmitting(true);
    try {
      await apiRequest("/pharmacy/products", {
        method: "POST",
        body: JSON.stringify({
          facility_id: facilityId,
          code,
          name,
          category,
          form,
          dosage: dosage || undefined,
        }),
      });
      showToast("Produit créé avec succès.", "success");
      resetForm();
      setShowForm(false);
      onCreated();
      reload();
    } catch (err: any) {
      showToast(err.message || "Erreur lors de la création.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const categoryLabel: Record<string, string> = {};
  CATEGORY_OPTIONS.forEach((o) => {
    categoryLabel[o.value] = o.label;
  });

  const formLabel: Record<string, string> = {};
  FORM_OPTIONS.forEach((o) => {
    formLabel[o.value] = o.label;
  });

  return (
    <>
      <div className="section-header">
        <h2>Catalogue produits</h2>
        <button
          className="primary-button"
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
          onClick={() => setShowForm(!showForm)}
        >
          <Plus size={16} />
          {showForm ? "Annuler" : "Nouveau produit"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3 style={{ marginBottom: "16px" }}>Nouveau produit</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <label className="form-control">
                Code *
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Ex: PARAC500"
                  required
                />
              </label>
              <label className="form-control">
                Nom *
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ex: Paracétamol 500mg"
                  required
                />
              </label>
              <label className="form-control">
                Catégorie
                <select value={category} onChange={(e) => setCategory(e.target.value)}>
                  {CATEGORY_OPTIONS.filter((o) => o.value).map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-control">
                Forme
                <select value={form} onChange={(e) => setForm(e.target.value)}>
                  {FORM_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-control">
                Dosage
                <input
                  type="text"
                  value={dosage}
                  onChange={(e) => setDosage(e.target.value)}
                  placeholder="Ex: 500mg"
                />
              </label>
              <label className="form-control">
                Seuil minimum
                <input
                  type="number"
                  min={0}
                  value={minThreshold}
                  onChange={(e) => setMinThreshold(e.target.value)}
                />
              </label>
            </div>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Création..." : "Créer le produit"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Barre de recherche + filtre catégorie (server-side, debounce 300ms) */}
      <div
        style={{
          display: "flex",
          gap: 12,
          alignItems: "center",
          marginBottom: 12,
          flexWrap: "wrap",
        }}
      >
        <input
          type="text"
          placeholder="🔍 Rechercher (code, nom)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: 250, padding: "8px 12px" }}
        />
        <select
          value={categoryFilter}
          onChange={(e) => {
            setCategoryFilter(e.target.value);
            setPage(1);
          }}
          style={{ padding: "8px 12px", minWidth: 180 }}
        >
          {CATEGORY_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : error ? (
        <div className="card" style={{ padding: "16px", color: "var(--danger)" }}>
          {error}
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
                  <th>Forme</th>
                  <th>Dosage</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {products.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: "center", padding: "24px" }}>
                      <span className="muted">Aucun produit enregistré.</span>
                    </td>
                  </tr>
                ) : (
                  products.map((p) => (
                    <tr key={p.id}>
                      <td style={{ fontWeight: 700, fontFamily: "monospace" }}>
                        {p.code}
                      </td>
                      <td style={{ fontWeight: 600 }}>{p.name}</td>
                      <td>
                        <span className="badge badge-gray">
                          {categoryLabel[p.category] || p.category || "—"}
                        </span>
                      </td>
                      <td>{formLabel[p.form] || p.form || "—"}</td>
                      <td>{p.dosage || "—"}</td>
                      <td>
                        <span
                          className={`badge ${
                            p.status === "ACTIVE" ? "badge-green" : "badge-gray"
                          }`}
                        >
                          {p.status === "ACTIVE" ? "Actif" : p.status || "—"}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div style={{ padding: "0 16px" }}>
            <Pagination
              page={page}
              totalPages={totalPages}
              total={total}
              onPageChange={setPage}
              loading={loading}
            />
          </div>
        </div>
      )}
    </>
  );
}

/* ═════════════════════════════════════════════════════════════════
   Movements Tab
   ═════════════════════════════════════════════════════════════════ */

function MovementsTab({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const options = buildOptions(lookups);
  const facilityId = firstValue(options.facilities);

  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Liste paginée des mouvements (recherche server-side + filtres type/date + debounce 300ms)
  const {
    items: movements,
    total,
    page,
    totalPages,
    loading,
    error,
    search,
    setSearch,
    setPage,
    reload,
  } = usePaginatedList<Row>("/pharmacy/stock/movements", {
    pageSize: 20,
    debounceMs: 300,
    extraParams: {
      movement_type: typeFilter || null,
      date_from: dateFrom || null,
      date_to: dateTo || null,
    },
  });

  // Form fields for entry
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState("");

  // Réagir aux refresh globaux (création d'mouvement ailleurs)
  useEffect(() => {
    const handler = () => reload();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [reload]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!productId || !quantity || parseInt(quantity) <= 0) {
      showToast("Veuillez remplir tous les champs.", "error");
      return;
    }
    setSubmitting(true);
    try {
      await apiRequest("/pharmacy/stock/movements", {
        method: "POST",
        body: JSON.stringify({
          facility_id: facilityId,
          product_id: productId,
          movement_type: "IN",
          quantity: parseInt(quantity),
          reason: reason || "Entrée de stock",
        }),
      });
      showToast("Entrée de stock enregistrée.", "success");
      setProductId("");
      setQuantity("");
      setReason("");
      setShowForm(false);
      onCreated();
      reload();
    } catch (err: any) {
      showToast(err.message || "Erreur lors de l'entrée.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  // Resolve product name from lookups
  function getProductName(productId: string): string {
    const prod = lookups.products.find((p) => p.id === productId);
    return prod ? `${prod.code} — ${prod.name}` : productId;
  }

  // Resolve staff name from lookups
  function getStaffName(staffId: string): string {
    const s = lookups.staff.find((st) => st.id === staffId);
    return s ? `${s.last_name || ""} ${s.first_name || ""}`.trim() : staffId;
  }

  return (
    <>
      <div className="section-header">
        <h2>Mouvements de stock</h2>
        <button
          className="primary-button"
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
          onClick={() => setShowForm(!showForm)}
        >
          <ArrowDownCircle size={16} />
          {showForm ? "Annuler" : "Nouvelle entrée"}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3 style={{ marginBottom: "16px" }}>Entrée de stock</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <label className="form-control">
                Produit *
                <select
                  value={productId}
                  onChange={(e) => setProductId(e.target.value)}
                  required
                >
                  <option value="">— Choisir un produit —</option>
                  {options.products.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-control">
                Quantité *
                <input
                  type="number"
                  min={1}
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  placeholder="Quantité"
                  required
                />
              </label>
              <label className="form-control">
                Motif
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Ex: Réapprovisionnement"
                />
              </label>
            </div>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Enregistrement..." : "Enregistrer l'entrée"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Barre de recherche + filtres (server-side, debounce 300ms) */}
      <div
        style={{
          display: "flex",
          gap: 12,
          alignItems: "center",
          marginBottom: 12,
          flexWrap: "wrap",
        }}
      >
        <input
          type="text"
          placeholder="🔍 Rechercher (motif, produit)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: 250, padding: "8px 12px" }}
        />
        <select
          value={typeFilter}
          onChange={(e) => {
            setTypeFilter(e.target.value);
            setPage(1);
          }}
          style={{ padding: "8px 12px", minWidth: 140 }}
        >
          <option value="">Tous types</option>
          <option value="IN">Entrée</option>
          <option value="OUT">Sortie</option>
        </select>
        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            fontSize: 13,
            color: "var(--muted)",
          }}
        >
          Du
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => {
              setDateFrom(e.target.value);
              setPage(1);
            }}
            style={{ padding: "8px 12px" }}
          />
        </label>
        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            fontSize: 13,
            color: "var(--muted)",
          }}
        >
          Au
          <input
            type="date"
            value={dateTo}
            onChange={(e) => {
              setDateTo(e.target.value);
              setPage(1);
            }}
            style={{ padding: "8px 12px" }}
          />
        </label>
      </div>

      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "32px" }}>
          <div className="spinner" />
        </div>
      ) : error ? (
        <div className="card" style={{ padding: "16px", color: "var(--danger)" }}>
          {error}
        </div>
      ) : (
        <div className="card" style={{ marginTop: showForm ? "16px" : 0, padding: 0, overflow: "hidden" }}>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Produit</th>
                  <th>Type</th>
                  <th style={{ textAlign: "right" }}>Quantité</th>
                  <th>Motif</th>
                  <th>Responsable</th>
                </tr>
              </thead>
              <tbody>
                {movements.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: "center", padding: "24px" }}>
                      <span className="muted">Aucun mouvement enregistré.</span>
                    </td>
                  </tr>
                ) : (
                  movements.map((m) => (
                    <tr key={m.id}>
                      <td style={{ whiteSpace: "nowrap" }}>
                        {m.performed_at
                          ? new Date(m.performed_at).toLocaleString("fr-FR")
                          : "—"}
                      </td>
                      <td style={{ fontWeight: 600 }}>
                        {getProductName(m.product_id)}
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            m.movement_type === "IN" ? "badge-green" : "badge-red"
                          }`}
                          style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}
                        >
                          {m.movement_type === "IN" ? (
                            <ArrowDownCircle size={12} />
                          ) : (
                            <ArrowUpCircle size={12} />
                          )}
                          {m.movement_type === "IN" ? "ENTRÉE" : "SORTIE"}
                        </span>
                      </td>
                      <td style={{ textAlign: "right", fontWeight: 700 }}>
                        {m.quantity}
                      </td>
                      <td style={{ fontSize: "13px" }}>{m.reason || "—"}</td>
                      <td style={{ fontSize: "13px" }}>
                        {m.performed_by ? getStaffName(m.performed_by) : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div style={{ padding: "0 16px" }}>
            <Pagination
              page={page}
              totalPages={totalPages}
              total={total}
              onPageChange={setPage}
              loading={loading}
            />
          </div>
        </div>
      )}
    </>
  );
}
