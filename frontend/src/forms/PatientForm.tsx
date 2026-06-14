import { SimpleForm } from "../components/SimpleForm";
import { apiRequest } from "../services/api";
import { LookupData } from "../types";
import { buildOptions, firstValue } from "../utils/options";

export function PatientForm({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <SimpleForm
      title="Nouveau patient"
      initialValues={{
        facility_id: firstValue(options.facilities),
        patient_number: `PAT-${Date.now()}`,
        first_name: "",
        last_name: "",
        date_of_birth: "",
        gender: "",
        phone: "",
        address: "",
        national_id: "",
        insurance_number: "",
        emergency_contact_name: "",
        emergency_contact_phone: "",
      }}
      fields={[
        { name: "facility_id", label: "Établissement", options: options.facilities },
        { name: "patient_number", label: "Numéro patient" },
        { name: "first_name", label: "Prénom" },
        { name: "last_name", label: "Nom" },
        { name: "date_of_birth", label: "Date de naissance", type: "date" },
        {
          name: "gender",
          label: "Sexe",
          options: [
            { value: "M", label: "Masculin" },
            { value: "F", label: "Féminin" },
            { value: "O", label: "Autre" },
          ],
        },
        { name: "phone", label: "Téléphone" },
        { name: "address", label: "Adresse" },
        { name: "national_id", label: "Numéro national" },
        { name: "insurance_number", label: "Numéro assurance" },
        { name: "emergency_contact_name", label: "Contact urgence - Nom" },
        { name: "emergency_contact_phone", label: "Contact urgence - Tel" },
      ]}
      onSubmit={async (values) => {
        await apiRequest("/patients", { method: "POST", body: JSON.stringify(values) });
        onCreated();
      }}
    />
  );
}
