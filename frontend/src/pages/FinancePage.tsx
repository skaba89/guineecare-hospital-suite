import { ResourcePage } from "../components/ResourcePage";
import { BillingForms } from "../forms/BillingForms";
import { LookupData } from "../types";

export function FinancePage({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  return (
    <ResourcePage
      title="Factures"
      path="/billing/invoices"
      form={<BillingForms lookups={lookups} onCreated={onCreated} />}
    />
  );
}
