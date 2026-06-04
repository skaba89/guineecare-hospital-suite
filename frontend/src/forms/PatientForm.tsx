import { SimpleForm } from "../components/SimpleForm";
import { apiRequest } from "../services/api";
import { LookupData } from "../types";
import { buildOptions, firstValue } from "../utils/options";

export function PatientForm({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <SimpleForm
      title="Nouveau patient"
      initialValues={{ facility_id: firstValue(options.facilities), patient_number: `PAT-${Date.now()}`, first_name: "", last_name: "" }}
      fields={[
        { name: "facility_id", label: "Etablissement", options: options.facilities },
        { name: "patient_number", label: "Numero patient" },
        { name: "first_name", label: "Prenom" },
        { name: "last_name", label: "Nom" },
      ]}
      onSubmit={async (values) => {
        await apiRequest("/patients", { method: "POST", body: JSON.stringify(values) });
        onCreated();
      }}
    />
  );
}
