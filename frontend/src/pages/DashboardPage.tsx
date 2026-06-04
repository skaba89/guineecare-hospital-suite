import { LookupData } from "../types";

export function DashboardPage({ lookups }: { lookups: LookupData }) {
  return (
    <section>
      <h1>Dashboard hopital</h1>
      <p className="muted">Vue MVP des principaux modules hospitaliers.</p>
      <div className="grid">
        <Kpi title="Etablissements" value={String(lookups.facilities.length)} />
        <Kpi title="Patients" value={String(lookups.patients.length)} />
        <Kpi title="Admissions" value={String(lookups.admissions.length)} />
        <Kpi title="Produits" value={String(lookups.products.length)} />
        <Kpi title="Examens" value={String(lookups.labTests.length)} />
        <Kpi title="Factures" value={String(lookups.invoices.length)} />
      </div>
    </section>
  );
}

function Kpi({ title, value }: { title: string; value: string }) {
  return (
    <div className="card">
      <div className="kpi">{value}</div>
      <div className="muted">{title}</div>
    </div>
  );
}
