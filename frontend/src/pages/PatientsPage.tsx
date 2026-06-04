import { ResourcePage } from "../components/ResourcePage";
import { PatientForm } from "../forms/PatientForm";
import { LookupData } from "../types";

export function PatientsPage({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  return (
    <ResourcePage
      title="Patients"
      path="/patients"
      form={<PatientForm lookups={lookups} onCreated={onCreated} />}
    />
  );
}
