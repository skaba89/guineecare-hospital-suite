import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { emptyLookups, LookupData } from "../types";

// page_size=1000 to fetch all items in one shot (lookup arrays need to be complete for dropdowns)
const ALL = "?page_size=1000";

export function useLookupData(enabled: boolean, version: number): LookupData {
  const [lookups, setLookups] = useState<LookupData>(emptyLookups);

  useEffect(() => {
    if (!enabled) return;
    let mounted = true;

    async function load() {
      const results = await Promise.allSettled([
        apiRequest<any>("/facilities"),
        apiRequest<any>(`/patients${ALL}`),
        apiRequest<any>("/departments"),
        apiRequest<any>(`/admissions${ALL}`),
        apiRequest<any>(`/pharmacy/products${ALL}`),
        apiRequest<any>(`/laboratory/tests${ALL}`),
        apiRequest<any>(`/laboratory/orders${ALL}`),
        apiRequest<any>(`/billing/invoices${ALL}`),
        apiRequest<any>(`/maternity/records${ALL}`),
        apiRequest<any>(`/personnel/staff${ALL}`),
        apiRequest<any>(`/quality/indicators${ALL}`),
        apiRequest<any>(`/personnel/shifts${ALL}`),
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
        maternityRecords: data[8],
        staff: data[9],
        indicators: data[10],
        shifts: data[11],
      });
    }

    load();
    return () => {
      mounted = false;
    };
  }, [enabled, version]);

  return lookups;
}
