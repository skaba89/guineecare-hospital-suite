import { ResourcePage } from "../components/ResourcePage";
import { AdmissionForm } from "../forms/AdmissionForm";
import { LookupData } from "../types";

export function AdmissionsPage({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  return (
    <ResourcePage
      title="Admissions"
      path="/admissions"
      form={<AdmissionForm lookups={lookups} onCreated={onCreated} />}
    />
  );
}
