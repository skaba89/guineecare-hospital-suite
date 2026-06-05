import { ResourcePage } from "../components/ResourcePage";
import { LaboratoryForms } from "../forms/LaboratoryForms";
import { LookupData } from "../types";

export function LabPage({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  return (
    <ResourcePage
      title="Examens"
      path="/laboratory/tests"
      form={<LaboratoryForms lookups={lookups} onCreated={onCreated} />}
    />
  );
}
