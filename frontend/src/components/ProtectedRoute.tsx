import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

type ProtectedRouteProps = {
  children: React.ReactNode;
  roles?: string[];
  permission?: string;
};

/**
 * Route guard that checks if the current user has the required role/permission.
 * If no roles/permission specified, only checks authentication.
 * If user doesn't meet requirements, redirects to dashboard.
 */
export function ProtectedRoute({ children, roles, permission }: ProtectedRouteProps) {
  const { isAuthenticated, hasRole, hasPermission } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (roles && !hasRole(...roles)) {
    return <Navigate to="/" replace />;
  }

  if (permission && !hasPermission(permission)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

/**
 * Navigation visibility helper - returns whether a nav item should be shown.
 */
export function useNavVisibility() {
  const { hasRole, hasPermission, isSuperAdmin, isAdmin } = useAuth();

  return {
    canSeeDashboard: true,
    canSeePatients: hasPermission("patient.read"),
    canSeeAdmissions: hasPermission("admission.read"),
    canSeeEmergency: hasPermission("emergency.read"),
    canSeeHospitalization: hasPermission("hospitalization.read"),
    canSeeMaternity: hasPermission("maternity.read"),
    canSeePharmacy: hasPermission("pharmacy.read"),
    canSeeLab: hasPermission("lab.read"),
    canSeeImaging: hasPermission("imaging.read"),
    canSeeSurgery: hasPermission("surgery.read"),
    canSeeBilling: hasPermission("billing.read"),
    canSeePersonnel: hasPermission("personnel.read"),
    canSeeQuality: hasPermission("quality.read"),
    canSeeActivity: hasRole("SUPER_ADMIN", "ADMIN"),
    canSeeNational: hasRole("SUPER_ADMIN", "ADMIN"),
    canSeeReporting: hasPermission("reporting.read"),
    // System admin pages (Users, RBAC, Facilities, Departments)
    canSeeSystemAdmin: isSuperAdmin || isAdmin,
    canSeeUsers: isSuperAdmin || isAdmin,
    canSeeRbac: isSuperAdmin || isAdmin,
    canSeeFacilities: hasPermission("facility.read") || isSuperAdmin || isAdmin,
    canSeeDepartments: hasPermission("department.read") || isSuperAdmin || isAdmin,
  };
}
