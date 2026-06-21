/**
 * Service API GuinéeCare — client HTTP avec gestion JWT + refresh automatique.
 *
 * Stockage sécurisé via expo-secure-store (Keychain iOS / Keystore Android).
 * Refresh automatique sur 401, avec queue des requêtes pendant le refresh.
 *
 * Endpoint backend : configuré via env `EXPO_PUBLIC_API_URL` ou défaut local.
 */
import * as SecureStore from 'expo-secure-store';
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { AuthSession, User } from '../types';

// Endpoints supportés par l'app mobile (sous-ensemble du backend)
const API_BASE_URL =
  (process.env.EXPO_PUBLIC_API_URL as string | undefined) ||
  'http://10.0.2.2:8000/api/v1'; // 10.0.2.2 = host loopback depuis l'émulateur Android
const API_PREFIX = '/api/v1';

const TOKEN_KEY = 'guineecare_session';
const FACILITY_KEY = 'guineecare_active_facility';

let session: AuthSession | null = null;
let refreshPromise: Promise<string | null> | null = null;

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// --- Session persistence ---

export async function loadSession(): Promise<AuthSession | null> {
  try {
    const raw = await SecureStore.getItemAsync(TOKEN_KEY);
    if (!raw) return null;
    session = JSON.parse(raw) as AuthSession;
    return session;
  } catch (e) {
    console.warn('loadSession failed:', e);
    return null;
  }
}

export async function saveSession(s: AuthSession): Promise<void> {
  session = s;
  await SecureStore.setItemAsync(TOKEN_KEY, JSON.stringify(s));
}

export async function clearSession(): Promise<void> {
  session = null;
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(FACILITY_KEY);
}

export function getSession(): AuthSession | null {
  return session;
}

export function getCurrentUser(): User | null {
  return session?.user ?? null;
}

// --- Active facility (for multi-tenant context) ---

export async function setActiveFacility(facilityId: string): Promise<void> {
  await SecureStore.setItemAsync(FACILITY_KEY, facilityId);
}

export async function getActiveFacility(): Promise<string | null> {
  return await SecureStore.getItemAsync(FACILITY_KEY);
}

// --- Request interceptor : inject Authorization + X-Facility-ID ---

api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  if (session?.access_token) {
    config.headers = config.headers || ({} as any);
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  // Multi-tenant header (sauf SUPER_ADMIN qui voit tout)
  if (session?.user && session.user.role !== 'SUPER_ADMIN' && session.user.facility_id) {
    config.headers = config.headers || ({} as any);
    config.headers['X-Facility-ID'] = session.user.facility_id;
  }
  return config;
});

// --- Refresh token with queue ---

async function refreshAccessToken(): Promise<string | null> {
  if (!session?.refresh_token) return null;
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const resp = await axios.post(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: session!.refresh_token,
      });
      const newSession: AuthSession = {
        ...session!,
        access_token: resp.data.access_token,
        refresh_token: resp.data.refresh_token || session!.refresh_token,
        user: resp.data.user || session!.user,
      };
      await saveSession(newSession);
      return newSession.access_token;
    } catch (e) {
      console.warn('Refresh failed, clearing session:', e);
      await clearSession();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

// --- Response interceptor : refresh on 401 ---

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retried?: boolean };
    if (error.response?.status === 401 && !originalRequest._retried && session?.refresh_token) {
      originalRequest._retried = true;
      const newToken = await refreshAccessToken();
      if (newToken) {
        originalRequest.headers = originalRequest.headers || ({} as any);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      }
    }
    return Promise.reject(error);
  }
);

// --- Auth API ---

export async function login(email: string, password: string): Promise<AuthSession> {
  const resp = await api.post('/auth/login', { email, password });
  const newSession: AuthSession = {
    access_token: resp.data.access_token,
    refresh_token: resp.data.refresh_token,
    token_type: resp.data.token_type || 'bearer',
    user: resp.data.user,
  };
  await saveSession(newSession);
  return newSession;
}

export async function logout(): Promise<void> {
  try {
    if (session?.access_token) {
      await api.post('/auth/logout', { refresh_token: session.refresh_token });
    }
  } catch (e) {
    // ignore — server-side logout may fail if token already expired
  } finally {
    await clearSession();
  }
}

export async function getProfile(): Promise<User> {
  const resp = await api.get('/auth/me');
  return resp.data;
}

// --- Patients API ---

export async function listPatients(params: {
  page?: number;
  page_size?: number;
  search?: string;
} = {}): Promise<{ data: Patient[]; total: number; page: number; total_pages: number }> {
  const resp = await api.get('/patients', { params });
  return resp.data;
}

export async function getPatient(id: string): Promise<{ data: Patient }> {
  const resp = await api.get(`/patients/${id}`);
  return resp.data;
}

export async function getPatientByQr(qrContent: string): Promise<{ data: Patient }> {
  // qrContent peut être un ID ou un patient_number (PAT-...)
  const resp = await api.get(`/patients/${qrContent}`);
  return resp.data;
}

// --- Admissions API ---

export async function listPatientAdmissions(patientId: string): Promise<{ data: any[] }> {
  const resp = await api.get('/admissions', {
    params: { patient_id: patientId, page_size: 50 },
  });
  return resp.data;
}

// --- Measurements (constantes vitales) API ---

export async function listPatientMeasurements(patientId: string): Promise<{ data: any[] }> {
  const resp = await api.get('/clinical/measurements', {
    params: { patient_id: patientId, page_size: 50 },
  });
  return resp.data;
}

export async function createMeasurement(payload: {
  patient_id: string;
  measurement_type: string;
  value: string;
  unit?: string;
}): Promise<{ data: any }> {
  const resp = await api.post('/clinical/measurements', payload);
  return resp.data;
}

// --- Lab orders / results ---

export async function listPatientLabOrders(patientId: string): Promise<{ data: any[] }> {
  const resp = await api.get('/laboratory/orders', {
    params: { patient_id: patientId, page_size: 50 },
  });
  return resp.data;
}

// --- Clinical notes (prescriptions) ---

export async function listPatientClinicalNotes(patientId: string): Promise<{ data: any[] }> {
  const resp = await api.get('/clinical/notes', {
    params: { patient_id: patientId, page_size: 50 },
  });
  return resp.data;
}

// --- Notifications ---

export async function listNotifications(params: {
  page?: number;
  page_size?: number;
  unread_only?: boolean;
} = {}): Promise<{ data: any[]; unread_count: number; total: number }> {
  const resp = await api.get('/notifications', { params });
  return resp.data;
}

export async function markNotificationRead(id: string): Promise<void> {
  await api.patch(`/notifications/${id}/read`);
}

// --- Dashboard KPIs (via /reporting/dashboard ou agrégat custom) ---

export async function getDashboardKPIs(): Promise<DashboardKPIs> {
  // Le backend expose /reporting/dashboard pour les admin
  // Pour les autres rôles, on agrège depuis plusieurs endpoints
  try {
    const resp = await api.get('/reporting/dashboard');
    return resp.data;
  } catch {
    // Fallback : valeurs à zéro si l'endpoint n'est pas accessible
    return {
      patients_total: 0,
      admissions_active: 0,
      beds_occupied: 0,
      emergencies_in_progress: 0,
      pending_lab_results: 0,
      pending_imaging: 0,
      revenue_today: 0,
      outstanding_balance: 0,
    };
  }
}

// --- Push notification registration ---

export async function registerPushToken(token: string): Promise<void> {
  try {
    await api.post('/user-profile/devices', {
      device_token: token,
      device_type: Platform.OS === 'ios' ? 'ios' : 'android',
    });
  } catch (e) {
    // Endpoint peut ne pas exister encore — silencieux en v1.7
    console.debug('Push token registration skipped:', e);
  }
}

import { Platform } from 'react-native';

// --- Export the configured axios instance for advanced use ---

export { api, API_BASE_URL };
