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

// v2.8.5 — Délai d'attente pour les requêtes (15s).
// Render free tier peut mettre 30-60s à se réveiller (cold start).
// On utilise 15s pour ne pas bloquer l'UI trop longtemps.
const REQUEST_TIMEOUT_MS = 15000;

// v2.8.5 — Wrapper fetch avec timeout + retry sur 502/503 (Render cold start)
async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = REQUEST_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

// v2.8.5 — Retry sur 502/503 (Render cold start ou restart)
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 3000;

async function fetchWithRetry(url: string, options: RequestInit = {}, timeoutMs = REQUEST_TIMEOUT_MS): Promise<Response> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await fetchWithTimeout(url, options, timeoutMs);

      // 502/503 = serveur en cours de redémarrage (Render free tier)
      if ((response.status === 502 || response.status === 503) && attempt < MAX_RETRIES) {
        console.warn(`[api] ${response.status} received — retrying in ${RETRY_DELAY_MS}ms (attempt ${attempt + 1}/${MAX_RETRIES})...`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
        continue;
      }

      return response;
    } catch (e: any) {
      // ERR_NETWORK ou AbortError (timeout) = serveur qui se réveille
      if (attempt < MAX_RETRIES) {
        console.warn(`[api] ${e.name || 'Network error'} — retrying in ${RETRY_DELAY_MS}ms (attempt ${attempt + 1}/${MAX_RETRIES})...`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
        lastError = e;
        continue;
      }
      throw e;
    }
  }

  throw lastError || new Error("Network error after retries");
}

async function tryRefresh(): Promise<string | null> {
  // If a refresh is already in flight, reuse it
  if (refreshPromise) return refreshPromise;

  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  refreshPromise = (async () => {
    try {
      const response = await fetchWithRetry(
        `${API_BASE_URL}/auth/refresh`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        },
        20000 // Refresh a un timeout plus long (20s) pour Render cold start
      );
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

  // v2.8.5 — fetchWithRetry gère timeout + retry sur 502/503 (Render cold start)
  let response = await fetchWithRetry(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  // If 401 and we have a refresh token, try to refresh and retry once
  if (response.status === 401 && token && getRefreshToken()) {
    const newToken = await tryRefresh();
    if (newToken) {
      // Retry the original request with the new token
      headers["Authorization"] = `Bearer ${newToken}`;
      response = await fetchWithRetry(`${API_BASE_URL}${path}`, {
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

  // v2.8.5 — Message compréhensible pour 502/503 (Render cold start)
  if (response.status === 502 || response.status === 503) {
    throw new Error("Le serveur est en cours de démarrage. Veuillez réessayer dans quelques secondes.");
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }

  // v2.8.5 — Gérer les réponses vides (204 No Content)
  const contentLength = response.headers.get("content-length");
  if (response.status === 204 || contentLength === "0") {
    return {} as T;
  }

  return response.json();
}
