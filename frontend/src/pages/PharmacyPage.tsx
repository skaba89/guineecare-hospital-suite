import { ResourcePage } from "../components/ResourcePage";
import { PharmacyForms } from "../forms/PharmacyForms";
import { LookupData } from "../types";

export function PharmacyPage({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  return (
    <ResourcePage
      title="Stock pharmacie"
      path="/pharmacy/stock"
      form={<PharmacyForms lookups={lookups} onCreated={onCreated} />}
    />
  );
}
