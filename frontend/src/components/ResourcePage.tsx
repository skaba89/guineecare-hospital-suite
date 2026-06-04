import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { Row } from "../types";
import { ResourceTable } from "./ResourceTable";

export function ResourcePage({ title, path, form }: { title: string; path: string; form?: React.ReactNode }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const payload = await apiRequest<any>(path);
      setRows(Array.isArray(payload.data) ? payload.data : []);
    } catch (err) {
      setError("Impossible de charger les donnees.");
    }
  }

  useEffect(() => {
    load();
    const handler = () => load();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [path]);

  return (
    <section>
      <h1>{title}</h1>
      <p className="muted">Donnees chargees depuis l API backend.</p>
      {form}
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      <ResourceTable rows={rows} />
    </section>
  );
}
