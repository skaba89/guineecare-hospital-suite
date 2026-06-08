import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useLookupData } from "./hooks/useLookupData";
import { AppLayout } from "./layout/AppLayout";
import { ActivityPage } from "./pages/ActivityPage";
import { AdmissionsPage } from "./pages/AdmissionsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EmergencyPage } from "./pages/EmergencyPage";
import { FinancePage } from "./pages/FinancePage";
import { LabPage } from "./pages/LabPage";
import { LoginPage } from "./pages/LoginPage";
import { PatientsPage } from "./pages/PatientsPage";
import { PharmacyPage } from "./pages/PharmacyPage";
import { clearToken, getToken } from "./services/api";
import { getCurrentUser } from "./services/authService";

export default function App() {
  const [bootstrapping, setBootstrapping] = useState(Boolean(getToken()));
  const [tokenReady, setTokenReady] = useState(false);
  const [lookupVersion, setLookupVersion] = useState(0);
  const lookups = useLookupData(tokenReady, lookupVersion);

  useEffect(() => {
    async function verifyExistingSession() {
      if (!getToken()) {
        setBootstrapping(false);
        return;
      }

      try {
        await getCurrentUser();
        setTokenReady(true);
      } catch (err) {
        clearToken();
        setTokenReady(false);
      } finally {
        setBootstrapping(false);
      }
    }

    verifyExistingSession();
  }, []);

  function refreshAll() {
    window.dispatchEvent(new Event("refresh-resource"));
    setLookupVersion((value) => value + 1);
  }

  function logout() {
    clearToken();
    setTokenReady(false);
  }

  if (bootstrapping) {
    return (
      <div className="login-page">
        <div className="card login-card">
          <h1>GuineeCare</h1>
          <p className="muted">Verification de la session...</p>
        </div>
      </div>
    );
  }

  if (!tokenReady) {
    return <LoginPage onLogin={() => setTokenReady(true)} />;
  }

  return (
    <BrowserRouter>
      <AppLayout onLogout={logout}>
        <Routes>
          <Route path="/" element={<DashboardPage lookups={lookups} />} />
          <Route path="/patients" element={<PatientsPage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/admissions" element={<AdmissionsPage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/emergency" element={<EmergencyPage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/pharmacy" element={<PharmacyPage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/lab" element={<LabPage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/billing" element={<FinancePage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/activity" element={<ActivityPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}
