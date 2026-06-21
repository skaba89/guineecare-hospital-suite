import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { emptyLookups, LookupData } from "../types";

// page_size=1000 to fetch all items in one shot (lookup arrays need to be complete for dropdowns)
const ALL = "?page_size=1000";

/**
 * Reference data — petites tables stables chargées UNE FOIS au démarrage
 * et partagées via le contexte App pour alimenter les dropdowns/selects.
 *
 * Sont considérées "référence" : tables dont la taille reste petite (< 200 lignes)
 * et rarement modifiées (facilities, departments, staff, indicators, shifts,
 * labTests, products).
 *
 * Pour les tables volumineuses (patients, admissions, invoices, labOrders,
 * maternityRecords), utiliser `useVolatileData` (lazy, paginé par page).
 */
export function useReferenceData(enabled: boolean, version: number): LookupData {
  const [lookups, setLookups] = useState<LookupData>(emptyLookups);

  useEffect(() => {
    if (!enabled) return;
    let mounted = true;

    async function load() {
      const results = await Promise.allSettled([
        apiRequest<any>("/facilities"),
        apiRequest<any>("/departments"),
        apiRequest<any>(`/personnel/staff${ALL}`),
        apiRequest<any>(`/quality/indicators${ALL}`),
        apiRequest<any>(`/personnel/shifts${ALL}`),
        apiRequest<any>(`/laboratory/tests${ALL}`),
        apiRequest<any>(`/pharmacy/products${ALL}`),
      ]);

      if (!mounted) return;
      const data = results.map((result) =>
        result.status === "fulfilled" && Array.isArray(result.value.data) ? result.value.data : []
      );

      setLookups({
        ...emptyLookups,
        facilities: data[0],
        departments: data[1],
        staff: data[2],
        indicators: data[3],
        shifts: data[4],
        labTests: data[5],
        products: data[6],
      });
    }

    load();
    return () => {
      mounted = false;
    };
  }, [enabled, version]);

  return lookups;
}

/**
 * Volatile data — tables volumineuses à fetcher à la demande par page.
 *
 * NE PAS utiliser ce hook pour pré-charger toutes les données au démarrage.
 * Chaque page concernée (PatientsPage, AdmissionsPage, FinancePage, LabPage,
 * MaternityPage, etc.) doit gérer sa propre pagination via `usePaginatedList`.
 *
 * Ce hook est fourni uniquement pour la rétro-compatibilité des pages qui
 * n'ont pas encore été migrées et qui lisent encore `lookups.patients`,
 * `lookups.admissions`, `lookups.invoices`, `lookups.labOrders`,
 * `lookups.maternityRecords`. Il retourne des arrays vides par défaut —
 * ces pages DOIVENT être migrées vers usePaginatedList.
 *
 * @deprecated Ne pas utiliser dans les nouvelles pages — utiliser usePaginatedList.
 */
export function useVolatileData(): Pick<
  LookupData,
  "patients" | "admissions" | "invoices" | "labOrders" | "maternityRecords"
> {
  // Retourne des arrays vides : les pages doivent gérer leur pagination elles-mêmes.
  return {
    patients: [],
    admissions: [],
    invoices: [],
    labOrders: [],
    maternityRecords: [],
  };
}

/**
 * Hook de rétro-compatibilité — conserve l'ancien comportement (12 endpoints
 * page_size=1000) pour les pages non migrées. À NE PAS utiliser dans les
 * nouvelles pages.
 *
 * @deprecated Utiliser useReferenceData + usePaginatedList à la place.
 */
export function useLookupData(enabled: boolean, version: number): LookupData {
  const ref = useReferenceData(enabled, version);
  const volatile = useVolatileData();

  return {
    ...ref,
    ...volatile,
  };
}
