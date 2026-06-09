import { LookupData } from "../types";

export function NationalPilotagePage({ lookups }: { lookups: LookupData }) {
  const indicators = [
    { label: "Etablissements suivis", value: lookups.facilities.length, description: "Base multi-etablissements pour un deploiement progressif." },
    { label: "Patients enregistres", value: lookups.patients.length, description: "Centralisation du dossier patient hospitalier." },
    { label: "Admissions", value: lookups.admissions.length, description: "Suivi des entrees, orientations et sorties." },
    { label: "Produits pharmacie", value: lookups.products.length, description: "Pilotage des stocks et reduction des ruptures." },
    { label: "Examens laboratoire", value: lookups.labTests.length, description: "Traçabilite des demandes et resultats." },
    { label: "Factures", value: lookups.invoices.length, description: "Suivi des recettes et transparence financiere." },
  ];

  return (
    <section>
      <div className="hero-panel">
        <p className="eyebrow">Pilotage national</p>
        <h1>Vue ministerielle de la plateforme GuinéeCare</h1>
        <p>
          Cette page présente la plateforme comme un socle de gouvernance sanitaire : suivi des etablissements,
          activite hospitaliere, traçabilite, pharmacie, laboratoire, facturation et audit.
        </p>
      </div>

      <div className="grid">
        {indicators.map((item) => (
          <div className="card" key={item.label}>
            <div className="kpi">{item.value}</div>
            <strong>{item.label}</strong>
            <p className="muted">{item.description}</p>
          </div>
        ))}
      </div>

      <div className="split-grid">
        <div className="card">
          <h2>Impacts attendus pour l'Etat</h2>
          <ul className="clean-list">
            <li>Meilleure visibilité sur l'activité hospitalière.</li>
            <li>Suivi plus fiable des patients, admissions et recettes.</li>
            <li>Traçabilité des actions sensibles et des opérations critiques.</li>
            <li>Base de reporting régional puis national.</li>
            <li>Préparation à l'interopérabilité avec les systèmes publics.</li>
          </ul>
        </div>

        <div className="card">
          <h2>Modules à démontrer</h2>
          <ul className="clean-list">
            <li>Dashboard opérationnel.</li>
            <li>Gestion patients et admissions.</li>
            <li>Urgences et orientation.</li>
            <li>Pharmacie et mouvements de stock.</li>
            <li>Laboratoire et résultats.</li>
            <li>Facturation, paiement et audit.</li>
          </ul>
        </div>
      </div>

      <div className="card">
        <h2>Déploiement national progressif</h2>
        <div className="timeline-grid">
          <div>
            <strong>1. Démonstration</strong>
            <p className="muted">Validation institutionnelle et choix du périmètre pilote.</p>
          </div>
          <div>
            <strong>2. Pilote hospitalier</strong>
            <p className="muted">Déploiement dans un établissement de référence pendant 3 à 6 mois.</p>
          </div>
          <div>
            <strong>3. Extension régionale</strong>
            <p className="muted">Déploiement multi-établissements et consolidation des indicateurs.</p>
          </div>
          <div>
            <strong>4. Plateforme nationale</strong>
            <p className="muted">Reporting national, interopérabilité et gouvernance centralisée.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
