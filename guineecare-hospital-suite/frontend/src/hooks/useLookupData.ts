import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { emptyLookups, LookupData } from "../types";

// v2.8.5 — Réduction du payload au login.
// Avant : 12 requêtes dont 5 avec page_size=1000 → lent sur Render free
// Maintenant : seules les petites tables de référence sont chargées.
// Les tables volumineuses (patients, admissions, invoices, etc.) sont
// vides au démarrage — les pages utilisent usePaginatedList pour leur
// propre fetch paginé.

/**
 * Reference data — petites tables stables chargées UNE FOIS au démarrage.
 *
 * v2.8.5 — Tables volumineuses (patients, admissions, invoices, labOrders,
 * maternityRecords) NE SONT PLUS chargées ici. Elles étaient chargées avec
 * page_size=1000 ce qui rendait le login très lent (12 requêtes dont 5
 * lourdes). Les pages qui en ont besoin utilisent usePaginatedList.
 *
 * Les dropdowns patients utilisent /patients/lookup/light (endpoint léger).
 */
export function useReferenceData(enabled: boolean, version: number): LookupData {
  const [lookups, setLookups] = useState<LookupData>(emptyLookups);

  useEffect(() => {
    if (!enabled) return;
    let mounted = true;

    async function load() {
      // v2.8.5 — Seulement 7 petites tables de référence + patients lookup léger
      const results = await Promise.allSettled([
        apiRequest<any>("/facilities"),
        apiRequest<any>("/departments"),
        apiRequest<any>("/personnel/staff?page_size=200"),
        apiRequest<any>("/quality/indicators?page_size=200"),
        apiRequest<any>("/personnel/shifts?page_size=200"),
        apiRequest<any>("/laboratory/tests?page_size=200"),
        apiRequest<any>("/pharmacy/products?page_size=200"),
        // v2.8.5 — patients lookup léger (pas de PHI, max 500)
        apiRequest<any>("/patients/lookup/light"),
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
        patients: data[7], // lookup léger (id, label, patient_number seulement)
        // Tables volumineuses — vides au démarrage (usePaginatedList s'occupe du fetch)
        admissions: [],
        invoices: [],
        labOrders: [],
        maternityRecords: [],
      });
    }

    load();
    return () => {
      mounted = false;
    };
  }, [enabled, version]);

  return lookups;
}

export function useLookupData(enabled: boolean, version: number): LookupData {
  return useReferenceData(enabled, version);
}
