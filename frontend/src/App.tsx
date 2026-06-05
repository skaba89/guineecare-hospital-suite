import { useState } from "react";
import { useLookupData } from "./hooks/useLookupData";
import { AdmissionsPage } from "./pages/AdmissionsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EmergencyPage } from "./pages/EmergencyPage";
import { FinancePage } from "./pages/FinancePage";
import { LabPage } from "./pages/LabPage";
import { LoginPage } from "./pages/LoginPage";
import { PatientsPage } from "./pages/PatientsPage";
import { PharmacyPage } from "./pages/PharmacyPage";
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
        {page === "Patients" && <PatientsPage lookups={lookups} onCreated={refreshAll} />}
        {page === "Admissions" && <AdmissionsPage lookups={lookups} onCreated={refreshAll} />}
        {page === "Urgences" && <EmergencyPage lookups={lookups} onCreated={refreshAll} />}
        {page === "Pharmacie" && <PharmacyPage lookups={lookups} onCreated={refreshAll} />}
        {page === "Laboratoire" && <LabPage lookups={lookups} onCreated={refreshAll} />}
        {page === "Facturation" && <FinancePage lookups={lookups} onCreated={refreshAll} />}
      </main>
    </div>
  );
}
