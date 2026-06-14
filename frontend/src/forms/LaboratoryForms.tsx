import { SimpleForm } from "../components/SimpleForm";
import { apiRequest } from "../services/api";
import { LookupData } from "../types";
import { buildOptions, firstValue } from "../utils/options";

export function LaboratoryForms({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <>
      <SimpleForm
        title="Nouvel examen laboratoire"
        initialValues={{ facility_id: firstValue(options.facilities), code: `LAB-${Date.now()}`, name: "", category: "GENERAL", sample_type: "Sample" }}
        fields={[
          { name: "facility_id", label: "Établissement", options: options.facilities },
          { name: "code", label: "Code examen" },
          { name: "name", label: "Nom examen" },
          { name: "category", label: "Catégorie" },
          { name: "sample_type", label: "Type échantillon" },
        ]}
        onSubmit={async (values) => {
          await apiRequest("/laboratory/tests", { method: "POST", body: JSON.stringify(values) });
          onCreated();
        }}
      />
      <SimpleForm
        title="Nouvelle demande laboratoire"
        initialValues={{ facility_id: firstValue(options.facilities), patient_id: firstValue(options.patients), admission_id: "", test_id: firstValue(options.labTests), priority: "NORMAL" }}
        fields={[
          { name: "facility_id", label: "Établissement", options: options.facilities },
          { name: "patient_id", label: "Patient", options: options.patients },
          { name: "admission_id", label: "Admission optionnelle", options: options.admissions },
          { name: "test_id", label: "Examen", options: options.labTests },
          { name: "priority", label: "Priorité", options: [
            { value: "NORMAL", label: "Normale" },
            { value: "URGENT", label: "Urgente" },
          ] },
        ]}
        onSubmit={async (values) => {
          const payload = { ...values, admission_id: values.admission_id || null };
          await apiRequest("/laboratory/orders", { method: "POST", body: JSON.stringify(payload) });
          onCreated();
        }}
      />
      <SimpleForm
        title="Résultat laboratoire"
        initialValues={{ facility_id: firstValue(options.facilities), order_id: firstValue(options.labOrders), result_value: "", interpretation: "" }}
        fields={[
          { name: "facility_id", label: "Établissement", options: options.facilities },
          { name: "order_id", label: "Demande", options: options.labOrders },
          { name: "result_value", label: "Résultat" },
          { name: "interpretation", label: "Interprétation" },
        ]}
        onSubmit={async (values) => {
          await apiRequest(`/laboratory/orders/${values.order_id}/results`, {
            method: "POST",
            body: JSON.stringify({ facility_id: values.facility_id, result_value: values.result_value, interpretation: values.interpretation }),
          });
          onCreated();
        }}
      />
    </>
  );
}
