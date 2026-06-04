import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { emptyLookups, LookupData } from "../types";

export function useLookupData(enabled: boolean, version: number): LookupData {
  const [lookups, setLookups] = useState<LookupData>(emptyLookups);

  useEffect(() => {
    if (!enabled) return;
    let mounted = true;

    async function load() {
      const results = await Promise.allSettled([
        apiRequest<any>("/facilities"),
        apiRequest<any>("/patients"),
        apiRequest<any>("/departments"),
        apiRequest<any>("/admissions"),
        apiRequest<any>("/pharmacy/products"),
        apiRequest<any>("/laboratory/tests"),
        apiRequest<any>("/laboratory/orders"),
        apiRequest<any>("/billing/invoices"),
      ]);

      if (!mounted) return;
      const data = results.map((result) =>
        result.status === "fulfilled" && Array.isArray(result.value.data) ? result.value.data : []
      );

      setLookups({
        facilities: data[0],
        patients: data[1],
        departments: data[2],
        admissions: data[3],
        products: data[4],
        labTests: data[5],
        labOrders: data[6],
        invoices: data[7],
      });
    }

    load();
    return () => {
      mounted = false;
    };
  }, [enabled, version]);

  return lookups;
}
