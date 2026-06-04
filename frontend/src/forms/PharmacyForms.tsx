import { SimpleForm } from "../components/SimpleForm";
import { apiRequest } from "../services/api";
import { LookupData } from "../types";
import { buildOptions, firstValue } from "../utils/options";

export function PharmacyForms({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const options = buildOptions(lookups);
  return (
    <>
      <SimpleForm
        title="Nouveau produit pharmacie"
        initialValues={{ facility_id: firstValue(options.facilities), code: `PROD-${Date.now()}`, name: "", category: "MEDICINE", form: "", dosage: "" }}
        fields={[
          { name: "facility_id", label: "Etablissement", options: options.facilities },
          { name: "code", label: "Code" },
          { name: "name", label: "Nom produit" },
          { name: "category", label: "Categorie" },
          { name: "form", label: "Forme" },
          { name: "dosage", label: "Dosage" },
        ]}
        onSubmit={async (values) => {
          await apiRequest("/pharmacy/products", { method: "POST", body: JSON.stringify(values) });
          onCreated();
        }}
      />
      <SimpleForm
        title="Mouvement de stock"
        initialValues={{ facility_id: firstValue(options.facilities), product_id: firstValue(options.products), movement_type: "IN", quantity: "1", reason: "" }}
        fields={[
          { name: "facility_id", label: "Etablissement", options: options.facilities },
          { name: "product_id", label: "Produit", options: options.products },
          { name: "movement_type", label: "Type", options: [
            { value: "IN", label: "Entree" },
            { value: "OUT", label: "Sortie" },
          ] },
          { name: "quantity", label: "Quantite", type: "number" },
          { name: "reason", label: "Motif" },
        ]}
        onSubmit={async (values) => {
          await apiRequest("/pharmacy/stock/movements", {
            method: "POST",
            body: JSON.stringify({ ...values, quantity: Number(values.quantity || 0) }),
          });
          onCreated();
        }}
      />
    </>
  );
}
