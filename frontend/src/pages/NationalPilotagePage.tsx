import { LookupData } from "../types";

export function NationalPilotagePage({ lookups }: { lookups: LookupData }) {
  const indicators = [
    { label: "Établissements suivis", value: lookups.facilities.length, description: "Base multi-établissements pour un déploiement progressif." },
    { label: "Patients enregistrés", value: lookups.patients.length, description: "Centralisation du dossier patient hospitalier." },
    { label: "Admissions", value: lookups.admissions.length, description: "Suivi des entrées, orientations et sorties." },
    { label: "Produits pharmacie", value: lookups.products.length, description: "Pilotage des stocks et réduction des ruptures." },
    { label: "Examens laboratoire", value: lookups.labTests.length, description: "Traçabilité des demandes et résultats." },
    { label: "Factures", value: lookups.invoices.length, description: "Suivi des recettes et transparence financière." },
  ];

  return (
    <section>
      {/* Hero Panel */}
      <div
        className="card"
        style={{
          background: "linear-gradient(135deg, #0b2e58 0%, #1a4a7a 100%)",
          color: "white",
          padding: "32px",
          marginBottom: "24px",
        }}
      >
        <p
          style={{
            textTransform: "uppercase",
            fontSize: "12px",
            letterSpacing: "2px",
            color: "#f2c94c",
            fontWeight: 700,
            marginBottom: "8px",
          }}
        >
          Pilotage national
        </p>
        <h1 style={{ margin: "0 0 12px", fontSize: "28px", color: "white" }}>
          Vue ministérielle de la plateforme GuinéeCare
        </h1>
        <p style={{ color: "rgba(255,255,255,0.8)", margin: 0, lineHeight: 1.6 }}>
          Cette page présente la plateforme comme un socle de gouvernance sanitaire : suivi des établissements,
          activité hospitalière, traçabilité, pharmacie, laboratoire, facturation et audit.
        </p>
      </div>

      {/* KPI Grid */}
      <div className="grid">
        {indicators.map((item) => (
          <div className="card" key={item.label}>
            <div className="kpi">{item.value}</div>
            <strong>{item.label}</strong>
            <p className="muted">{item.description}</p>
          </div>
        ))}
      </div>

      {/* Split Grid: Impacts + Modules */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "16px",
          marginTop: "18px",
        }}
      >
        <div className="card">
          <h2>Impacts attendus pour l'État</h2>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            <li style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              ✓ Meilleure visibilité sur l'activité hospitalière.
            </li>
            <li style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              ✓ Suivi plus fiable des patients, admissions et recettes.
            </li>
            <li style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              ✓ Traçabilité des actions sensibles et des opérations critiques.
            </li>
            <li style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              ✓ Base de reporting régional puis national.
            </li>
            <li style={{ padding: "8px 0" }}>
              ✓ Préparation à l'interopérabilité avec les systèmes publics.
            </li>
          </ul>
        </div>

        <div className="card">
          <h2>Modules à démontrer</h2>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            <li style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              ■ Dashboard opérationnel.
            </li>
            <li style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              ■ Gestion patients et admissions.
            </li>
            <li style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              ■ Urgences et orientation.
            </li>
            <li style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              ■ Pharmacie et mouvements de stock.
            </li>
            <li style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              ■ Laboratoire et résultats.
            </li>
            <li style={{ padding: "8px 0" }}>
              ■ Facturation, paiement et audit.
            </li>
          </ul>
        </div>
      </div>

      {/* Timeline */}
      <div className="card" style={{ marginTop: "18px" }}>
        <h2>Déploiement national progressif</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "20px",
            marginTop: "12px",
          }}
        >
          {[
            { step: "1", title: "Démonstration", desc: "Validation institutionnelle et choix du périmètre pilote." },
            { step: "2", title: "Pilote hospitalier", desc: "Déploiement dans un établissement de référence pendant 3 à 6 mois." },
            { step: "3", title: "Extension régionale", desc: "Déploiement multi-établissements et consolidation des indicateurs." },
            { step: "4", title: "Plateforme nationale", desc: "Reporting national, interopérabilité et gouvernance centralisée." },
          ].map((item) => (
            <div key={item.step} style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "50%",
                  background: "var(--primary)",
                  color: "white",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: 800,
                  fontSize: "16px",
                  flexShrink: 0,
                }}
              >
                {item.step}
              </div>
              <div>
                <strong>{item.title}</strong>
                <p className="muted" style={{ margin: "4px 0 0", fontSize: "14px" }}>
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
