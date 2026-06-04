const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export type ApiResponse<T> = {
  data?: T;
  message?: string;
  access_token?: string;
  token_type?: string;
  user?: unknown;
};

export function getToken(): string | null {
  return localStorage.getItem("guineecare_token");
}

export function setToken(token: string): void {
  localStorage.setItem("guineecare_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("guineecare_token");
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

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }

  return response.json();
}
