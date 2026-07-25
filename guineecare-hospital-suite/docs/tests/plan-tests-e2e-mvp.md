# Plan de tests E2E MVP

## Objectif

Valider les parcours critiques de GuinéeCare Hospital Suite avant mise en production pilote.

## Tests socle

- Connexion utilisateur valide.
- Connexion refusée avec mauvais mot de passe.
- Accès refusé sans permission.
- Création établissement.
- Création service.
- Création utilisateur.
- Audit d'une action sensible.

## Tests patient et admission

- Création patient.
- Recherche patient.
- Détection doublon simple.
- Création admission consultation.
- Création admission urgence.
- Clôture admission.

## Tests DPI

- Consultation synthèse patient.
- Création note clinique.
- Ajout mesure patient.
- Ajout diagnostic.
- Vérification timeline.

## Tests urgences

- Création passage urgence.
- Triage.
- Changement priorité.
- Orientation sortie.
- Orientation hospitalisation.

## Tests hospitalisation

- Création chambre.
- Création lit.
- Affectation lit.
- Transfert lit.
- Sortie séjour.

## Tests pharmacie

- Création produit.
- Entrée stock.
- Sortie stock.
- Contrôle stock insuffisant.
- Alerte seuil minimum.

## Tests laboratoire

- Création examen.
- Création demande.
- Saisie résultat.
- Validation résultat.
- Consultation résultat dans le dossier patient.

## Tests facturation

- Création tarif.
- Création facture.
- Ajout ligne.
- Paiement.
- Reçu.
- Clôture caisse.

## Tests reporting

- Dashboard hôpital.
- Rapport mensuel.
- Export.
- Contrôle cohérence données.

## Critères de sortie recette

- Aucun bug critique ouvert.
- Parcours patient complet validé.
- Parcours urgence validé.
- Parcours facture et paiement validé.
- Tests permissions validés.
- Formation pilote réalisée.
