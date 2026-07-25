# Lot 06 — Hospitalisation, lits et soins

## Objectif

Gérer le séjour hospitalier complet : demande d'admission, affectation de lit, mouvements, surveillance, soins et sortie.

## Modules inclus

- Demandes d'hospitalisation.
- Séjours.
- Chambres et lits.
- Tableau des lits.
- Mouvements patient.
- Transmissions.
- Plan de soins.
- Visites médicales.
- Préparation de sortie.

## Acteurs

- Médecin.
- Infirmier.
- Cadre de service.
- Agent admission.
- Brancardier.
- Direction médicale.

## Règles métier

- Un lit ne peut pas être affecté à deux patients en même temps.
- Tout mouvement doit être historisé.
- Une sortie doit avoir une décision médicale.
- Le lit passe en nettoyage avant de redevenir disponible.

## Critères d'acceptation

- Ouvrir un séjour.
- Affecter un lit.
- Voir le tableau des lits.
- Créer une transmission.
- Suivre un plan de soins.
- Clôturer un séjour.
