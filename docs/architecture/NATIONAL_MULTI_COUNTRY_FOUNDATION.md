# GuinéeCare — Fondation nationale Guinée et multi-pays

## Vision

GuinéeCare doit rester **Guinea-first** tout en devenant un produit déployable dans d'autres pays sans dupliquer le code clinique.

La séparation cible est la suivante :

1. **Core clinique commun** — patient, consultation, urgence, hospitalisation, maternité, laboratoire, pharmacie, imagerie, bloc, facturation, qualité.
2. **Profil pays** — devise, indicatif téléphonique, fuseau horaire, langues disponibles, hiérarchie administrative et sanitaire, conventions nationales.
3. **Adaptateurs nationaux** — DHIS2, systèmes logistiques, RH, assurance, identité, état civil et autres SI externes.
4. **Configuration établissement** — type de structure, rattachement territorial, district sanitaire, identifiants externes, géolocalisation.

## Profil Guinée par défaut

`COUNTRY_CODE=GN` active le profil Guinée.

Le profil contient notamment :

- devise : `GNF` ;
- indicatif : `+224` ;
- fuseau : `Africa/Conakry` ;
- langue par défaut : français ;
- niveaux administratifs : Région > Préfecture / Zone spéciale > Commune > Quartier / District ;
- niveaux sanitaires : National > Région sanitaire > District sanitaire > Formation sanitaire > Communauté ;
- intégrations nationales à isoler derrière des adaptateurs : DHIS2 SISR, DHIS2 Surveillance, DHIS2 PEV, e-SIGL et iHRIS.

## Évolution du registre des établissements

Les colonnes historiques `region`, `prefecture` et `commune` restent disponibles pour éviter les régressions.

Les champs génériques suivants sont ajoutés :

- `country_code` ;
- `admin_level_1` à `admin_level_4` ;
- `health_district` ;
- `facility_type_code` ;
- `dhis2_org_unit_id` ;
- `latitude`, `longitude`.

Pour `GN`, l'API synchronise automatiquement :

- `region` <-> `admin_level_1` ;
- `prefecture` <-> `admin_level_2` ;
- `commune` <-> `admin_level_3`.

Un autre pays peut utiliser uniquement `admin_level_1..4` et définir son propre profil sans faire entrer ses termes administratifs dans le core.

## Architecture nationale cible

```text
Utilisateurs / Patients / Professionnels
              |
       GuinéeCare Apps
 Web + Mobile + Offline-first
              |
        API Gateway / IAM
              |
       Core clinique SIH
              |
     Interoperability Layer
       FHIR / REST / Events
       /       |        \
   DHIS2     e-SIGL     iHRIS
 SISR/PEV/   Logistique   RH
 Surveillance
              |
   Data Platform Nationale
  indicateurs / qualité / alertes
```

GuinéeCare ne doit pas répliquer les responsabilités des plateformes nationales existantes. Le SIH reste la source opérationnelle clinique de l'établissement ; les agrégats et événements réglementaires sont transmis aux systèmes nationaux via des adaptateurs versionnés.

## Prochaines étapes prioritaires

### P0 — Sécurité et identité

- Remplacer le pseudo-RLS applicatif par de vraies policies PostgreSQL RLS sur les tables de santé.
- Introduire une identité patient nationale / MPI séparée du `patient_number` local établissement.
- Ajouter fusion de doublons, aliases d'identité, règles de rapprochement et journal de fusion.
- Chiffrement des données sensibles et gestion centralisée des secrets/clefs.
- Généraliser MFA pour les rôles à privilèges, avec procédure de récupération sécurisée.

### P0 — Interopérabilité nationale

- Master Facility Registry avec correspondance DHIS2 OrgUnit.
- Adaptateur DHIS2 versionné, idempotent, avec file d'attente, retry et dead-letter queue.
- FHIR R4 : Patient, Organization, Practitioner, Encounter, Observation, DiagnosticReport, MedicationRequest, Immunization, ServiceRequest.
- Terminologies : ICD-11 complet via service de terminologie ; LOINC pour laboratoire ; catalogues médicaments et actes externalisés.
- Contrats d'API et tests de conformité des échanges.

### P1 — Parcours spécifiques Guinée

- référence / contre-référence entre poste de santé, centre de santé, hôpital préfectoral/régional et CHU ;
- ambulance et régulation des urgences ;
- vaccination PEV et carnet vaccinal ;
- surveillance épidémiologique et alertes ;
- banque de sang / transfusion ;
- santé communautaire et agents communautaires ;
- programmes paludisme, TB, VIH, santé maternelle et néonatale ;
- gestion des indigents, tiers payeur, mutuelles et couverture sanitaire ;
- paiements locaux configurables et rapprochement de caisse.

### P1 — Offline-first national

- base locale chiffrée sur mobile/tablette ;
- journal de mutations avec identifiants idempotents ;
- synchronisation différentielle ;
- gestion explicite des conflits ;
- pièces jointes mises en file d'attente ;
- indicateur de fraîcheur et état de synchronisation visible par l'utilisateur.

### P1 — Gouvernance nationale

- rôles National / Région sanitaire / District sanitaire / Établissement ;
- délégation temporaire et séparation des responsabilités ;
- audit immuable des accès aux données de santé ;
- centre de pilotage national sans exposition de données nominatives ;
- qualité et complétude des données par établissement ;
- catalogue d'indicateurs versionné.

## Règle d'adaptation à un autre pays

Pour ajouter un pays :

1. enregistrer un `CountryProfile` ;
2. configurer les libellés des niveaux administratifs et sanitaires ;
3. ajouter les terminologies et référentiels nationaux ;
4. implémenter les adaptateurs externes du pays ;
5. configurer devise, paiements, assurance, formats d'identifiants et règles légales ;
6. exécuter la suite de conformité multi-pays.

Le core clinique ne doit pas être forké par pays.
