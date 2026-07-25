import { lazy, Suspense, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useLookupData } from "./hooks/useLookupData";
import { AppLayout } from "./layout/AppLayout";
import { LoginPage } from "./pages/LoginPage";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";

// ---------------------------------------------------------------------------
// Code splitting: lazy-load all authenticated pages so the initial bundle
// stays small. The LoginPage + AuthContext + DashboardPage load eagerly
// (critical path); everything else is split into per-route chunks.
// ---------------------------------------------------------------------------
const DashboardPage = lazy(() => import("./pages/DashboardPage").then(m => ({ default: m.DashboardPage })));
const PatientsPage = lazy(() => import("./pages/PatientsPage").then(m => ({ default: m.PatientsPage })));
const PatientDetailPage = lazy(() => import("./pages/PatientDetailPage").then(m => ({ default: m.PatientDetailPage })));
const AdmissionsPage = lazy(() => import("./pages/AdmissionsPage").then(m => ({ default: m.AdmissionsPage })));
const EmergencyPage = lazy(() => import("./pages/EmergencyPage").then(m => ({ default: m.EmergencyPage })));
const EmergencyTriagePage = lazy(() => import("./pages/EmergencyTriagePage").then(m => ({ default: m.EmergencyTriagePage })));
const EmergencyOrientationPage = lazy(() => import("./pages/EmergencyOrientationPage").then(m => ({ default: m.EmergencyOrientationPage })));
const PharmacyPage = lazy(() => import("./pages/PharmacyPage").then(m => ({ default: m.PharmacyPage })));
const LabPage = lazy(() => import("./pages/LabPage").then(m => ({ default: m.LabPage })));
const FinancePage = lazy(() => import("./pages/FinancePage").then(m => ({ default: m.FinancePage })));
const ActivityPage = lazy(() => import("./pages/ActivityPage").then(m => ({ default: m.ActivityPage })));
const HospitalizationPage = lazy(() => import("./pages/HospitalizationPage").then(m => ({ default: m.HospitalizationPage })));
const MaternityPage = lazy(() => import("./pages/MaternityPage").then(m => ({ default: m.MaternityPage })));
const PersonnelPage = lazy(() => import("./pages/PersonnelPage").then(m => ({ default: m.PersonnelPage })));
const ImagingPage = lazy(() => import("./pages/ImagingPage").then(m => ({ default: m.ImagingPage })));
const SurgeryPage = lazy(() => import("./pages/SurgeryPage").then(m => ({ default: m.SurgeryPage })));
const QualityPage = lazy(() => import("./pages/QualityPage").then(m => ({ default: m.QualityPage })));
const ReportingPage = lazy(() => import("./pages/ReportingPage").then(m => ({ default: m.ReportingPage })));
const NationalPilotagePage = lazy(() => import("./pages/NationalPilotagePage").then(m => ({ default: m.NationalPilotagePage })));
const UsersPage = lazy(() => import("./pages/UsersPage").then(m => ({ default: m.UsersPage })));
const RbacPage = lazy(() => import("./pages/RbacPage").then(m => ({ default: m.RbacPage })));
const FacilitiesPage = lazy(() => import("./pages/FacilitiesPage").then(m => ({ default: m.FacilitiesPage })));
const DepartmentsPage = lazy(() => import("./pages/DepartmentsPage").then(m => ({ default: m.DepartmentsPage })));
const AuditPage = lazy(() => import("./pages/AuditPage").then(m => ({ default: m.AuditPage })));
const NotificationsPage = lazy(() => import("./pages/NotificationsPage").then(m => ({ default: m.NotificationsPage })));
const SmsAdminPage = lazy(() => import("./pages/SmsAdminPage").then(m => ({ default: m.SmsAdminPage })));
const TasksAdminPage = lazy(() => import("./pages/TasksAdminPage").then(m => ({ default: m.TasksAdminPage })));
const PersonnelPlanningPage = lazy(() => import("./pages/PersonnelPlanningPage").then(m => ({ default: m.PersonnelPlanningPage })));
const LeaveManagementPage = lazy(() => import("./pages/LeaveManagementPage").then(m => ({ default: m.LeaveManagementPage })));

function PageLoader() {
  return (
    <div style={{ padding: "32px", textAlign: "center", color: "#94a3b8" }}>
      <div style={{ fontSize: "14px" }}>Chargement…</div>
    </div>
  );
}

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
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<DashboardPage lookups={lookups} />} />
            <Route path="/notifications" element={<NotificationsPage />} />
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
            <Route path="/personnel/planning" element={<ProtectedRoute permission="personnel.read"><PersonnelPlanningPage lookups={lookups} /></ProtectedRoute>} />
            <Route path="/personnel/leaves" element={<ProtectedRoute permission="personnel.read"><LeaveManagementPage lookups={lookups} /></ProtectedRoute>} />
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
            <Route path="/audit" element={<ProtectedRoute roles={["SUPER_ADMIN", "ADMIN"]}><AuditPage /></ProtectedRoute>} />
            <Route path="/sms-admin" element={<ProtectedRoute roles={["SUPER_ADMIN", "ADMIN"]}><SmsAdminPage /></ProtectedRoute>} />
            <Route path="/tasks-admin" element={<ProtectedRoute roles={["SUPER_ADMIN", "ADMIN"]}><TasksAdminPage /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
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
