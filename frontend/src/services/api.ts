const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export type ApiResponse<T> = {
  data?: T;
  message?: string;
  access_token?: string;
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

export function clearToken(): void {
  localStorage.removeItem("guineecare_token");
  localStorage.removeItem("guineecare_user");
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

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

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
