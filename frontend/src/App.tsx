import { useState } from "react";
import { ResourcePage } from "./components/ResourcePage";
import { SimpleForm } from "./components/SimpleForm";
import { useLookupData } from "./hooks/useLookupData";
import { apiRequest, clearToken, getToken } from "./services/api";
import { login } from "./services/authService";
import { LookupData } from "./types";
import { buildOptions, firstValue } from "./utils/options";

const pages = [
  "Dashboard",
  "Patients",
  "Admissions",
  "Urgences",
  "Pharmacie",
  "Laboratoire",
  "Facturation",
];

export default function App() {
  const [tokenReady, setTokenReady] = useState(Boolean(getToken()));
  const [page, setPage] = useState("Dashboard");
  const [lookupVersion, setLookupVersion] = useState(0);
  const lookups = useLookupData(tokenReady, lookupVersion);

  function refreshAll() {
    window.dispatchEvent(new Event("refresh-resource"));
    setLookupVersion((value) => value + 1);
  }

  if (!tokenReady) {
    return <LoginPage onLogin={() => setTokenReady(true)} />;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>GuineeCare</h1>
        {pages.map((item) => (
          <button
            key={item}
            className={`nav-button ${page === item ? "active" : ""}`}
            onClick={() => setPage(item)}
          >
            {item}
          </button>
        ))}
        <button
          className="nav-button"
          onClick={() => {
            clearToken();
            setTokenReady(false);
          }}
        >
          Deconnexion
        </button>
      </aside>
      <main className="main-content">
        {page === "Dashboard" && <Dashboard lookups={lookups} />}
        {page === "Patients" && (
          <ResourcePage title="Patients" path="/patients" form={<PatientForm lookups={lookups} onCreated={refreshAll} />} />
        )}
        {page === "Admissions" && (
          <ResourcePage title="Admissions" path="/admissions" form={<AdmissionForm lookups={lookups} onCreated={refreshAll} />} />
        )}
        {page === "Urgences" && (
          <ResourcePage title="File urgences" path="/emergency/queue" form={<EmergencyForm lookups={lookups} onCreated={refreshAll} />} />
        )}
        {page === "Pharmacie" && (
          <ResourcePage title="Stock pharmacie" path="/pharmacy/stock" form={<PharmacyForms lookups={lookups} onCreated={refreshAll} />} />
        )}
        {page === "Laboratoire" && (
          <ResourcePage title="Examens laboratoire" path="/laboratory/tests" form={<LaboratoryForms lookups={lookups} onCreated={refreshAll} />} />
        )}
        {page === "Facturation" && (
          <ResourcePage title="Factures" path="/billing/invoices" form={<BillingForms lookups={lookups} onCreated={refreshAll} />} />
        )}
      </main>
    </div>
  );
}

function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("admin@guineecare.local");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await login({ email, password });
      onLogin();
    } catch (err) {
      setError("Connexion impossible. Verifiez les identifiants ou le backend.");
    }
  }

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>GuineeCare Hospital Suite</h1>
        <p className="muted">Connexion au MVP hospitalier</p>
        <form onSubmit={submit}>
          <label className="form-control">
            Email
            <input value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="form-control">
            Mot de passe
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <p style={{ color: "crimson" }}>{error}</p>}
          <button className="primary-button" type="submit">Se connecter</button>
        </form>
      </div>
    </div>
  );
}

function Dashboard({ lookups }: { lookups: LookupData }) {
  return (
    <section>
      <h1>Dashboard hopital</h1>
      <p className="muted">Vue MVP des principaux modules hospitaliers.</p>
      <div className="grid">
        <Kpi title="Etablissements" value={String(lookups.facilities.length)} />
        <Kpi title="Patients" value={String(lookups.patients.length)} />
        <Kpi title="Admissions" value={String(lookups.admissions.length)} />
        <Kpi title="Produits" value={String(lookups.products.length)} />
        <Kpi title="Examens" value={String(lookups.labTests.length)} />
        <Kpi title="Factures" value={String(lookups.invoices.length)} />
      </div>
    </section>
  );
}

function Kpi({ title, value }: { title: string; value: string }) {
  return (
    <div className="card">
      <div className="kpi">{value}</div>
      <div className="muted">{title}</div>
    </div>
  );
}

function PatientForm({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <SimpleForm
      title="Nouveau patient"
      initialValues={{ facility_id: firstValue(options.facilities), patient_number: `PAT-${Date.now()}`, first_name: "", last_name: "" }}
      fields={[
        { name: "facility_id", label: "Etablissement", options: options.facilities },
        { name: "patient_number", label: "Numero patient" },
        { name: "first_name", label: "Prenom" },
        { name: "last_name", label: "Nom" },
      ]}
      onSubmit={async (values) => {
        await apiRequest("/patients", { method: "POST", body: JSON.stringify(values) });
        onCreated();
      }}
    />
  );
}

function AdmissionForm({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <SimpleForm
      title="Nouvelle admission"
      initialValues={{ facility_id: firstValue(options.facilities), patient_id: firstValue(options.patients), department_id: firstValue(options.departments), admission_type: "CONSULTATION" }}
      fields={[
        { name: "facility_id", label: "Etablissement", options: options.facilities },
        { name: "patient_id", label: "Patient", options: options.patients },
        { name: "department_id", label: "Service", options: options.departments },
        { name: "admission_type", label: "Type admission" },
      ]}
      onSubmit={async (values) => {
        await apiRequest("/admissions", { method: "POST", body: JSON.stringify(values) });
        onCreated();
      }}
    />
  );
}

function EmergencyForm({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <SimpleForm
      title="Nouveau passage urgence"
      initialValues={{ facility_id: firstValue(options.facilities), patient_id: firstValue(options.patients), admission_id: "", priority_level: "NORMAL", chief_complaint: "" }}
      fields={[
        { name: "facility_id", label: "Etablissement", options: options.facilities },
        { name: "patient_id", label: "Patient", options: options.patients },
        { name: "admission_id", label: "Admission optionnelle", options: options.admissions },
        { name: "priority_level", label: "Priorite", options: [
          { value: "LOW", label: "Basse" },
          { value: "NORMAL", label: "Normale" },
          { value: "HIGH", label: "Haute" },
          { value: "CRITICAL", label: "Critique" },
        ] },
        { name: "chief_complaint", label: "Motif" },
      ]}
      onSubmit={async (values) => {
        const payload = { ...values, admission_id: values.admission_id || null };
        await apiRequest("/emergency/visits", { method: "POST", body: JSON.stringify(payload) });
        onCreated();
      }}
    />
  );
}

function PharmacyForms({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <>
      <SimpleForm
        title="Nouveau produit pharmacie"
        initialValues={{ facility_id: firstValue(options.facilities), code: `PROD-${Date.now()}`, name: "", category: "MEDICINE", form: "", dosage: "" }}
        fields={[
          { name: "facility_id", label: "Etablissement", options: options.facilities },
          { name: "code", label: "Code" },
          { name: "name", label: "Nom produit" },
          { name: "category", label: "Categorie" },
          { name: "form", label: "Forme" },
          { name: "dosage", label: "Dosage" },
        ]}
        onSubmit={async (values) => {
          await apiRequest("/pharmacy/products", { method: "POST", body: JSON.stringify(values) });
          onCreated();
        }}
      />
      <SimpleForm
        title="Mouvement de stock"
        initialValues={{ facility_id: firstValue(options.facilities), product_id: firstValue(options.products), movement_type: "IN", quantity: "1", reason: "" }}
        fields={[
          { name: "facility_id", label: "Etablissement", options: options.facilities },
          { name: "product_id", label: "Produit", options: options.products },
          { name: "movement_type", label: "Type", options: [
            { value: "IN", label: "Entree" },
            { value: "OUT", label: "Sortie" },
          ] },
          { name: "quantity", label: "Quantite", type: "number" },
          { name: "reason", label: "Motif" },
        ]}
        onSubmit={async (values) => {
          await apiRequest("/pharmacy/stock/movements", {
            method: "POST",
            body: JSON.stringify({ ...values, quantity: Number(values.quantity || 0) }),
          });
          onCreated();
        }}
      />
    </>
  );
}

function LaboratoryForms({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <>
      <SimpleForm
        title="Nouvel examen laboratoire"
        initialValues={{ facility_id: firstValue(options.facilities), code: `LAB-${Date.now()}`, name: "", category: "GENERAL", sample_type: "Sample" }}
        fields={[
          { name: "facility_id", label: "Etablissement", options: options.facilities },
          { name: "code", label: "Code examen" },
          { name: "name", label: "Nom examen" },
          { name: "category", label: "Categorie" },
          { name: "sample_type", label: "Type echantillon" },
        ]}
        onSubmit={async (values) => {
          await apiRequest("/laboratory/tests", { method: "POST", body: JSON.stringify(values) });
          onCreated();
        }}
      />
      <SimpleForm
        title="Nouvelle demande laboratoire"
        initialValues={{ facility_id: firstValue(options.facilities), patient_id: firstValue(options.patients), admission_id: "", test_id: firstValue(options.labTests), priority: "NORMAL" }}
        fields={[
          { name: "facility_id", label: "Etablissement", options: options.facilities },
          { name: "patient_id", label: "Patient", options: options.patients },
          { name: "admission_id", label: "Admission optionnelle", options: options.admissions },
          { name: "test_id", label: "Examen", options: options.labTests },
          { name: "priority", label: "Priorite", options: [
            { value: "NORMAL", label: "Normale" },
            { value: "URGENT", label: "Urgente" },
          ] },
        ]}
        onSubmit={async (values) => {
          const payload = { ...values, admission_id: values.admission_id || null };
          await apiRequest("/laboratory/orders", { method: "POST", body: JSON.stringify(payload) });
          onCreated();
        }}
      />
      <SimpleForm
        title="Resultat laboratoire"
        initialValues={{ facility_id: firstValue(options.facilities), order_id: firstValue(options.labOrders), result_value: "", interpretation: "" }}
        fields={[
          { name: "facility_id", label: "Etablissement", options: options.facilities },
          { name: "order_id", label: "Demande", options: options.labOrders },
          { name: "result_value", label: "Resultat" },
          { name: "interpretation", label: "Interpretation" },
        ]}
        onSubmit={async (values) => {
          await apiRequest(`/laboratory/orders/${values.order_id}/results`, {
            method: "POST",
            body: JSON.stringify({ facility_id: values.facility_id, result_value: values.result_value, interpretation: values.interpretation }),
          });
          onCreated();
        }}
      />
    </>
  );
}

function BillingForms({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <>
      <SimpleForm
        title="Nouvelle facture"
        initialValues={{ facility_id: firstValue(options.facilities), patient_id: firstValue(options.patients), admission_id: "", invoice_number: `INV-${Date.now()}`, description: "", net_amount: "0" }}
        fields={[
          { name: "facility_id", label: "Etablissement", options: options.facilities },
          { name: "patient_id", label: "Patient", options: options.patients },
          { name: "admission_id", label: "Admission optionnelle", options: options.admissions },
          { name: "invoice_number", label: "Numero facture" },
          { name: "description", label: "Description" },
          { name: "net_amount", label: "Montant", type: "number" },
        ]}
        onSubmit={async (values) => {
          const payload = { ...values, admission_id: values.admission_id || null, net_amount: Number(values.net_amount || 0) };
          await apiRequest("/billing/invoices", { method: "POST", body: JSON.stringify(payload) });
          onCreated();
        }}
      />
      <SimpleForm
        title="Nouveau paiement"
        initialValues={{ facility_id: firstValue(options.facilities), invoice_id: firstValue(options.invoices), amount: "0", payment_method: "CASH" }}
        fields={[
          { name: "facility_id", label: "Etablissement", options: options.facilities },
          { name: "invoice_id", label: "Facture", options: options.invoices },
          { name: "amount", label: "Montant", type: "number" },
          { name: "payment_method", label: "Mode paiement", options: [
            { value: "CASH", label: "Especes" },
            { value: "MOBILE_MONEY", label: "Mobile Money" },
            { value: "CARD", label: "Carte" },
          ] },
        ]}
        onSubmit={async (values) => {
          await apiRequest(`/billing/invoices/${values.invoice_id}/payments`, {
            method: "POST",
            body: JSON.stringify({ facility_id: values.facility_id, amount: Number(values.amount || 0), payment_method: values.payment_method }),
          });
          onCreated();
        }}
      />
    </>
  );
}
