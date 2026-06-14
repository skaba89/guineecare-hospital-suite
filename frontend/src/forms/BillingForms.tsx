import { SimpleForm } from "../components/SimpleForm";
import { apiRequest } from "../services/api";
import { LookupData } from "../types";
import { buildOptions, firstValue } from "../utils/options";

export function BillingForms({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <>
      <SimpleForm
        title="Nouvelle facture"
        initialValues={{ facility_id: firstValue(options.facilities), patient_id: firstValue(options.patients), admission_id: "", invoice_number: `INV-${Date.now()}`, description: "", net_amount: "0" }}
        fields={[
          { name: "facility_id", label: "Établissement", options: options.facilities },
          { name: "patient_id", label: "Patient", options: options.patients },
          { name: "admission_id", label: "Admission optionnelle", options: options.admissions },
          { name: "invoice_number", label: "Numéro facture" },
          { name: "description", label: "Description" },
          { name: "net_amount", label: "Montant", type: "number" },
        ]}
        onSubmit={async (values) => {
          const payload = { ...values, admission_id: values.admission_id || null, net_amount: Number(values.net_amount || 0) };
          await apiRequest("/billing/invoices", { method: "POST", body: JSON.stringify(payload) });
          onCreated();
        }}
      />
      <SimpleForm
        title="Nouveau paiement"
        initialValues={{ facility_id: firstValue(options.facilities), invoice_id: firstValue(options.invoices), amount: "0", payment_method: "CASH" }}
        fields={[
          { name: "facility_id", label: "Établissement", options: options.facilities },
          { name: "invoice_id", label: "Facture", options: options.invoices },
          { name: "amount", label: "Montant", type: "number" },
          { name: "payment_method", label: "Mode paiement", options: [
            { value: "CASH", label: "Espèces" },
            { value: "MOBILE_MONEY", label: "Mobile Money" },
            { value: "CARD", label: "Carte" },
          ] },
        ]}
        onSubmit={async (values) => {
          await apiRequest(`/billing/invoices/${values.invoice_id}/payments`, {
            method: "POST",
            body: JSON.stringify({ facility_id: values.facility_id, amount: Number(values.amount || 0), payment_method: values.payment_method }),
          });
          onCreated();
        }}
      />
    </>
  );
}
