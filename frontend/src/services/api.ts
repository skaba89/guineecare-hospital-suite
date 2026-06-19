const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";

export type ApiResponse<T> = {
  data?: T;
  message?: string;
  access_token?: string;
  refresh_token?: string;
  token_type?: string;
  user?: unknown;
};

let onUnauthorized: (() => void) | null = null;

export function setOnUnauthorized(handler: () => void) {
  onUnauthorized = handler;
}

export function getToken(): string | null {
  return localStorage.getItem("guineecare_token");
}

export function setToken(token: string): void {
  localStorage.setItem("guineecare_token", token);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem("guineecare_refresh_token");
}

export function setRefreshToken(token: string): void {
  localStorage.setItem("guineecare_refresh_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("guineecare_token");
  localStorage.removeItem("guineecare_user");
  localStorage.removeItem("guineecare_refresh_token");
}

export function getStoredUser(): Record<string, any> | null {
  const raw = localStorage.getItem("guineecare_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setStoredUser(user: Record<string, any>): void {
  localStorage.setItem("guineecare_user", JSON.stringify(user));
}

// In-flight refresh promise — prevents multiple parallel refresh attempts
let refreshPromise: Promise<string | null> | null = null;

async function tryRefresh(): Promise<string | null> {
  // If a refresh is already in flight, reuse it
  if (refreshPromise) return refreshPromise;

  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) {
        // Refresh failed — clear tokens
        clearToken();
        if (onUnauthorized) onUnauthorized();
        return null;
      }
      const data = await response.json();
      if (data.access_token) setToken(data.access_token);
      if (data.refresh_token) setRefreshToken(data.refresh_token);
      if (data.user) setStoredUser(data.user);
      return data.access_token as string;
    } catch {
      clearToken();
      if (onUnauthorized) onUnauthorized();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const storedUser = getStoredUser();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Add tenant header for facility scoping (non-SUPER_ADMIN)
  if (storedUser?.facility_id && storedUser?.role !== "SUPER_ADMIN") {
    headers["X-Facility-ID"] = storedUser.facility_id;
  }

  let response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  // If 401 and we have a refresh token, try to refresh and retry once
  if (response.status === 401 && token && getRefreshToken()) {
    const newToken = await tryRefresh();
    if (newToken) {
      // Retry the original request with the new token
      headers["Authorization"] = `Bearer ${newToken}`;
      response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
      });
    }
  }

  if (response.status === 401) {
    clearToken();
    if (onUnauthorized) {
      onUnauthorized();
    }
    throw new Error("Session expirée. Veuillez vous reconnecter.");
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }

  return response.json();
}
