import { ResourcePage } from "../components/ResourcePage";
import { PatientForm } from "../forms/PatientForm";
import { LookupData } from "../types";
import { useT } from "../i18n";

export function PatientsPage({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  const t = useT();
  return (
    <ResourcePage
      title={t("patients.title")}
      path="/patients"
      searchPlaceholder={t("patients.search_placeholder")}
      form={<PatientForm lookups={lookups} onCreated={onCreated} />}
    />
  );
}
