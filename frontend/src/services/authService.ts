import { apiRequest, setToken, setRefreshToken, clearToken, setStoredUser } from "./api";

export type LoginPayload = {
  email: string;
  password: string;
};

export type CurrentUser = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  facility_id: string | null;
  is_active: boolean;
};

const ROLE_LABELS: Record<string, string> = {
  SUPER_ADMIN: "Super Admin",
  ADMIN: "Administrateur",
  DOCTOR: "Médecin",
  NURSE: "Infirmier(e)",
  PHARMACIST: "Pharmacien",
  LAB_TECH: "Laborantin",
  CASHIER: "Caissier",
  MIDWIFE: "Sage-femme",
};

export function getRoleLabel(role: string): string {
  return ROLE_LABELS[role] || role;
}

export function getUserInitials(user: CurrentUser): string {
  const first = user.first_name?.charAt(0)?.toUpperCase() || "";
  const last = user.last_name?.charAt(0)?.toUpperCase() || "";
  return first + last || "U";
}

export function getUserDisplayName(user: CurrentUser): string {
  const parts = [user.first_name, user.last_name].filter(Boolean);
  return parts.join(" ") || user.email;
}

export async function login(payload: LoginPayload) {
  const response = await apiRequest<any>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  // v3.4.1 — Gestion de la réponse 2FA
  if (response.requires_2fa) {
    return response;
  }

  setToken(response.access_token);
  if (response.refresh_token) {
    setRefreshToken(response.refresh_token);
  }
  if (response.user) {
    setStoredUser(response.user);
  }
  return response;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiRequest<any>("/auth/me");
  setStoredUser(response);
  return response;
}

export async function logout(): Promise<void> {
  const refreshToken = localStorage.getItem("guineecare_refresh_token");
  try {
    // Best-effort: notify backend to revoke the refresh token.
    // If it fails (network error, expired token), we still clear locally.
    await apiRequest<any>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } catch {
    // ignore — local clear is the source of truth for the UI
  } finally {
    clearToken();
  }
}
