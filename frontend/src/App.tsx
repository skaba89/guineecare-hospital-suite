import { useState } from "react";
import { ResourcePage } from "./components/ResourcePage";
import { AdmissionForm } from "./forms/AdmissionForm";
import { BillingForms } from "./forms/BillingForms";
import { EmergencyForm } from "./forms/EmergencyForm";
import { LaboratoryForms } from "./forms/LaboratoryForms";
import { PatientForm } from "./forms/PatientForm";
import { PharmacyForms } from "./forms/PharmacyForms";
import { useLookupData } from "./hooks/useLookupData";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { clearToken, getToken } from "./services/api";

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
        {page === "Dashboard" && <DashboardPage lookups={lookups} />}
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
