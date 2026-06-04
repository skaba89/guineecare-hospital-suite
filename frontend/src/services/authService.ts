import { apiRequest, setToken, clearToken } from "./api";

export type LoginPayload = {
  email: string;
  password: string;
};

export async function login(payload: LoginPayload) {
  const response = await apiRequest<any>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  setToken(response.access_token);
  return response;
}

export async function getCurrentUser() {
  return apiRequest<any>("/auth/me");
}

export function logout() {
  clearToken();
}
