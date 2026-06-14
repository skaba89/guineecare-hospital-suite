import { SimpleForm } from "../components/SimpleForm";
import { apiRequest } from "../services/api";
import { LookupData } from "../types";
import { buildOptions, firstValue } from "../utils/options";

export function EmergencyForm({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <SimpleForm
      title="Nouveau passage urgence"
      initialValues={{ facility_id: firstValue(options.facilities), patient_id: firstValue(options.patients), admission_id: "", priority_level: "NORMAL", chief_complaint: "" }}
      fields={[
        { name: "facility_id", label: "Établissement", options: options.facilities },
        { name: "patient_id", label: "Patient", options: options.patients },
        { name: "admission_id", label: "Admission optionnelle", options: options.admissions },
        { name: "priority_level", label: "Priorité", options: [
          { value: "LOW", label: "Basse" },
          { value: "NORMAL", label: "Normale" },
          { value: "HIGH", label: "Haute" },
          { value: "CRITICAL", label: "Critique" },
        ] },
        { name: "chief_complaint", label: "Motif" },
      ]}
      onSubmit={async (values) => {
        const payload = { ...values, admission_id: values.admission_id || null };
        await apiRequest("/emergency/visits", { method: "POST", body: JSON.stringify(payload) });
        onCreated();
      }}
    />
  );
}
