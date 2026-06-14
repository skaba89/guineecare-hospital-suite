import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useLookupData } from "./hooks/useLookupData";
import { AppLayout } from "./layout/AppLayout";
import { ActivityPage } from "./pages/ActivityPage";
import { AdmissionsPage } from "./pages/AdmissionsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EmergencyPage } from "./pages/EmergencyPage";
import { EmergencyOrientationPage } from "./pages/EmergencyOrientationPage";
import { EmergencyTriagePage } from "./pages/EmergencyTriagePage";
import { FinancePage } from "./pages/FinancePage";
import { HospitalizationPage } from "./pages/HospitalizationPage";
import { LabPage } from "./pages/LabPage";
import { LoginPage } from "./pages/LoginPage";
import { MaternityPage } from "./pages/MaternityPage";
import { NationalPilotagePage } from "./pages/NationalPilotagePage";
import { PatientDetailPage } from "./pages/PatientDetailPage";
import { PatientsPage } from "./pages/PatientsPage";
import { PersonnelPage } from "./pages/PersonnelPage";
import { PharmacyPage } from "./pages/PharmacyPage";
import { ImagingPage } from "./pages/ImagingPage";
import { SurgeryPage } from "./pages/SurgeryPage";
import { QualityPage } from "./pages/QualityPage";
import { ReportingPage } from "./pages/ReportingPage";
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

  function getPatientName(patientId: string): string {
    const patient = lookups.patients.find((p) => p.id === patientId);
    if (!patient) return "Inconnu";
    return `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.patient_number || "N/A";
  }

  if (bootstrapping) {
    return (
      <div className="login-page">
        <div className="card login-card">
          <h1>GuinéeCare</h1>
          <p className="muted">Vérification de la session...</p>
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
          <Route path="/patients/:id" element={<PatientDetailPage lookups={lookups} />} />
          <Route path="/admissions" element={<AdmissionsPage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/emergency" element={<EmergencyPage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/pharmacy" element={<PharmacyPage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/lab" element={<LabPage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/billing" element={<FinancePage lookups={lookups} onCreated={refreshAll} />} />
          <Route path="/activity" element={<ActivityPage lookups={lookups} />} />
          <Route path="/hospitalization" element={<HospitalizationPage lookups={lookups} />} />
          <Route path="/maternity" element={<MaternityPage lookups={lookups} />} />
          <Route path="/personnel" element={<PersonnelPage lookups={lookups} />} />
          <Route path="/imaging" element={<ImagingPage lookups={lookups} />} />
          <Route path="/surgery" element={<SurgeryPage lookups={lookups} />} />
          <Route path="/quality" element={<QualityPage lookups={lookups} />} />
          <Route path="/reporting" element={<ReportingPage lookups={lookups} />} />
          <Route path="/emergency/triage" element={<EmergencyTriagePage lookups={lookups} onCreated={refreshAll} getPatientName={getPatientName} />} />
          <Route path="/emergency/orientation" element={<EmergencyOrientationPage lookups={lookups} onCreated={refreshAll} getPatientName={getPatientName} />} />
          <Route path="/national" element={<NationalPilotagePage lookups={lookups} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}
