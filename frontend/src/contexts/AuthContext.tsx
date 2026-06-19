import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";
import {
  clearToken,
  getToken,
  getStoredUser,
  setOnUnauthorized,
  setStoredUser,
  setToken,
} from "../services/api";
import {
  getCurrentUser,
  login as apiLogin,
  logout as apiLogout,
  type CurrentUser,
  type LoginPayload,
} from "../services/authService";

type AuthContextType = {
  currentUser: CurrentUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  isSuperAdmin: boolean;
  isAdmin: boolean;
  isDoctor: boolean;
  isNurse: boolean;
  isPharmacist: boolean;
  isLabTech: boolean;
  isCashier: boolean;
  isMidwife: boolean;
  userFacilityId: string | null;
  hasRole: (...roles: string[]) => boolean;
  hasPermission: (permission: string) => boolean;
};

const AuthContext = createContext<AuthContextType | null>(null);

// Role-based permission map (mirrors backend RBAC)
const ROLE_PERMISSIONS: Record<string, string[]> = {
  SUPER_ADMIN: ["*"], // All permissions
  ADMIN: ["*"], // All permissions
  DOCTOR: [
    "patient.read", "admission.read", "admission.create",
    "emergency.read", "emergency.create", "emergency.triage", "emergency.orient",
    "emergency.care", "emergency.discharge",
    "lab.read", "lab.order", "lab.result",
    "clinical.read", "clinical.write",
    "hospitalization.read", "hospitalization.manage",
    "personnel.read", "maternity.read", "maternity.write",
    "imaging.read", "imaging.manage", "surgery.read", "surgery.manage",
    "quality.read", "reporting.read",
  ],
  NURSE: [
    "patient.read", "admission.read", "emergency.read",
    "emergency.triage", "emergency.care",
    "clinical.read", "clinical.write",
    "hospitalization.read", "personnel.read",
    "maternity.read", "imaging.read", "quality.read",
  ],
  PHARMACIST: ["patient.read", "pharmacy.read", "pharmacy.manage"],
  LAB_TECH: ["patient.read", "lab.read", "lab.result", "lab.validate"],
  CASHIER: ["patient.read", "billing.read", "billing.manage", "billing.pay"],
  MIDWIFE: [
    "patient.read", "maternity.read", "maternity.write",
    "emergency.care", "clinical.read", "clinical.write",
  ],
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [bootstrapping, setBootstrapping] = useState(Boolean(getToken()));
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(
    getStoredUser() as CurrentUser | null
  );
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Register 401 handler
  useEffect(() => {
    setOnUnauthorized(() => {
      setIsAuthenticated(false);
      setCurrentUser(null);
    });
  }, []);

  // Verify existing session on mount
  useEffect(() => {
    async function verifyExistingSession() {
      if (!getToken()) {
        setBootstrapping(false);
        setLoading(false);
        return;
      }
      try {
        const user = await getCurrentUser();
        setCurrentUser(user);
        setIsAuthenticated(true);
      } catch {
        clearToken();
        setIsAuthenticated(false);
        setCurrentUser(null);
      } finally {
        setBootstrapping(false);
        setLoading(false);
      }
    }
    verifyExistingSession();
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    await apiLogin(payload);
    // Fetch full user data after login
    const user = await getCurrentUser();
    setCurrentUser(user);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setIsAuthenticated(false);
    setCurrentUser(null);
  }, []);

  const hasRole = useCallback(
    (...roles: string[]) => {
      if (!currentUser) return false;
      return roles.includes(currentUser.role);
    },
    [currentUser]
  );

  const hasPermission = useCallback(
    (permission: string) => {
      if (!currentUser) return false;
      const perms = ROLE_PERMISSIONS[currentUser.role] || [];
      if (perms.includes("*")) return true;
      return perms.includes(permission);
    },
    [currentUser]
  );

  const value: AuthContextType = {
    currentUser,
    isAuthenticated,
    loading: loading || bootstrapping,
    login,
    logout,
    isSuperAdmin: currentUser?.role === "SUPER_ADMIN",
    isAdmin: currentUser?.role === "ADMIN" || currentUser?.role === "SUPER_ADMIN",
    isDoctor: currentUser?.role === "DOCTOR",
    isNurse: currentUser?.role === "NURSE",
    isPharmacist: currentUser?.role === "PHARMACIST",
    isLabTech: currentUser?.role === "LAB_TECH",
    isCashier: currentUser?.role === "CASHIER",
    isMidwife: currentUser?.role === "MIDWIFE",
    userFacilityId: currentUser?.facility_id || null,
    hasRole,
    hasPermission,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
