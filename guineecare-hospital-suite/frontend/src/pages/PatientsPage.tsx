import { useState, useEffect } from "react";
import { ResourcePage } from "../components/ResourcePage";
import { PatientForm } from "../forms/PatientForm";
import { InfinitePatientsList } from "./InfinitePatientsList";
import { LookupData } from "../types";
import { useT } from "../i18n";

/**
 * Patients Page — v2.9.2
 *
 * Deux vues disponibles :
 *   1. Vue paginée (ResourcePage) — défaut, navigation par page
 *   2. Vue scroll infini (InfinitePatientsList) — v2.9.2, UX plus fluide
 *
 * La préférence est persistée dans localStorage (clé "guineecare_patients_view").
 */

const VIEW_STORAGE_KEY = "guineecare_patients_view";
type ViewMode = "paginated" | "infinite";

function getInitialView(): ViewMode {
  if (typeof window === "undefined") return "paginated";
  const stored = localStorage.getItem(VIEW_STORAGE_KEY);
  return stored === "infinite" ? "infinite" : "paginated";
}

export function PatientsPage({
  lookups,
  onCreated,
}: {
  lookups: LookupData;
  onCreated: () => void;
}) {
  const t = useT();
  const [view, setView] = useState<ViewMode>(getInitialView);
  const [search, setSearch] = useState("");

  // Persiste la préférence de vue
  useEffect(() => {
    localStorage.setItem(VIEW_STORAGE_KEY, view);
  }, [view]);

  if (view === "infinite") {
    return (
      <InfinitePatientsList
        lookups={lookups}
        search={search}
        onSearchChange={setSearch}
        onViewToggle={() => setView("paginated")}
      />
    );
  }

  return (
    <ResourcePage
      title={t("patients.title")}
      path="/patients"
      searchPlaceholder={t("patients.search_placeholder")}
      form={<PatientForm lookups={lookups} onCreated={onCreated} />}
    />
  );
}
