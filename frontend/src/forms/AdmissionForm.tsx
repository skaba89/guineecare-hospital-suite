import { SimpleForm } from "../components/SimpleForm";
import { apiRequest } from "../services/api";
import { LookupData } from "../types";
import { buildOptions, firstValue } from "../utils/options";

export function AdmissionForm({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <SimpleForm
      title="Nouvelle admission"
      initialValues={{ facility_id: firstValue(options.facilities), patient_id: firstValue(options.patients), department_id: firstValue(options.departments), admission_type: "CONSULTATION" }}
      fields={[
        { name: "facility_id", label: "Établissement", options: options.facilities },
        { name: "patient_id", label: "Patient", options: options.patients },
        { name: "department_id", label: "Service", options: options.departments },
        { name: "admission_type", label: "Type admission" },
      ]}
      onSubmit={async (values) => {
        await apiRequest("/admissions", { method: "POST", body: JSON.stringify(values) });
        onCreated();
      }}
    />
  );
}
