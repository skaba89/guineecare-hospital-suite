import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useLookupData } from "./hooks/useLookupData";
import { AppLayout } from "./layout/AppLayout";
import { ActivityPage } from "./pages/ActivityPage";
import { UsersPage } from "./pages/UsersPage";
import { RbacPage } from "./pages/RbacPage";
import { FacilitiesPage } from "./pages/FacilitiesPage";
import { DepartmentsPage } from "./pages/DepartmentsPage";
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
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";

function AppInner() {
  const { currentUser, isAuthenticated, loading, login, logout } = useAuth();
  const [lookupVersion, setLookupVersion] = useState(0);
  const lookups = useLookupData(isAuthenticated, lookupVersion);

  function refreshAll() {
    window.dispatchEvent(new Event("refresh-resource"));
    setLookupVersion((value) => value + 1);
  }

  function getPatientName(patientId: string): string {
    const patient = lookups.patients.find((p) => p.id === patientId);
    if (!patient) return "Inconnu";
    return `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.patient_number || "N/A";
  }

  function getStaffName(staffId: string): string {
    const staff = lookups.staff.find((s) => s.id === staffId);
    if (!staff) return "Inconnu";
    return `${staff.first_name || ""} ${staff.last_name || ""}`.trim() || staff.employee_number || "N/A";
  }

  if (loading) {
    return (
      <div className="login-page">
        <div className="card login-card">
          <h1>GuinéeCare</h1>
          <p className="muted">Vérification de la session...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={login} />;
  }

  return (
    <BrowserRouter>
      <AppLayout onLogout={logout} currentUser={currentUser} getPatientName={getPatientName} getStaffName={getStaffName}>
        <Routes>
          <Route path="/" element={<DashboardPage lookups={lookups} />} />
          <Route path="/patients" element={<ProtectedRoute permission="patient.read"><PatientsPage lookups={lookups} onCreated={refreshAll} /></ProtectedRoute>} />
          <Route path="/patients/:id" element={<ProtectedRoute permission="patient.read"><PatientDetailPage lookups={lookups} /></ProtectedRoute>} />
          <Route path="/admissions" element={<ProtectedRoute permission="admission.read"><AdmissionsPage lookups={lookups} onCreated={refreshAll} /></ProtectedRoute>} />
          <Route path="/emergency" element={<ProtectedRoute permission="emergency.read"><EmergencyPage lookups={lookups} onCreated={refreshAll} /></ProtectedRoute>} />
          <Route path="/pharmacy" element={<ProtectedRoute permission="pharmacy.read"><PharmacyPage lookups={lookups} onCreated={refreshAll} /></ProtectedRoute>} />
          <Route path="/lab" element={<ProtectedRoute permission="lab.read"><LabPage lookups={lookups} onCreated={refreshAll} /></ProtectedRoute>} />
          <Route path="/billing" element={<ProtectedRoute permission="billing.read"><FinancePage lookups={lookups} onCreated={refreshAll} /></ProtectedRoute>} />
          <Route path="/activity" element={<ProtectedRoute roles={["SUPER_ADMIN", "ADMIN"]}><ActivityPage lookups={lookups} /></ProtectedRoute>} />
          <Route path="/hospitalization" element={<ProtectedRoute permission="hospitalization.read"><HospitalizationPage lookups={lookups} /></ProtectedRoute>} />
          <Route path="/maternity" element={<ProtectedRoute permission="maternity.read"><MaternityPage lookups={lookups} /></ProtectedRoute>} />
          <Route path="/personnel" element={<ProtectedRoute permission="personnel.read"><PersonnelPage lookups={lookups} onCreated={refreshAll} /></ProtectedRoute>} />
          <Route path="/imaging" element={<ProtectedRoute permission="imaging.read"><ImagingPage lookups={lookups} /></ProtectedRoute>} />
          <Route path="/surgery" element={<ProtectedRoute permission="surgery.read"><SurgeryPage lookups={lookups} /></ProtectedRoute>} />
          <Route path="/quality" element={<ProtectedRoute permission="quality.read"><QualityPage lookups={lookups} /></ProtectedRoute>} />
          <Route path="/reporting" element={<ProtectedRoute permission="reporting.read"><ReportingPage lookups={lookups} /></ProtectedRoute>} />
          <Route path="/emergency/triage" element={<ProtectedRoute permission="emergency.triage"><EmergencyTriagePage lookups={lookups} onCreated={refreshAll} getPatientName={getPatientName} /></ProtectedRoute>} />
          <Route path="/emergency/orientation" element={<ProtectedRoute permission="emergency.orient"><EmergencyOrientationPage lookups={lookups} onCreated={refreshAll} getPatientName={getPatientName} /></ProtectedRoute>} />
          <Route path="/national" element={<ProtectedRoute roles={["SUPER_ADMIN", "ADMIN"]}><NationalPilotagePage lookups={lookups} /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute roles={["SUPER_ADMIN", "ADMIN"]}><UsersPage /></ProtectedRoute>} />
          <Route path="/rbac" element={<ProtectedRoute roles={["SUPER_ADMIN", "ADMIN"]}><RbacPage /></ProtectedRoute>} />
          <Route path="/facilities" element={<ProtectedRoute roles={["SUPER_ADMIN", "ADMIN"]}><FacilitiesPage /></ProtectedRoute>} />
          <Route path="/departments" element={<ProtectedRoute roles={["SUPER_ADMIN", "ADMIN"]}><DepartmentsPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
