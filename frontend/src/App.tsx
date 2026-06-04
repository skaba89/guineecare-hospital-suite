import { useState } from "react";
import { ResourcePage } from "./components/ResourcePage";
import { AdmissionForm } from "./forms/AdmissionForm";
import { BillingForms } from "./forms/BillingForms";
import { EmergencyForm } from "./forms/EmergencyForm";
import { LaboratoryForms } from "./forms/LaboratoryForms";
import { PatientForm } from "./forms/PatientForm";
import { PharmacyForms } from "./forms/PharmacyForms";
import { useLookupData } from "./hooks/useLookupData";
import { clearToken, getToken } from "./services/api";
import { login } from "./services/authService";
import { LookupData } from "./types";

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
