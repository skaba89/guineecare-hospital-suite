/**
 * Types partagés entre l'app mobile React Native et le backend GuinéeCare.
 * Version simplifiée des modèles backend — uniquement les champs utilisés côté mobile.
 */

export type Role =
  | 'SUPER_ADMIN'
  | 'ADMIN'
  | 'DOCTOR'
  | 'NURSE'
  | 'MIDWIFE'
  | 'PHARMACIST'
  | 'LAB_TECH'
  | 'CASHIER';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  facility_id: string | null;
  is_active: boolean;
  phone?: string;
}

export interface AuthSession {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Patient {
  id: string;
  facility_id: string;
  patient_number: string;
  first_name: string;
  last_name: string;
  date_of_birth: string | null;
  gender: string | null;
  phone: string | null;
  address: string | null;
  national_id: string | null;
  status: string;
  created_at: string;
}

export interface PatientListResponse {
  data: Patient[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Admission {
  id: string;
  facility_id: string;
  patient_id: string;
  admission_type: string;
  status: string;
  admitted_at: string;
  closed_at: string | null;
  department_id: string | null;
}

export interface PatientMeasurement {
  id: string;
  patient_id: string;
  measurement_type: string;
  value: string;
  unit: string | null;
  recorded_at: string;
  recorded_by: string | null;
}

export interface LabOrder {
  id: string;
  patient_id: string;
  test_id: string;
  status: string;
  priority: string;
  ordered_at: string;
}

export interface LabResult {
  id: string;
  order_id: string;
  result_value: string;
  interpretation: string | null;
  status: string;
  entered_at: string;
  validated_at: string | null;
}

export interface ClinicalNote {
  id: string;
  patient_id: string;
  note_type: string;
  content: string;
  created_at: string;
}

export interface NotificationItem {
  id: string;
  category: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  title: string;
  body: string | null;
  read_at: string | null;
  created_at: string;
  resource_type: string | null;
  resource_id: string | null;
}

export interface DashboardKPIs {
  patients_total: number;
  admissions_active: number;
  beds_occupied: number;
  emergencies_in_progress: number;
  pending_lab_results: number;
  pending_imaging: number;
  revenue_today: number;
  outstanding_balance: number;
}

export interface ApiError {
  detail: string | { detail: string } | Array<{ msg: string; loc: string[] }>;
}

/** Mutations en attente de synchronisation (offline queue). */
export interface PendingMutation {
  id: string;
  method: 'POST' | 'PATCH' | 'DELETE';
  path: string;
  body?: any;
  created_at: string;
  retry_count: number;
}
