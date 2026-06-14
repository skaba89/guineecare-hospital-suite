# Lot 10 — Facturation, caisse et paiements

## Objectif

Gérer la tarification, les factures, les paiements, les reçus, les prises en charge, les exonérations et le suivi des soldes patients.

## Modules inclus

- Référentiel tarifs.
- Factures patient.
- Lignes de facture.
- Paiements.
- Reçus.
- Caisse.
- Clôture caisse.
- Prises en charge.
- Exonérations.
- Suivi des soldes.

## Acteurs

- Caissier.
- Agent facturation.
- Comptable.
- Direction administrative.
- Agent admission.

## Règles métier

- Un paiement validé ne doit pas être supprimé physiquement.
- Une annulation doit être justifiée.
- Une exonération doit être validée par un profil autorisé.
- La caisse doit pouvoir être clôturée et contrôlée.

## Critères d'acceptation

- Créer une facture.
- Ajouter des lignes.
- Encaisser un paiement.
- Générer un reçu.
- Clôturer une caisse.
- Consulter les soldes ouverts.
