import { LookupData, Option, Row } from "../types";

export function toOptions(rows: Row[], labelBuilder: (row: Row) => string): Option[] {
  return rows.filter((row) => row.id).map((row) => ({ value: row.id, label: labelBuilder(row) }));
}

export function firstValue(options: Option[]): string {
  return options[0]?.value || "";
}

export function buildOptions(lookups: LookupData) {
  return {
    facilities: toOptions(lookups.facilities, (row) => `${row.code || "ETAB"} - ${row.name || row.id}`),
    patients: toOptions(lookups.patients, (row) => `${row.patient_number || "PAT"} - ${row.first_name || ""} ${row.last_name || ""}`.trim()),
    departments: toOptions(lookups.departments, (row) => `${row.code || "SRV"} - ${row.name || row.id}`),
    admissions: toOptions(lookups.admissions, (row) => `${row.admission_type || "ADM"} - ${row.status || ""} - ${row.patient_id || row.id}`),
    products: toOptions(lookups.products, (row) => `${row.code || "PROD"} - ${row.name || row.id}`),
    labTests: toOptions(lookups.labTests, (row) => `${row.code || "LAB"} - ${row.name || row.id}`),
    labOrders: toOptions(lookups.labOrders, (row) => `${row.priority || "ORDER"} - ${row.status || ""} - ${row.patient_id || row.id}`),
    invoices: toOptions(lookups.invoices, (row) => `${row.invoice_number || "INV"} - solde ${row.balance_due ?? ""}`),
  };
}
